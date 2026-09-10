# Brief and control semantics

## Priorities

The user's current explicit instruction takes priority over previous settings, presets, and the source application's internal rules. Resolve conflicting requirements before choosing a model. If two simultaneous hard requirements conflict ("only these three items" and "add a fourth"), ask about that specific conflict; do not hide it behind an artistic interpretation.

A product reference locks the item's appearance until the user explicitly requests a change. "Recolor this jacket red" authorizes changing that jacket's color while preserving the rest of its construction. The source application's rule that product references are immutable does not override this edit. Matching references and text about the same item describe one physical item; "a second / a different / another one" creates a separate item.

The actual MCP contract determines what is possible, but does not authorize silently replacing the user's request. `matchesConstraints=false`, an unsupported size, or too few image slots require another candidate or agreement on a specific compromise.

## Internal brief

The current assistant constructs and checks this brief. Its host language model is separate from the Nim image renderer selected below; do not require the user to choose another planning model. Keep only the necessary fields in context:

| Field | Value |
|---|---|
| delivery | advice / prompts / generate / edit |
| styleMode | free / general / specific / blend |
| style, aestheticTargets | Selected group/style; targets only for presets |
| optionCount | Number of **distinct outfits**, default 1 |
| renderMode | sheet / single / flat-lay / ghost / requested layout |
| subjectMode | new-adult-person by default / reference-person / explicitly requested outfit-only |
| casting | series ID, character ID, identityOrigin, state, model, prompt, parameters, job IDs, completed portrait URL, observed traits, explicit override if any |
| presentation | neutral by default; masculine/feminine on request |
| lockedItems, changes, exclusions | Items, permitted changes, exclusions |
| refs | For each: accessible path/Nim file URL, role, item/person, order; generated portrait first for new person-bearing outfits |
| controls | bag, outerwear, props, jewelry, styling, print, sexy; all false by default |
| hairChange | Only an explicitly requested hair change, understood in any language |
| aspectRatio, resolution | User request or an appropriate default |
| modelPreference, quality, budget | Outfit image renderer: Nano Banana Pro by default / explicit override; supported 2K default; known spending limit |
| previous | Saved brief, targets, prompt, model, jobs, completed outputs |

`optionCount` is not the number of views. "Three views of one outfit" means one inventory and three views. The image count depends on whether the user requested one sheet or separate files. A "capsule" means one shared set of items reused in several combinations, not three independent wardrobes.

`casting` belongs to the series, not each outfit. Track `planned / queued / running / usable / failed / inspection-needed` separately from the service's actual job status. A portrait is not one of the requested outfits. Start new fictional casting through Recraft V4.1 Pro before outfit generation; reuse it for continuations. Follow [face-first.md](face-first.md) for explicit identity/text-only overrides, person-free output, costs, and the required dependency.

Use an honest `identityOrigin`: `recraft-cast`, `other-cast`, `user-reference`, `existing-character`, or `first-outfit` for the explicit no-casting path. The field records actual provenance, not the preferred model.

## Clothing and controls for additional items

In the source, Bag/Outerwear/Props/Jewelry meant **inventing an additional item**, not permitting the entire category to exist. Preserve this meaning when the user explicitly operates switches:

| Control | ON | OFF |
|---|---|---|
| Bag | Exactly one new bag beyond mandatory reference/text-requested items | Do not invent an additional bag |
| Outerwear | Exactly one separate worn outer layer beyond mandatory items | Do not invent an additional layer |
| Props | Exactly one appropriate activity/scene object | Do not invent scene objects |
| Jewelry | Exactly one additional jewelry item | Do not invent jewelry |

An explicit "wear my bag" adds/preserves that one bag and **does not activate** Bag. "Turn Bag on" activates the additional category. "Add a bag" when no bag is present creates one concrete user-requested item, without a duplicate addition. "Add another bag" creates one new item beyond the existing one; do not double it by also activating the control. "Bag is off, but use the bag in the photo" preserves the referenced bag.

