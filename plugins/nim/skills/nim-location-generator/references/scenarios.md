# Scenarios and activation from user intent

## Intent map

The examples illustrate the meaning of a request, regardless of its language; they are not a list of required keywords. Conditions combine: “three nighttime angles of this kitchen with no foreground” means a series of the same place, nighttime lighting, foreground off.

If the user asks for one location (“come up with an apartment based on this portrait”), provide one cohesive concept. If they ask for “ideas/options” without a number, offer three; preserve an explicitly stated quantity in every mode.

| No. | The user wants | Mode and decision |
|---|---|---|
| 1 | “Generate a cozy living room”, “create an interior” | New image from text; Flux 2 Pro for standard realism |
| 2 | “I need a background for UGC/a talking head/an interview” | Empty character-ready plate, clear space, suitable camera; usually 9:16 for short vertical video |
| 3 | “A background for a film/a wide shot of a street”, “cinematic exterior” | Usually 16:9 for the intended use, readable depth, motivated lighting; foreground is not enabled automatically |
| 4 | “Kitchen/bedroom/bathroom/cafe/street” | Use the corresponding location type; put special details in the brief |
| 5 | “Workshop/forest/space greenhouse” | `custom`; do not replace an unknown type with a living room |
| 6 | “Come up with options”, “location ideas” | Text concepts; if no number is given, 3 distinct directions; no renders |
| 7 | “Only a prompt/JSON, do not generate” | One ready-to-use prompt or the exact number requested; JSON only on request |
| 8 | “Here is a moodboard; use its colors and mood” | Read the visual motifs; if generation is requested, use an approved Edit/image-input model and include the moodboard; new geometry is allowed |
| 9 | “Come up with an apartment based on this portrait” | A concept using visible motifs from the portrait; do not infer a biography; the person does not appear in the location |
| 10 | “Generate an interior for this character; they are a musician” | The occupation is a fact confirmed by the text; connect objects to it; send the portrait to an approved Edit/image-input model as design cues and explicitly exclude the person from the background |
| 11 | “Keep this room; change only the lighting” | Image-edit; lock geometry, furniture, materials, and camera; change only the lighting |
| 12 | “This same room based on two/four photos” | Account for all views in the contract; choose a compatible approved image-input model, such as Nano Banana Pro Edit 2K or GPT Image 2 Medium image mode at 2K |
| 13 | “The same place, at night/in winter/after rain” | Preserve anchor details; change only the related lighting, weather, and seasonal elements |
| 14 | “Another angle/a view from the window/three views of the room” | A master reference + separate, specific camera positions; not three new rooms |
| 15 | “One apartment: living room, kitchen, bedroom” | Different connected spaces; shared palette, materials, era, and details, while acknowledging a new layout for each room |
| 16 | “Make 4 variants” | In an image context: 4 images; in a concept context: 4 texts. For an ambiguous new request: text directions preserving the explicitly stated number; use 3 only when no number is given |
| 17 | “More editorial/unusual/quiet/cozy” | Change the art direction or lighting; edit an existing room without resetting its identity |
| 18 | “No foreground / add framing” | Explicitly disable/enable foreground; preserve the other settings |
| 19 | “More story, but no clutter” | `rich + minimal`; a few tidy story clusters |
| 20 | “Completely empty / a couple of visitors in the distance” | `empty` or background extras on request; the clear space remains unobstructed |
| 21 | “An advertising background in the brand colors, with space for a product” | New surroundings with a surface for the product; add the product itself only on request |
| 22 | “Move this specific product into the location” | Preserving the product requires image-input; any Nim workflow must obey the same closed model policy and reference requirements; do not substitute a similar product |
| 23 | “A sign saying ‘CAFE WORLD’, exactly like that” | Preserve the exact text and placement; check the lettering; typography does not automatically change the entire model policy |
| 24 | “4:5 / 2K / the cheapest / Recraft only” | Apply the closed model router; Recraft means V4.1 Pro, Nano Pro stays 2K, GPT Image 2 stays Medium 2K; do not hide incompatibility |
| 25 | “Repeat option 2 / use fewer details / reuse it” | Restore the brief, settings, and actual references for result 2; change only the specified conditions |
| 26 | “Save the location bible / give me the prompt and original” | Provide the available original media and save the description/links locally on request; do not promise a nonexistent history database |
| 27 | “Now animate the location / a slow camera tracking shot” | A new video request: the finished frame as a reference, then current video discovery/get and `generate_video`; the closed image-model policy applies to any generated still frame |
| 28 | “Improve the quality/size of the finished frame” | If upscaling is needed: `upscale_image` using the current schema; if details/style must change: image-edit; do not present an upscale as native 4K generation |
| 29 | “Find a Nim template for a location” | Inspect via `explore_templates` → selected `get_template` → contract; finding is not running. Before requested execution, verify all image stages obey the closed model policy; opaque/unknown models cannot establish compliance |
| 30 | “Where is a good place to shoot in Belgrade / book a studio” | Do not activate the generator: this is a search for real places or a booking |
| 31 | “Make a map/drawing with exact dimensions” | Do not present an artistic render as a measured plan; if only an environment concept is needed, state its purpose |

