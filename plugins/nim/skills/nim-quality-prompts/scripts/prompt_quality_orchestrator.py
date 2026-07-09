#!/usr/bin/env python3
"""Index prompt-quality sources and build structured prompt improvements.

The script is dependency-free by design. It builds a SQLite index from a
registry of prompt databases and Codex skills, then retrieves matching records
to assemble a deterministic improvement plan.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sqlite3
import sys
import textwrap
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

SCRIPT_PATH = Path(__file__).resolve()
SKILL_ROOT = SCRIPT_PATH.parents[1]
WORKSPACE_ROOT = SKILL_ROOT.parent
DEFAULT_REGISTRY = SKILL_ROOT / "references" / "prompt_database_registry.json"

NO_IMPROVE_MARKERS = (
    "do not improve",
    "dont improve",
    "don't improve",
    "no improvement",
    "keep unchanged",
    "passthrough",
    "as is",
    "leave as is",
    "keep as is",
    "do not rewrite",
)

STOP_WORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "that",
    "this",
    "into",
    "onto",
    "your",
    "about",
    "prompt",
    "make",
    "video",
    "image",
    "photo",
    "shot",
    "scene",
    "style",
    "quality",
    "high",
    "very",
}


@dataclass(frozen=True)
class SourceSpec:
    id: str
    title: str
    kind: str
    adapter: str
    path: Path
    enabled: bool
    weight: float
    tags: tuple[str, ...]


@dataclass(frozen=True)
class Record:
    source_id: str
    record_type: str
    title: str
    text: str
    keywords: tuple[str, ...]
    tags: tuple[str, ...]
    weight: float
    metadata: dict[str, Any]


def read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1251", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="replace")


def read_json(path: Path) -> Any:
    return json.loads(read_text(path))


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def compact_text(value: Any, limit: int = 2400) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        text = value
    else:
        text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def flatten_values(value: Any, limit: int = 1200) -> str:
    parts: list[str] = []

    def walk(item: Any) -> None:
        if item is None:
            return
        if isinstance(item, dict):
            for child in item.values():
                walk(child)
        elif isinstance(item, (list, tuple)):
            for child in item:
                walk(child)
        else:
            text = str(item).strip()
            if text:
                parts.append(text)

    walk(value)
    unique = list(dict.fromkeys(parts))
    return compact_text(", ".join(unique), limit)


def normalize_path(raw: str, registry_path: Path) -> Path:
    expanded = raw.replace("${WORKSPACE_ROOT}", str(WORKSPACE_ROOT))
    expanded = expanded.replace("${SKILL_ROOT}", str(SKILL_ROOT))
    expanded = os.path.expandvars(expanded)
    path = Path(expanded)
    if not path.is_absolute():
        path = (registry_path.parent / path).resolve()
    return path


def tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[\w]+", text.lower(), flags=re.UNICODE)
    return [token for token in tokens if len(token) > 2 and token not in STOP_WORDS]


def infer_record_type(text: str, tags: Iterable[str]) -> str:
    haystack = " ".join([text, " ".join(tags)]).lower()
    tag_set = {str(tag).lower() for tag in tags}
    if {"structure", "meta-prompt"} & tag_set:
        return "structure"
    if {"rulebook", "continuity"} & tag_set:
        return "composition"
    checks = (
        ("negative", ("negative", "avoid", "forbidden")),
        ("lut", ("lut", "color grade", "palette", "halation", "grain")),
        ("camera", ("camera", "lens", "arri", "sony", "hasselblad", "phase one")),
        ("lighting", ("lighting", "key light", "rim light", "rembrandt", "fill")),
        ("composition", ("composition", "angle", "shot scale", "transition", "axis")),
        ("recipe", ("recipe", "stack", "best for")),
        ("artist_style", ("artist", "painting", "illustration", "style")),
    )
    for label, needles in checks:
        if any(needle in haystack for needle in needles):
            return label
    return "reference"


def infer_markdown_record_type(title: str, body: str, tags: Iterable[str]) -> str:
    title_lower = title.lower()
    if any(needle in title_lower for needle in ("negative", "avoid", "forbidden")):
        return "negative"
    record_type = infer_record_type(" ".join([title, body]), tags)
    if record_type == "negative":
        return "reference"
    return record_type


def load_registry(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Registry not found: {path}")
    return read_json(path)


def source_from_mapping(raw: dict[str, Any], registry_path: Path) -> SourceSpec:
    return SourceSpec(
        id=str(raw["id"]),
        title=str(raw.get("title") or raw["id"]),
        kind=str(raw.get("kind") or "unknown"),
        adapter=str(raw.get("adapter") or raw.get("kind") or "unknown"),
        path=normalize_path(str(raw["path"]), registry_path),
        enabled=bool(raw.get("enabled", True)),
        weight=float(raw.get("weight", 1.0)),
        tags=tuple(str(tag) for tag in raw.get("tags", [])),
    )


def discover_skill_sources(registry: dict[str, Any], registry_path: Path) -> list[SourceSpec]:
    discovered: list[SourceSpec] = []
    seen_paths: set[Path] = set()
    for root_spec in registry.get("skill_roots", []):
        if not root_spec.get("enabled", True):
            continue
        root = normalize_path(str(root_spec["path"]), registry_path)
        max_depth = int(root_spec.get("max_depth", 2))
        tags = tuple(str(tag) for tag in root_spec.get("tags", []))
        if not root.exists() or not root.is_dir():
            continue
        root_depth = len(root.parts)
        for skill_md in root.rglob("SKILL.md"):
            depth = len(skill_md.parent.parts) - root_depth
            if depth > max_depth:
                continue
            skill_dir = skill_md.parent.resolve()
            if skill_dir in seen_paths:
                continue
            seen_paths.add(skill_dir)
            skill_id = f"skill:{skill_dir.name}"
            discovered.append(
                SourceSpec(
                    id=skill_id,
                    title=skill_dir.name,
                    kind="codex_skill",
                    adapter="codex_skill",
                    path=skill_dir,
                    enabled=True,
                    weight=float(root_spec.get("weight", 0.75)),
                    tags=tags + ("auto-discovered",),
                )
            )
    return discovered


def load_sources(registry: dict[str, Any], registry_path: Path) -> list[SourceSpec]:
    explicit = [source_from_mapping(raw, registry_path) for raw in registry.get("sources", [])]
    by_key: dict[tuple[str, str], SourceSpec] = {}
    for source in explicit + discover_skill_sources(registry, registry_path):
        key = (source.adapter, str(source.path.resolve()))
        if source.enabled:
            by_key[key] = source
    return list(by_key.values())


def record_from_parts(
    source: SourceSpec,
    record_type: str,
    title: str,
    text: Any,
    keywords: Iterable[str] = (),
    tags: Iterable[str] = (),
    weight: float | None = None,
    metadata: dict[str, Any] | None = None,
) -> Record | None:
    body = compact_text(text)
    if not body:
        return None
    merged_tags = tuple(dict.fromkeys([*source.tags, *[str(tag) for tag in tags]]))
    merged_keywords = tuple(dict.fromkeys([*tokenize(title), *[str(k).lower() for k in keywords], *tokenize(body)[:40]]))
    return Record(
        source_id=source.id,
        record_type=record_type or infer_record_type(body, merged_tags),
        title=title.strip() or record_type or source.title,
        text=body,
        keywords=merged_keywords,
        tags=merged_tags,
        weight=source.weight if weight is None else source.weight * weight,
        metadata=metadata or {},
    )


def iter_seedance_lut(source: SourceSpec) -> Iterator[Record]:
    data = read_json(source.path)
    usage = data.get("usage", {})
    negative = usage.get("global_negative_prompt")
    if negative:
        record = record_from_parts(source, "negative", "Seedance global negative prompt", negative, tags=("negative",), weight=1.2)
        if record:
            yield record
    for item in data.get("luts", []):
        text = {
            "name": item.get("name"),
            "best_for": item.get("best_for"),
            "look_goal": item.get("look_goal"),
            "color_grade_prompt_en": item.get("color_grade_prompt_en"),
            "camera_enhancers_prompt_en": item.get("camera_enhancers_prompt_en"),
            "copy_paste_suffix_en": item.get("copy_paste_suffix_en"),
        }
        keywords = as_list(item.get("best_for")) + [item.get("name"), item.get("look_goal")]
        record = record_from_parts(
            source,
            "lut",
            f"{item.get('id', 'lut')} - {item.get('name', 'LUT')}",
            text,
            keywords=filter(None, keywords),
            tags=("lut", "color"),
            metadata={"id": item.get("id"), "rank": item.get("rank")},
        )
        if record:
            yield record


def iter_seedance_camera_quality(source: SourceSpec) -> Iterator[Record]:
    data = read_json(source.path)
    for item in data.get("style_prompts", []):
        camera = item.get("camera") or {}
        optics = item.get("optics") or {}
        lighting = item.get("lighting") or {}
        look = item.get("look") or {}
        text = "; ".join(
            part
            for part in (
                f"Style: {item.get('style_name_en')}",
                f"Category: {item.get('category')}",
                f"Camera: {flatten_values(camera, 420)}",
                f"Optics: {flatten_values(optics, 360)}",
                f"Lighting: {flatten_values(lighting, 520)}",
                f"Look: {flatten_values(look, 420)}",
            )
            if part and not part.endswith(": ")
        )
        keywords = [item.get("style_name_en"), item.get("category")]
        record = record_from_parts(
            source,
            "camera_quality",
            f"{item.get('id', 'quality')} - {item.get('style_name_en', 'quality style')}",
            text,
            keywords=filter(None, keywords),
            tags=("camera", "lighting", "quality"),
            metadata={"id": item.get("id"), "category": item.get("category")},
        )
        if record:
            yield record


def iter_seedance_camera_angles(source: SourceSpec) -> Iterator[Record]:
    data = read_json(source.path)
    for item in data.get("reference_items", []):
        title = item.get("title") or item.get("id") or "camera angle item"
        study = item.get("angle_transition_study", {})
        text = {
            "title": title,
            "primary_mood": item.get("primary_mood"),
            "camera_language_tags": item.get("camera_language_tags"),
            "recommended_shot_scale_path": study.get("recommended_shot_scale_path"),
            "transition_methods_to_study": study.get("transition_methods_to_study"),
            "signature_lesson": study.get("signature_lesson"),
            "ugc_adaptation": study.get("ugc_adaptation"),
            "negative_rule_focus": item.get("negative_rule_focus"),
        }
        keywords = as_list(item.get("camera_language_tags")) + [item.get("primary_mood"), title]
        record = record_from_parts(
            source,
            "composition",
            f"{item.get('id', 'angle')} - {title}",
            text,
            keywords=filter(None, keywords),
            tags=("camera-angle", "transition", "composition"),
            metadata={"id": item.get("id"), "reference_type": item.get("reference_type")},
        )
        if record:
            yield record


def iter_universal_prompt_skills(source: SourceSpec) -> Iterator[Record]:
    data = read_json(source.path)
    groups = {
        "cameras": ("camera", "Camera", "Prompt skill", ("camera",)),
        "lights": ("lighting", "Technique", "Prompt skill", ("lighting",)),
        "modifiers": ("modifier", "Modifier", "Prompt skill", ("modifier",)),
        "fx": ("fx", "FX", "Prompt skill", ("fx",)),
        "color_quality": ("color_quality", "Skill", "Prompt skill", ("color", "quality")),
        "recipes": ("recipe", "Recipe", None, ("recipe",)),
    }
    for key, (record_type, title_field, prompt_field, tags) in groups.items():
        for item in data.get(key, []):
            title = item.get(title_field) or item.get("Category") or item.get("Type") or key
            if prompt_field and item.get(prompt_field):
                text = item.get(prompt_field)
            else:
                text = item
            keywords = [title, item.get("Best use"), item.get("Best for"), item.get("Mood / use"), item.get("Category")]
            record = record_from_parts(
                source,
                record_type,
                str(title),
                text,
                keywords=filter(None, keywords),
                tags=tags,
                metadata={"group": key},
            )
            if record:
                yield record


def iter_markdown_sections(source: SourceSpec) -> Iterator[Record]:
    text = read_text(source.path)
    chunks = re.split(r"(?m)^(#{1,4}\s+.+)$", text)
    if len(chunks) <= 1:
        record = record_from_parts(source, "reference", source.title, text, tags=("markdown",))
        if record:
            yield record
        return
    pending_title = source.title
    pending_body: list[str] = []
    for chunk in chunks:
        if re.match(r"^#{1,4}\s+", chunk):
            if pending_body:
                record_type = infer_markdown_record_type(pending_title, "\n".join(pending_body), source.tags)
                record = record_from_parts(source, record_type, pending_title, "\n".join(pending_body), tags=("markdown",))
                if record:
                    yield record
            pending_title = re.sub(r"^#{1,4}\s+", "", chunk).strip()
            pending_body = []
        else:
            pending_body.append(chunk)
    if pending_body:
        record_type = infer_markdown_record_type(pending_title, "\n".join(pending_body), source.tags)
        record = record_from_parts(source, record_type, pending_title, "\n".join(pending_body), tags=("markdown",))
        if record:
            yield record


def iter_codex_skill(source: SourceSpec) -> Iterator[Record]:
    skill_md = source.path / "SKILL.md"
    if not skill_md.exists():
        return
    text = read_text(skill_md)
    frontmatter = {}
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            frontmatter_text, body = parts[1], parts[2]
            for line in frontmatter_text.splitlines():
                if ":" in line:
                    key, value = line.split(":", 1)
                    frontmatter[key.strip()] = value.strip().strip('"')
    title = frontmatter.get("name") or source.title
    description = frontmatter.get("description", "")
    record = record_from_parts(
        source,
        "skill",
        str(title),
        {"description": description, "instructions": body},
        tags=("codex-skill",),
        metadata={"skill_path": str(source.path)},
    )
    if record:
        yield record
    references = source.path / "references"
    if references.exists():
        for file_path in sorted(references.glob("*")):
            if file_path.suffix.lower() not in {".md", ".txt"}:
                continue
            ref_source = SourceSpec(
                id=f"{source.id}:{file_path.name}",
                title=f"{title} reference {file_path.name}",
                kind=file_path.suffix.lower().lstrip("."),
                adapter="markdown_sections",
                path=file_path,
                enabled=True,
                weight=source.weight * 0.85,
                tags=source.tags + ("codex-skill-reference",),
            )
            yield from iter_source_records(ref_source)


def iter_generic_json(source: SourceSpec) -> Iterator[Record]:
    data = read_json(source.path)
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, list):
                for index, item in enumerate(value[:1000]):
                    title = item.get("id") if isinstance(item, dict) else f"{key} {index + 1}"
                    record = record_from_parts(source, infer_record_type(stable_json(item), source.tags), str(title or f"{key} {index + 1}"), item, tags=(key,))
                    if record:
                        yield record
            else:
                record = record_from_parts(source, infer_record_type(stable_json(value), source.tags), key, value, tags=(key,))
                if record:
                    yield record
    elif isinstance(data, list):
        for index, item in enumerate(data[:1000]):
            record = record_from_parts(source, infer_record_type(stable_json(item), source.tags), f"{source.title} {index + 1}", item)
            if record:
                yield record


class AssignmentCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.values: dict[str, Any] = {}

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            name = None
            if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                name = target.attr
            if not name:
                continue
            try:
                value = ast.literal_eval(node.value)
            except Exception:
                continue
            if isinstance(value, (list, dict, tuple)):
                self.values[name] = value
        self.generic_visit(node)


def iter_legacy_prompt_python(source: SourceSpec) -> Iterator[Record]:
    tree = ast.parse(read_text(source.path))
    collector = AssignmentCollector()
    collector.visit(tree)
    for name, value in collector.values.items():
        if isinstance(value, dict):
            for key, item in value.items():
                record = record_from_parts(
                    source,
                    infer_record_type(stable_json(item), (name, str(key))),
                    f"{name}.{key}",
                    item,
                    keywords=(name, str(key)),
                    tags=("python-literal", name, str(key)),
                )
                if record:
                    yield record
        elif isinstance(value, (list, tuple)):
            record = record_from_parts(
                source,
                infer_record_type(stable_json(value[:80]), (name,)),
                name,
                list(value),
                keywords=(name,),
                tags=("python-literal", name),
            )
            if record:
                yield record


def iter_source_records(source: SourceSpec) -> Iterator[Record]:
    if not source.path.exists():
        print(f"warning: missing source {source.id}: {source.path}", file=sys.stderr)
        return
    adapters = {
        "seedance_lut": iter_seedance_lut,
        "seedance_camera_quality": iter_seedance_camera_quality,
        "seedance_camera_angles": iter_seedance_camera_angles,
        "universal_prompt_skills": iter_universal_prompt_skills,
        "markdown_sections": iter_markdown_sections,
        "codex_skill": iter_codex_skill,
        "generic_json": iter_generic_json,
        "legacy_prompt_python": iter_legacy_prompt_python,
    }
    adapter = adapters.get(source.adapter)
    if adapter is None:
        adapter = iter_markdown_sections if source.path.suffix.lower() in {".md", ".txt"} else iter_generic_json
    yield from adapter(source)


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        drop table if exists records;
        drop table if exists sources;
        create table sources (
          id text primary key,
          title text not null,
          kind text not null,
          adapter text not null,
          path text not null,
          tags_json text not null,
          weight real not null,
          indexed_at real not null
        );
        create table records (
          id integer primary key autoincrement,
          source_id text not null,
          record_type text not null,
          title text not null,
          text text not null,
          keywords_json text not null,
          tags_json text not null,
          weight real not null,
          metadata_json text not null,
          foreign key(source_id) references sources(id)
        );
        create index idx_records_source on records(source_id);
        create index idx_records_type on records(record_type);
        """
    )