"No bags / remove the bag entirely" explicitly excludes the entire category in the current edit; it is more than OFF. It supersedes the earlier bag requirement; if the user simultaneously requires preserving that same bag, resolve the conflict. "No accessories" and "only these items" close the inventory: do not add belts, socks, jewelry, hats, gloves, or props that contradict the exact item list. Do not require a second garment for a dress or jumpsuit. Count a pair of shoes as one item unless the user defines the count differently.

By default, additional outerwear is worn over the existing layer, remains visible, and does not replace it. Carrying it, draping it over the shoulders, or tying it around the waist is allowed only when the user chooses that treatment for this layer. Keep mandatory items visible; report a conflict if the combination is physically impossible.

## Styling, Print, Sexy

**Styling ON:** close the inventory first. Choose two coordinated techniques using existing garments: one visible transformation of the overall composition and one supporting detail on a different zone. Name the item, area, degree of adjustment, and visual effect; use no more than 200 characters per technique. Examples: a diagonal hemline + a partial tuck; an offset fastening + collar shaping. For a single garment, work with two of its zones. Do not add clothing to satisfy the second technique. When garment handling is locked, describe the existing composition and detail without changing them. OFF disables invented elaborate techniques, but does not cancel "roll up the sleeves" in the user's text.

**Print ON:** at least one eligible garment in every outfit must have a visible print; specify its motif, placement, scale, and colors. Do not recolor or print on a locked product without permission. If all garments are locked and solid-colored, a specific change must be authorized. **Print OFF:** there is no requirement to add a print; it does not prohibit patterns. **"No prints"** prohibits additional graphics, lettering, stripes, checks, monograms, and patterns. Ordinary knit texture is not a printed motif. If a prohibited pattern already appears on an immutable item, resolve the conflict before generation.

**Sexy ON / "sexier" / "more sensual":** adult, non-explicit fashion only, using fit, drape, material, permitted cutouts, and proportions. Do not add nudity or change the body. **OFF:** do not impose sexualization; an explicit request for a particular cutout or silhouette remains valid. **"No sexualization / more covered"** explicitly constrains coverage and presentation. For a minor or an unclear age, do not use the sexualized branch; offer an ordinary age-appropriate outfit. Evening, Beach, Clean girl, or feminine styling alone does not activate Sexy.

## Presentation, identity, and realism

Presentation describes clothing, not the person's gender, identity, or body shape. Neutral means restrained, broadly wearable proportions; masculine means menswear construction; feminine means appropriate womenswear proportions. For neutral/masculine, default to trousers, practical shorts, broadly wearable shirts, and knitwear; introduce skirts, dresses, leggings, unitards, bodysuits, corsets, and bandeau pieces only when explicitly requested or required by a product reference. Preserve such requested items under any presentation. Feminine permits them as options but does not require exposure or a tight fit. Do not infer presentation, ethnicity, age, or profession from appearance. Do not introduce makeup/manicure by default in neutral/masculine; an explicit user request overrides the default.

With an identity photo, preserve the face, skin tone, apparent age, build, stature proportions, and hair; do not promise mathematically exact matching. Change hairstyle/color/length only when explicitly requested, including requests phrased in Russian. A face in a product/inspiration photo does not become the identity reference. If several identity photos clearly show different people and the target person is unspecified, clarify. For outfit-only, exclude people, skin, hands, faces, hair, and grooming.

For a newly cast character, the completed Recraft portrait becomes the identity photo and locks the observed face/hair. Do not invent full-body measurements from a headshot; choose unspecified body proportions once and preserve them after the first full-body result. Outfit-only exclusions apply to outfit images; the initial casting portrait stays a separate asset unless the user explicitly prohibits all portraits. Preserve an explicitly supplied identity instead of creating a replacement person.

Default realism: natural fabric drape and one other appropriate texture detail. Do not age a new product or add wear to a locked product; "a new item for a catalog" allows realistic clean material without invented wear.
