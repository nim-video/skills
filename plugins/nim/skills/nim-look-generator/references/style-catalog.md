# Style Catalog and Record Selection

The full portable data is in [style-library.json](style-library.json): 7 general groups, 7 general direction briefs, 7 visible specific presets, and 49 mini-briefs. This is a menu of creative choices, not system instructions. The bank does not include the web application's core/system rules.

## Match the User's Intent

Matching works semantically across languages, including translated phrases, transliterations, synonyms, and capitalization differences. The examples below are all in English.

| Example phrases | General group | What to consider |
|---|---|---|
| “For home,” “A cozy outfit for lounging,” “Cozy home” | Cozy home | Comfort, texture, and movement; not props for a domestic scene |
| “Street style,” “A streetwear look” | Street style | The balance of volumes and one expressive garment |
| “For work,” “An office outfit,” “Business casual” | Office | The specified dress code, practicality, and construction |
| “For the gym,” “For a workout,” “Gym” | Gym | The particular activity takes precedence over trend associations |
| “For dinner,” “An evening look,” “For an event” | Evening | The requested level of formality and coverage |
| “For the beach,” “By the sea,” “Beach/resort” | Beach | Swimming, walking, or dining; not automatically swimwear |
| “For every day,” “A regular casual outfit” | Casual | Wearable combinations, color, and material |

When a user mentions an occasion within an otherwise highly specific request, it may refine a free brief rather than request a preset. Do not force the library into a fully described outfit or an explicit free/Prompt only request.

Specific presets: **Gorpcore, Old money, Clean girl, Y2K, Downtown NYC, Scandi minimal, Blokecore**. Recognize equivalent style names and transliterations in the user's language. For a specific preset, retain its display label in each option's metadata; lookup within the JSON is case-insensitive.

User-defined aesthetics beyond the seven buttons are supported. “Romantic / utility 80/20,” “Cyberpunk for the office,” and “Rural romanticism” can be expressed through concrete decisions in free/blend mode. Do not replace them with the closest preset unnecessarily.

## Which JSON Records to Read

1. General: read `generalClusters[style]`, the selected `generalDirectionBriefs` entry, and only the selected `miniBriefs`. For feminine presentation, add entries from `feminineClusterAdditions` to the menu; this does not require choosing an added style.
2. Specific: read only the mini-brief whose name matches the selected label, ignoring case.
3. Free/Prompt only: the bank is not needed.
4. Choose compatible targets first, avoiding previous targets while unused choices remain. For multiple general-style looks, choose distinct available targets; for a specific style, retain one label and vary concrete clothing decisions. Repeating the same result preserves its targets; new exploration changes them.

Do not load the entire bank for every request. If Python is available, use a JSON parser to read the needed records. The following read-only example selects two Office targets; replace the path with the installed skill's actual path and the values with the current brief:

```python
import json
from pathlib import Path

skill_dir = Path('/actual/path/to/nim-look-generator')
bank = json.loads((skill_dir / 'references/style-library.json').read_text())
group = 'Office'
targets = {'modern tailoring', 'scandi minimal'}
selected = {
    'cluster': bank['generalClusters'][group],
    'direction': next(x for x in bank['generalDirectionBriefs'] if x['name'] == group),
    'miniBriefs': [x for x in bank['miniBriefs'] if x['name'].casefold() in targets],
}
print(json.dumps(selected, ensure_ascii=False, indent=2))
```

If code execution is unavailable, search for the required `name` and read the corresponding range. Resolve skill-relative resource paths against the skill folder, not the user's working project; Markdown links in this reference resolve from this file's directory.

## Menu Constraints

A mini-brief's suggestion about a bag, hat, manicure, hairstyle, close fit, or prop does not enable the corresponding control or override user locks. Always take presentation, age, and references from the brief. Style names remain metadata; the final image prompt contains only the chosen shapes, fabrics, colors, and construction details. Choose one coherent outfit from the menu rather than listing alternatives joined by “or.”