def registry_db_path(registry: dict[str, Any], registry_path: Path, override: str | None = None) -> Path:
    raw = override or registry.get("database_path") or "prompt_quality_index.db"
    path = normalize_path(str(raw), registry_path)
    if not path.is_absolute():
        path = registry_path.parent / path
    return path


def index_database(registry_path: Path, db_override: str | None = None) -> dict[str, Any]:
    registry = load_registry(registry_path)
    sources = load_sources(registry, registry_path)
    db_path = registry_db_path(registry, registry_path, db_override)
    conn = connect(db_path)
    try:
        init_schema(conn)
        indexed_at = time.time()
        source_count = 0
        record_count = 0
        for source in sources:
            source_count += 1
            conn.execute(
                "insert into sources values (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    source.id,
                    source.title,
                    source.kind,
                    source.adapter,
                    str(source.path),
                    stable_json(source.tags),
                    source.weight,
                    indexed_at,
                ),
            )
            for record in iter_source_records(source):
                conn.execute(
                    """
                    insert into records
                    (source_id, record_type, title, text, keywords_json, tags_json, weight, metadata_json)
                    values (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.source_id,
                        record.record_type,
                        record.title,
                        record.text,
                        stable_json(record.keywords),
                        stable_json(record.tags),
                        record.weight,
                        stable_json(record.metadata),
                    ),
                )
                record_count += 1
        conn.commit()
    finally:
        conn.close()
    return {"db_path": str(db_path), "sources": source_count, "records": record_count}


def load_records(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return list(conn.execute("select * from records"))


def score_record(row: sqlite3.Row, query_tokens: Counter[str], wanted_types: set[str]) -> float:
    if not query_tokens:
        return 0.0
    title = row["title"].lower()
    text = row["text"].lower()
    keywords = set(json.loads(row["keywords_json"]))
    tags = set(json.loads(row["tags_json"]))
    score = 0.0
    for token, count in query_tokens.items():
        if token in keywords:
            score += 4.0 * count
        if token in tags:
            score += 3.0 * count
        if token in title:
            score += 2.5 * count
        if token in text:
            score += 1.0 * count
    if row["record_type"] in wanted_types:
        score *= 1.25
    return score * float(row["weight"])


def detect_intent(prompt: str) -> dict[str, Any]:
    lower = prompt.lower()
    is_scene = any(word in lower for word in ("scene", "shot list", "storyboard", "beats", "edit", "montage", "sequence"))
    is_video = is_scene or any(
        word in lower
        for word in (
            "video",
            "seedance",
            "nim",
            "kling",
            "motion",
            "camera movement",
            "ugc",
            "tiktok",
            "reels",
            "shorts",
            "creator ad",
            "direct-to-camera",
            "selfie",
            "iphone",
            "image-to-video",
            "lip sync",
            "testimonial",
            "hook",
        )
    )
    is_image = any(word in lower for word in ("image", "photo", "portrait", "poster", "illustration"))
    style_cues = []
    for cue in ("luxury", "ugc", "beauty", "fashion", "noir", "fantasy", "cinematic", "editorial", "anime", "cyberpunk", "horror"):
        if cue in lower:
            style_cues.append(cue)
    missing = []
    checks = {
        "camera_or_lens": ("camera", "lens", "shot on", "captured on"),
        "lighting": ("light", "lighting", "key", "rim"),
        "composition": ("composition", "close-up", "wide", "angle", "frame"),
        "color_or_lut": ("color", "lut", "grade", "palette"),
        "negative_constraints": ("avoid", "no ", "negative", "do not"),
    }
    for name, needles in checks.items():
        if not any(needle in lower for needle in needles):
            missing.append(name)
    return {
        "kind": "video" if is_video else "image" if is_image else "general",
        "is_scene": is_scene,
        "style_cues": style_cues,
        "missing": missing,
        "tokens": tokenize(prompt),
    }


def no_improve_requested(prompt: str) -> bool:
    lower = prompt.lower()
    return any(marker in lower for marker in NO_IMPROVE_MARKERS)


def wanted_types_for(intent: dict[str, Any]) -> set[str]:
    wanted = {"skill", "camera", "lighting", "color_quality", "recipe", "camera_quality", "lut", "negative"}
    if intent["kind"] == "video":
        wanted |= {"composition", "modifier", "fx"}
    if intent["kind"] == "image":
        wanted |= {"artist_style", "modifier", "fx"}
    if intent["is_scene"]:
        wanted |= {"composition"}
    return wanted


def retrieve(db_path: Path, prompt: str, top_k: int) -> list[dict[str, Any]]:
    conn = connect(db_path)
    try:
        rows = load_records(conn)
    finally:
        conn.close()
    intent = detect_intent(prompt)
    query = Counter(intent["tokens"] + intent["style_cues"] + intent["missing"])
    wanted = wanted_types_for(intent)
    scored = []
    for row in rows:
        score = score_record(row, query, wanted)
        if score > 0:
            scored.append((score, row))
    if not scored:
        scored = [(float(row["weight"]), row) for row in rows if row["record_type"] in wanted]
    scored.sort(key=lambda item: (-item[0], item[1]["id"]))
    results = []
    selected_rows = scored[:top_k]
    present_types = {row["record_type"] for _, row in selected_rows}
    required_groups: list[tuple[str, ...]] = [("negative",)]
    if "camera_or_lens" in intent["missing"]:
        required_groups.append(("camera_quality", "camera"))
    if "lighting" in intent["missing"]:
        required_groups.append(("lighting",))
    if "composition" in intent["missing"] or intent["is_scene"]:
        required_groups.append(("composition",))
    if "color_or_lut" in intent["missing"]:
        required_groups.append(("lut", "color_quality"))

    selected_ids = {row["id"] for _, row in selected_rows}
    for required_group in required_groups:
        if present_types & set(required_group):
            continue
        candidates = [item for item in scored if item[1]["record_type"] in required_group and item[1]["id"] not in selected_ids]
        if candidates:
            best_score, best = candidates[0]
        else:
            fallback = [row for row in rows if row["record_type"] in required_group and row["id"] not in selected_ids]
            if not fallback:
                continue
            best = sorted(fallback, key=lambda row: (-float(row["weight"]), row["id"]))[0]
            best_score = float(best["weight"])
        selected_rows.append((best_score, best))
        selected_ids.add(best["id"])
        present_types.add(best["record_type"])

    for score, row in selected_rows:
        results.append(
            {
                "score": round(score, 3),
                "id": row["id"],
                "source_id": row["source_id"],
                "record_type": row["record_type"],
                "title": row["title"],
                "text": row["text"],
                "tags": json.loads(row["tags_json"]),
                "metadata": json.loads(row["metadata_json"]),
            }
        )
    return results


def pick_first(records: list[dict[str, Any]], *record_types: str) -> dict[str, Any] | None:
    wanted = set(record_types)
    for record in records:
        if record["record_type"] in wanted:
            return record
    return None


def extract_prompt_skill(record: dict[str, Any] | None) -> str:
    if not record:
        return ""
    text = record["text"]
    try:
        value = json.loads(text)
    except Exception:
        value = text
    if isinstance(value, dict):
        if record["record_type"] == "composition":
            composition_parts = []
            for key in ("signature_lesson", "recommended_shot_scale_path", "transition_methods_to_study", "negative_rule_focus"):
                if value.get(key):
                    composition_parts.append(flatten_values(value[key], 360))
            if composition_parts:
                return compact_text("; ".join(composition_parts), 900)
        for key in (
            "Prompt skill",
            "prompt_skill",
            "Camera skill",
            "Lighting stack",
            "Modifier / FX / Color",
            "copy_paste_suffix_en",
            "camera_enhancers_prompt_en",
            "color_grade_prompt_en",
            "prompt_en",
        ):
            if value.get(key):
                return compact_text(value[key], 1400)
        return flatten_values(value, 1400)
    return compact_text(text, 1500)


def extract_recipe_stack(record: dict[str, Any] | None) -> str:
    if not record:
        return ""
    try:
        value = json.loads(record["text"])
    except Exception:
        return compact_text(record["text"], 900)
    if not isinstance(value, dict):
        return compact_text(value, 900)
    fields = []
    for key in ("Camera skill", "Lighting stack", "Modifier / FX / Color", "Best for"):
        if value.get(key):
            fields.append(str(value[key]))
    return compact_text("; ".join(fields), 1400)


def build_directions(intent: dict[str, Any], records: list[dict[str, Any]], no_improve: bool) -> list[str]:
    if no_improve:
        return []
    directions = []
    missing = set(intent["missing"])
    if "camera_or_lens" in missing or pick_first(records, "camera", "camera_quality"):
        directions.append("Add one coherent camera/lens package that fits the subject and generator.")
    if "lighting" in missing or pick_first(records, "lighting"):
        directions.append("Add motivated lighting with key/fill/rim logic instead of generic quality words.")
    if "composition" in missing or intent["is_scene"] or pick_first(records, "composition"):
        directions.append("Clarify shot scale, framing, camera movement, and continuity rules.")
    if "color_or_lut" in missing or pick_first(records, "lut", "color_quality"):
        directions.append("Select color grade, LUT, palette, grain, and texture cues from the quality banks.")
    if "negative_constraints" in missing or pick_first(records, "negative"):
        directions.append("Add negative constraints that prevent common AI artifacts without blocking the concept.")
    if intent["kind"] == "image":
        directions.append("Keep art-direction references as mood/technique cues, not as copied artwork.")
    return directions


def assemble_final_prompt(original: str, intent: dict[str, Any], records: list[dict[str, Any]], no_improve: bool) -> str:
    if no_improve:
        return original
    camera = extract_prompt_skill(pick_first(records, "camera", "camera_quality"))
    lighting = extract_prompt_skill(pick_first(records, "lighting"))
    composition = extract_prompt_skill(pick_first(records, "composition"))
    color = extract_prompt_skill(pick_first(records, "lut", "color_quality"))
    fx = extract_prompt_skill(pick_first(records, "fx", "modifier"))
    recipe = extract_recipe_stack(pick_first(records, "recipe"))
    negative = extract_prompt_skill(pick_first(records, "negative"))

    parts = [original.strip()]
    if intent["kind"] == "video":
        parts.insert(0, "Copy-ready AI video prompt in English.")
        parts.append("One physically plausible continuous action unless a shot list is explicitly requested.")
    else:
        parts.insert(0, "Copy-ready image prompt in English.")
    for label, value in (
        ("Camera and optics", camera),
        ("Lighting", lighting),
        ("Composition and motion", composition or ("medium shot with motivated framing, one clear action arc, readable subject silhouette, physically plausible camera movement" if intent["kind"] == "video" else "")),
        ("Atmosphere / FX", fx),
        ("Color / quality", color),
        ("Reference stack", recipe),
    ):
        if value:
            parts.append(f"{label}: {value}")
    parts.append("Preserve the user's subject, identity, props, setting, and core intent.")
    parts.append("Avoid unsupported logos, fake readable text, impossible camera moves, warped anatomy, duplicate faces, melted props, plastic skin, and over-sharpened AI texture.")
    if negative:
        parts.append(f"Negative prompt: {negative}")
    return " ".join(part.strip() for part in parts if part.strip())


def build_prompt(registry_path: Path, db_override: str | None, prompt: str, top_k: int, no_improve_flag: bool) -> dict[str, Any]:
    registry = load_registry(registry_path)
    db_path = registry_db_path(registry, registry_path, db_override)
    if not db_path.exists():
        index_database(registry_path, db_override)
    no_improve = no_improve_flag or no_improve_requested(prompt)
    intent = detect_intent(prompt)
    records = [] if no_improve else retrieve(db_path, prompt, top_k)
    directions = build_directions(intent, records, no_improve)
    final_prompt = assemble_final_prompt(prompt, intent, records, no_improve)
    return {
        "mode": "passthrough" if no_improve else "improve",
        "analysis": {
            "kind": intent["kind"],
            "is_scene": intent["is_scene"],
            "style_cues": intent["style_cues"],
            "missing_or_weak": intent["missing"],
            "token_count": len(intent["tokens"]),
        },
        "directions": directions,
        "selected_records": [
            {
                "source_id": record["source_id"],
                "record_type": record["record_type"],
                "title": record["title"],
                "score": record["score"],
            }
            for record in records
        ],
        "final_prompt": final_prompt,
        "database": str(db_path),
    }


def render_markdown(result: dict[str, Any]) -> str:
    analysis = result["analysis"]
    selected = result["selected_records"]
    lines = [
        "## Prompt Analysis",
        f"- Mode: {result['mode']}",
        f"- Kind: {analysis['kind']}",
        f"- Scene/shot-list intent: {analysis['is_scene']}",
        f"- Style cues: {', '.join(analysis['style_cues']) if analysis['style_cues'] else 'none'}",
        f"- Missing or weak areas: {', '.join(analysis['missing_or_weak']) if analysis['missing_or_weak'] else 'none'}",
        "",
        "## Improvement Directions",
    ]
    if result["directions"]:
        lines.extend(f"- {direction}" for direction in result["directions"])
    else:
        lines.append("- No changes requested; prompt is returned unchanged.")
    lines.extend(["", "## Selected Database Records"])
    if selected:
        for item in selected:
            lines.append(f"- {item['record_type']} | {item['source_id']} | {item['title']} | score {item['score']}")
    else:
        lines.append("- none")
    lines.extend(["", "## Final Prompt", result["final_prompt"], "", f"Database: `{result['database']}`"])
    return "\n".join(lines)


def command_index(args: argparse.Namespace) -> int:
    summary = index_database(args.registry, args.db)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def command_build(args: argparse.Namespace) -> int:
    prompt = args.prompt
    if args.prompt_file:
        prompt = read_text(args.prompt_file)
    if not prompt:
        print("error: provide --prompt or --prompt-file", file=sys.stderr)
        return 2
    result = build_prompt(args.registry, args.db, prompt, args.top_k, args.no_improve)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(result))
    return 0


def command_retrieve(args: argparse.Namespace) -> int:
    registry = load_registry(args.registry)
    db_path = registry_db_path(registry, args.registry, args.db)
    if not db_path.exists():
        index_database(args.registry, args.db)
    records = retrieve(db_path, args.prompt, args.top_k)
    print(json.dumps(records, ensure_ascii=False, indent=2))
    return 0


def command_self_test(args: argparse.Namespace) -> int:
    summary = index_database(args.registry, args.db)
    sample = "luxury fashion editorial portrait of a Slavic witch in a misty forest, cinematic video, dramatic light"
    result = build_prompt(args.registry, args.db, sample, 6, False)
    assert summary["records"] > 0, "index produced no records"
    assert result["mode"] == "improve", "expected improve mode"
    assert result["selected_records"], "expected retrieved records"
    assert "Final Prompt" in render_markdown(result), "expected markdown render"
    passthrough = build_prompt(args.registry, args.db, "do not improve: " + sample, 6, False)
    assert passthrough["mode"] == "passthrough", "expected passthrough mode"
    assert passthrough["final_prompt"].startswith("do not improve:"), "expected unchanged prompt"
    print(json.dumps({"ok": True, "summary": summary}, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Index prompt-quality databases and assemble improved prompts.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """
            Examples:
              python scripts/prompt_quality_orchestrator.py index
              python scripts/prompt_quality_orchestrator.py build --prompt "luxury UGC skincare video"
              python scripts/prompt_quality_orchestrator.py build --no-improve --prompt "keep this prompt as is"
            """
        ),
    )
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--db", default=None, help="Override SQLite database path.")
    sub = parser.add_subparsers(dest="command", required=True)

    index = sub.add_parser("index", help="Build or rebuild the SQLite prompt-quality index.")
    index.set_defaults(func=command_index)

    build = sub.add_parser("build", help="Analyze a user prompt, retrieve records, and assemble the final prompt.")
    build.add_argument("--prompt", default="")
    build.add_argument("--prompt-file", type=Path)
    build.add_argument("--top-k", type=int, default=10)
    build.add_argument("--json", action="store_true", help="Return JSON instead of Markdown.")
    build.add_argument("--no-improve", action="store_true", help="Return the prompt unchanged.")
    build.set_defaults(func=command_build)

    retrieve_parser = sub.add_parser("retrieve", help="Return raw matching records for a prompt.")
    retrieve_parser.add_argument("--prompt", required=True)
    retrieve_parser.add_argument("--top-k", type=int, default=10)
    retrieve_parser.set_defaults(func=command_retrieve)

    self_test = sub.add_parser("self-test", help="Run a smoke test against configured sources.")
    self_test.set_defaults(func=command_self_test)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
