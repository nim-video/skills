# Model routing

The Nim video catalog is live and changes. Discover, do not hardcode. A model
identifier written here is a starting point for discovery, not a contract.

## Preferred target

**Seedance Reference-to-Video** (the Seedance 2 Advanced Mode entry, found with
`models_explore`). This is the model this
skill is built around: it accepts a source clip that defines the performance and
identity references that define who performs it.

**Provider preference: runware.** When both a runware-backed and a fal-backed variant of
the same Seedance reference-to-video model are offered, select the runware one. Do not
invent a provider selector, provider-specific endpoint, or a second submission to the
other provider; the provider is a property of the discovered model entry, not an extra
argument. If the discovered entry does not expose provider metadata, say so instead of
guessing.

For sources over 15 s ([long-videos.md](long-videos.md)) use **Seedance 2** Advanced Mode for every part,
not Seedance 2.5 and not a mix of models.

Do not substitute another family for this job. Text-to-video and image-to-video cannot
carry an existing performance, and a different reference-to-video family is a different
skill, not a fallback. If no reference-to-video model is available, report the blocker
and prepare the prompt and depth reference as interim work without spending.

## Discovery and exact variant selection

1. Use `models_explore` with `action: "search"` or `"recommend"`, `type: "video"`, and
   the input requirement when the action supports it. Filter results against this
   policy yourself; a recommendation cannot authorize another family.
2. Call `action: "get"` for the chosen model only. Read `generationContract.required`,
   `.optional`, `.forbidden`, allowed values, file-input count, supported aspect
   ratios, supported durations, and current price estimates. Follow
   `next_page_token` when the needed variant is not on the current page.
3. Resolve the exact version and input mode from returned metadata. Seedance 2,
   Seedance 2.5, Seedance 2 Mini, Seedance 2 Fast, and the Advanced Mode entries are
   distinct models that can share a display name. Name matching alone is not
   identification.
4. Pass only fields the contract allows. Do not invent `negative_prompt`, `style`,
   `quality`, `width`, `height`, `image_urls`, `strength`, a mask, or a custom endpoint.
   Style and exclusion instructions belong in the prompt.

Tool names may carry prefixes such as `mcp__nim__...`. Discover callable tools instead
of inventing a namespace, and do not hardcode UUIDs or prices from memory.

## Input rules for this job

| Input | Role | Notes |
|---|---|---|
| `@vid1` | Motion reference - the depth clip | Exactly one. It carries motion, timing, camera, and framing, and nothing else |
| `@img1` | Identity | Required. Without it the model reinvents the face and wardrobe on every run |
| `@img2`+ | Wardrobe, product, or environment | Optional. One job each; never let a role silently merge with identity |

Constraints that matter before submitting:

- **The source clip must have a real aspect ratio and a usable pixel count.** Aspect is
  inherited from the reference in reference-to-video mode, so a landscape source and a
  portrait output fight each other. Match the requested output shape to the depth clip.
- **Provider limits, not Nim guarantees:** the ByteDance reference-video path can reject
  clips below 409,600 pixels and expects the reference as a fetchable web URL rather than
  inline data. This is why the depth step produces a 480p-or-larger clip that is uploaded
  through `media_upload`. Verify against the live contract; do not present these numbers
  as Nim's documented limits.
- **Duration follows usable motion.** Set the output duration to the portion of the
  source that actually contains motion. Longer outputs invent the tail.
- **Reference capacity.** Identity plus wardrobe plus environment plus the depth clip
  must fit the contract's file-input count. Drop optional roles rather than the identity
  reference; never drop the motion reference, because that changes the task.

## Cost

Track both bills internally and include their amounts in the single confirmation from SKILL.md, without explaining preprocessing:

1. The **depth step**, billed per second of source video by its provider. A long source
   costs real money here before Nim is involved at all.
2. The **Nim generation**, priced by the discovered contract for the chosen duration,
   resolution, and variant count.

Follow [pricing.md](pricing.md) to include video-reference charges and distinguish
base price, full quote and empirical estimate. Read [depth-provider.md](depth-provider.md)
for the depth-side rates, and the live
contract for the Nim side. Keep the cost breakdown internal; present the combined concise estimate, keeping dollars and credits separate. Check `get_credit_balance` before a multi-variant or
high-resolution run.

## Verified guidance, not a static contract

Capability guidance as of 2026-09:

- Reference-to-video entries exist under several families, which is
  why discovery is mandatory rather than optional.
- A `batchSize` field appeared on all audited video entries, but its presence in the
  tool does not make it valid for every model. Confirm it in the contract before using
  it to produce variants.

Recheck MCP before every actual run. Current contracts take precedence over any dated
snapshot, and this policy remains in force.
