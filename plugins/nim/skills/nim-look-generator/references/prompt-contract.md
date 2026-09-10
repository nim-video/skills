# From intent to a reproducible image prompt

Before the outfit prompt, prepare and complete the separate casting portrait under [face-first.md](face-first.md). The face prompt defines identity; the outfit prompt uses its completed image as a reference. Text-only delivery describes this dependency without creating jobs or fictitious URLs.

## Internal plan for one variant

The current assistant performs the source's stylist/system-prompt work: interpret wishes, resolve constraints, build and locally check the plan, and assemble the final image prompt. No separate text-model API or Nim generation job is needed for those operations. Nano Banana Pro receives the finished visual assignment and renders the image; do not ask it to return wardrobe-planning JSON or execute the Skill's control logic.

The plan is the agent's working structure, **not Nim parameters**. Each variant contains:

- `aesthetic`: the exact selected preset label or a concise original description for free mode; metadata only.
- `silhouette`: a concrete relationship between volumes and lengths.
- `keyGarments`: physical items described by cut, fabric, color, fit, and construction; the user/references determine the count.
- `outfit`: the coherent final composition, with every mandatory item present exactly once physically even if mentioned in several fields.
- `palette`: 2–3 named colors by default; the exact user/reference palette takes priority. A requested monochrome look does not require inventing a second color.
- `accessories`: only present shoes/headwear/socks; `bag`, `jewelry` are dedicated fields for additional ON-controls. Specifically requested/referenced bags/jewelry enter the inventory and outfit independently of the control.
- `extras.outerwear`, `extras.props`: only when the corresponding additional control is ON.
- `stylingGestures`: exactly two coordinated techniques when Styling is ON; otherwise absent. An explicitly specified way of wearing an item still belongs in the outfit.
- `grooming`: only when a person is present, respecting permitted changes; do not describe hair as a new styling choice without an explicit request.
- `materialRealism`: two appropriate material details that preserve the item's exact condition.

Omit unnecessary fields; do not send `none`, `n/a`, empty accessories, or lists of alternatives into the final scene. Do not turn "a red jacket" into an all-red outfit. Express a broad direction such as "romantic utility" through 2–3 connected visible choices; do not stop at a label.

## Reference inventory

For each item, record: the specific visible product + how it is used + locks + permitted changes. If one photo contains several selected items, list each separately under the same image index. Do not invent logos or indistinct details. Do not copy the face, body, or background from a product photo.

For each inspiration photo: the visible source category, 1–8 concrete fashion cues, and what must not transfer. Synthesize one combined idea, 2–4 coordinated clothing choices, and up to 12 necessary constraints. "80/20" means relative emphasis in the clothing, not an exact share of pixels. The user may assign the palette to one source and the material to another; preserve that assignment. A free blend does not require its labels to exist in the preset library.

## Final prompt order

1. **Result and layout:** a single frame, one sheet, a flat lay, or the explicitly requested composition.
2. **Subject/identity:** whose outfit is shown, or the complete absence of a person.
3. **Reference roles:** map the images actually submitted to the face, item, base edit, or inspiration.
4. **Resolved outfit:** silhouette → garments → how they are worn/layered → only present accessories → permitted grooming → palette and material.
5. **Background, framing, lighting:** follow the user's request, otherwise the appropriate mode default.
6. **Continuity and exclusions:** only those relevant to the task, with no contradictory requirements.

Translate aesthetic labels into visual properties; they do not replace clothing descriptions. Do not repeat the raw user request or the entire internal JSON. Use a concrete positive prompt and a short constraint block. Send aspect ratio/resolution separately to the tool according to its contract.

## Layout

**Default lookbook sheet:** one image containing one complete front view and one complete back view, plus compact detail crops of present garments, shoes, and specified accessories. Both main views are uncropped: head (when a person is present), clothing, legs, and all footwear. Keep the same outfit throughout, without labels; use a neutral background and soft studio light. Do not add a third main view merely because the face rules mention three-quarter views.