## A. Quick start without references

“Generate a warm UGC background with no people” is enough to start. Use one frame, restrained, lived-in/natural, foreground off; assume a neutral living room if no place is specified. Briefly state this along with the selected model. Do not ask the user to fill in every setting.

“Come up with something for a background” means ideas by default. Offer three concepts with distinct spatial ideas, lighting, and detail clusters. “Make the second one” after text concepts authorizes creating an image of the second concept if the context clearly points to a render; if the user previously specified “prompts only for this entire conversation”, preserve that mode.

## B. References with different purposes

Before selecting the model, map the roles: `ref-1 = geometry`, `ref-2 = palette`, `ref-3 = product identity`. Do not claim to have seen a file if viewing it is unavailable. If a required photo is inaccessible, ask for an accessible image; meanwhile, prepare only the known text portion.

“Make a background for this person” is not an instruction to copy the person into the image. Use visible colors/textures and the intended shot scale. If asked to invent a story, use an explicitly fictional creative hypothesis. If the user describes the character as a fictional architect, that is an acceptable fact in the brief.

Style and identity transfer different properties: “in the spirit of this kitchen” allows a new room; “this same kitchen” preserves its geometry. Both use an approved Edit/image-input model when generating from supplied images. A room photo plus a palette moodboard counts as two inputs; do not reduce either to text to fit a one-image model. If ambiguity materially affects cost or accuracy, clarify the role; do not ask about every obvious image.

## C. Preserve the place and change one parameter

For “the same room at night”, make two lists:

- Preserve: walls, openings, furniture, relative positions, materials, large decor, camera, and framing unless a new angle was requested.
- Change: time and light sources, the resulting shadows/reflections; the view outside the window if it naturally changes at night.

Do not add new story clusters on top of a precise edit. Do not rebuild the interior from defaults. “Cozier” in this context does not authorize changing all the furniture: start with the lighting and explicitly requested accessories.

## D. Angles and sequences

1. Find an existing master frame. If there is none and the user requests a new series, prepare a shared brief and first create one master **within the requested quantity**. If a master already exists, do not count it as an additional new result.
2. Record the location bible following [location-language.md](location-language.md).
3. Define separate views: for example, from the entrance toward the window; from the corner by the window toward the sofa; a side view of the work area. Specify visible anchor details and align the perspective.
4. Generate views from the original verified master. A chain where “each next image uses the previous one” can accumulate changes; use it only when a sequential transformation is actually needed.
5. Check the positions of anchor objects. Do not promise to reconstruct unseen walls with measurement-level accuracy.

For different rooms in one apartment, the bible stores the design language and plausible connections between spaces. It does not require every room to have the same geometry.

## E. Variants and model comparisons

Different concepts need different prompts. Random variations of one prompt can be generated through `batchSize` if the contract allows it. The current Nim image call allows a number from 1 to 4 per call; the actual schema and model contract take precedence over this guidance. For larger quantities, split the request into permitted groups, preserving numbering and budget.

“Compare Flux2 and Recraft” without a request for images means a text comparison of Flux 2 Pro and Recraft V4.1 Pro suitability and current constraints. “Generate one with each” means two images with the same brief/format, where compatible. Comparisons may also include Nano Banana Pro 2K and GPT Image 2 Medium 2K when requested. Supplied images require the corresponding approved image modes; text-only Recraft cannot replace an unavailable Edit variant.

Do not silently multiply results: 3 directions × 2 models × 4 seeds = 24 paid jobs, not “3 variants”.

## F. Errors and continuation

| Event | Next action |
|---|---|
| Nim MCP is unavailable | In text mode, finish the concept/prompt; for an image, clearly explain that a connected Nim service is required; do not silently replace it with another service |
| Not authenticated | Let the user complete the available standard sign-in flow; do not search for tokens in local files |
| Uploading a required photo failed | Fix the upload or request the file; do not switch to text-only |
| Model not found/schema changed | Repeat discovery and selection; do not guess an ID |
| The contract does not accept the photo count/format/resolution | Select a compatible approved model with all references and fixed Nano/GPT settings; if none fits or a hard model choice conflicts, explain and wait for a decision |
| Insufficient credits | Report the actual result and available Nim options; do not reduce quantity/quality or buy credits automatically |
| Job is still queued/running | Continue tracking its ID; exceeding estimatedDuration does not mean failure |
| Submission outcome is unknown | First establish the status of the accepted job; do not submit a duplicate |
| Part of the batch is ready, part failed | Deliver completed results with their numbers; identify failed results separately; do not repeat successful ones |
| Unwanted people, an object near the lens, incorrect lettering | Identify the detected defect; prepare a precise edit. A new paid run must stay within the already agreed iterations/budget or follow a new request |
| “Bring back the previous variant” | Return its existing result instead of generating it again |

Execution and result details: [nim-workflow.md](nim-workflow.md).