**Outfit-only sheet:** front/back garment views on an invisible form or dimensional flat lay, without a body/skin/hands/face/hair. Do not require a head-to-toe person in this branch. **Flat lay:** one outfit arranged and viewed from above, unless the user requests multiple panels. **Single full-body:** one complete person in one frame, without a sheet, inset, or additional views. **Series of views:** one locked outfit; separate files only if requested. **Detail-only:** a specific construction detail/item, without requiring the whole figure.

"Leave the background unchanged" disables the studio default: the base image determines the background, framing, and lighting to the extent that the user preserves them. For a lifestyle scene, depict that scene instead of imposing the studio template. If the requested aspect ratio is incompatible, resolve it through model routing before submission.

## Identity and continuity

For a referenced person, require a complete natural face in front/three-quarter views, the same identity across views, and preservation of the body/hair except for explicitly permitted changes. For the rear view, show the natural back of the same person's head, without a face on the back. Do not invent new facial traits in the clothing brief. A newly cast character uses the actual Recraft portrait across all person-bearing looks and panels. These face requirements do not apply to outfit-only output.

For example: "Image 1 defines identity only. Preserve this person's facial structure, apparent age, skin tone, and hair. Replace the portrait's incidental top with the complete outfit below. Show the whole person including head and shoes; do not copy the portrait's shoulder crop. Use the specified scene and lighting." Describe body proportions as planned unless a full-body base actually establishes them. The portrait top does not enter `keyGarments`, the palette, or the locked item inventory.

Across all views and crops of one outfit, preserve the items, colors, print and its placement, closures, layer order, lengths, footwear, accessories, and exact styling gestures. A detail crop must not create a new item. Do not add invented brands/readable text; if the user explicitly requests lettering, record it separately and check the model's capabilities without promising perfect reproduction.

## Variation

Plan the requested outfits together. Where possible, distinguish them along three unlocked axes from: palette, print, fabric, silhouette, composition; include silhouette/composition when available. If only one axis remains free, vary only that axis and state the limitation on diversity honestly. With a fully locked wardrobe, permitted garment handling/presentation may vary, but do not present a new view as a new wardrobe. For a capsule, establish the shared item list first, then build combinations without silently adding items.

## Complete example: free outfit-only lookbook

User: "Generate a photorealistic lookbook without a person: only a cream sweater, chocolate trousers, and loafers. No bags or prints." `delivery=generate`, `styleMode=free`, 1 sheet, outfit-only, 16:9, controls OFF. First create the separate Recraft V4.1 Pro casting portrait, unless the user explicitly prohibits portrait generation. The assistant assembles the outfit prompt below; Nano Banana Pro text-input renders it, with no portrait reference in this person-free image. Start with supported 2K unless requested otherwise, subject to the live contract and total budget. Count and disclose the casting asset separately from the requested outfit.

```text
Create one photorealistic outfit-only lookbook reference sheet on a clean warm-gray background under soft even studio light. Show two large views of the same complete outfit, front and back, on an invisible garment form, with small detail crops of the knit, trouser waistband and shoes. No person, body, skin, face, hands or hair.

The complete inventory contains exactly three items: a cream midweight merino crewneck sweater with a relaxed straight cut, ribbed collar and cuffs, and a softly falling hem; chocolate wool-twill trousers with a mid-rise waistband, two restrained front pleats and a full-length straight leg; chocolate leather penny loafers with a low stacked heel and a gently rounded toe. A pair of loafers is one inventory item. Balance the relaxed sweater volume with the long straight trouser line. Preserve visible merino fibers, natural wool drape and subtle leather texture without adding damage.

Keep the same garments, proportions, construction, colors and shoe design in both main views and all detail crops. Fully show the sweater, trousers and shoes in both main views. Palette: cream and chocolate. Plain surfaces only: no printed or decorative color motifs, stripes, checks, logos or readable text. No additional layers, bags, jewelry, belt, headwear, props or accessories. No labels and no duplicated items outside the requested detail crops.
```

This is a prompt example, not a ready-to-submit tool payload: it contains no fixed UUID, resolution, seed, or upload URLs. For other requests, preserve the structure rather than this example's items.
