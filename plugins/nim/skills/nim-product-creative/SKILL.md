---
name: nim-product-creative
description: >-
  Use when the user wants commercial product visuals or videos from product
  images, reference assets, or a product brief: ecommerce listing images,
  product photoshoots, studio/catalog shots, white-background product photos,
  lifestyle scenes, ad creatives, hero images, product launch visuals, social
  content, UGC-style creatives, on-model apparel/accessory shots, Shopify/Amazon
  PDP assets, product-in-use scenes, product videos, or similar selling,
  merchandising, marketplace, brand, or campaign imagery. Search Nim templates
  first for product/photoshoot/ad-style workflows, show the user matching
  template options with cost/input info, get an explicit template choice or
  approval, inspect the selected template contract, collect required inputs,
  upload references, and run the template. Fall back to Nim model generation
  only when no suitable template exists or the user explicitly asks for raw
  generation.
---

# Nim Product Creative

Create commercial product imagery and product videos through Nim. Treat the
user's wording as examples, not a closed trigger list: route by intent. If the
request is about making a product, SKU, garment, package, object, or brand asset
look sellable, shoppable, campaign-ready, or usable in ecommerce/social/ads,
start with Nim templates.

## UX Rules

1. **Search templates first.** For commercial/product creative, call
   `explore_templates` before choosing raw generation models.
2. **Show before spending.** Do not call `run_template`, `generate_image`, or
   `generate_video` in the first response unless the user explicitly said to
   auto-run, use the best option, or skip choices. First show the selected or
   shortlisted template(s), cost, and required inputs, then ask for confirmation.
3. **Do not over-ask.** Ask only for required assets or choices that the selected
   template contract requires.
4. **Use template contracts as source of truth.** After the user picks or
   approves a template, call `get_template` and follow its `templateContract`
   exactly.
5. **Keep template choice user-facing.** Show a concise shortlist with title,
   output type, price, and required inputs. Do not dump raw JSON.
6. **Never pass local paths directly.** Upload local files or attachments with
   `media_upload`, then pass returned Nim file URLs to `run_template`.
7. **Poll to completion.** `run_template` is async. Poll
   `get_generation_status` until `finished`, `failed`, or `cancelled`, then
   return the real media URL.

## Intent Detection

Use this skill when the user asks to create, improve, place, stage, model, sell,
advertise, merchandise, or make content for a product or object.

Strong signals include:

- **Product/object language:** product, item, SKU, merch, bottle, package,
  garment, shoe, watch, furniture, device, accessory, beauty product, apparel,
  brand asset.
- **Commercial-use language:** store, listing, ecommerce, Shopify, Amazon, PDP,
  marketplace, catalog, ad, campaign, launch, hero, banner, social, Meta ads,
  TikTok, content, creative.
- **Transformation language:** make this into, shoot it as, put it on, place it
  in, show it in use, make it premium, make variations, create product shots,
  make this sell better.
- **Reference-media language:** this image, attached product, my product photo,
  use this bottle, use these assets, on this model.

If the request is clearly commercial/product-oriented but the exact style is
unclear, search broadly rather than asking a style question first.

## Template Search Strategy

Build the template query from the inferred creative need. These are starting
points; adapt them freely to the user's words.

| Inferred need | Template query |
|---|---|
| Generic product creative | `product photoshoot ecommerce ad creative` |
| Clean listing/catalog | `product studio ecommerce white background catalog` |
| White-background product shot | `product white background studio ecommerce` |
| Lifestyle/product-in-use | `product lifestyle photoshoot in use` |
| Social or UGC | `UGC product ad social creative` |
| Hero image or campaign visual | `product ad hero campaign commercial` |
| Apparel/accessory on model | `on model fashion product photoshoot` |
| Beauty/cosmetics | `beauty product routine product photoshoot` |
| Product video/ad | `product video ad commercial product animation` |
| Surreal/viral ad | `surreal product ad viral commercial` |

Default broad query when uncertain:

```text
product photoshoot ecommerce ad creative lifestyle studio UGC
```

Use `explore_templates` with `action: "recommend"` for broad matching. Use
`action: "search"` when the user asks for a specific template type or phrase.
Start with 4-6 templates unless the user asks for more.

## Workflow

1. **Identify commercial intent.** Infer whether the user wants product imagery,
   product video, listing assets, ad creative, UGC, on-model output, or a
   related commercial visual.
2. **Search templates.** Call `explore_templates` with a query based on the
   intent. If multiple intents apply, include the product type and strongest
   commercial use in the query.
3. **Present options before any paid run.** Show a short list with:
   - title
   - slug
   - output type
   - price credits
   - required inputs from `inputSummary`
4. **Ask for template approval.**
   - If several templates fit, ask the user to choose one.
   - If one result is clearly best, recommend it, but still ask for approval
     before running.
   - If the user already said "use the best one", "go ahead", "just do it",
     "auto-run", or equivalent, you may choose the best fit and continue.
   - If results are weak or mixed, ask which direction they want before
     inspecting/running anything.
5. **Select or infer a template only after approval.**
   - If the user picks one, use it.
   - If the user approved your recommendation, use it.
   - If the user explicitly delegated choice, pick the strongest fit.
6. **Inspect the contract.** Call `get_template` for the selected `slug` or
   `template_id`.
7. **Collect missing required inputs.** Ask only for required files, prompts,
   selects, or settings from `templateContract.required`. Ask about optional
   settings only when they materially change the output, especially aspect ratio,
   number of outputs, image/video count, or photo type.
8. **Upload references.** For every local file or attachment needed by the
   template, call `media_upload`, run the returned upload command, and use the
   returned `file_url` in `run_template.inputs.files`.
9. **Run and poll.** Call `run_template`, then poll `get_generation_status` until
   terminal status. Return the final media URL and relevant settings.

## Fallback To Models

Use raw Nim generation instead of templates only when:

- template search returns no suitable result;
- the user explicitly asks for a specific model or raw image/video generation;
- the request is a simple edit better handled by an image-edit model;
- the user rejects template-based options.

Fallback model routing:

- Still image, background replacement, product restyle, catalog-style output:
  use `models_explore` for image edit/generation.
- Product animation or ad clip without a suitable template:
  use `models_explore` for video, with `input: "image"` when a reference product
  image is supplied.

Always inspect the chosen model with `models_explore action=get`, follow the
`generationContract`, upload references with `media_upload`, generate with
`generate_image` or `generate_video`, and poll until terminal status.

## Prompt And Input Handling

When a selected template has a free-text prompt/details field, compress the
user's intent into a practical commercial brief:

```text
Create a polished commercial product visual for <product>. Intended use:
<store/ad/social/campaign>. Style: <studio/lifestyle/UGC/on-model/hero/etc>.
Preserve product identity, shape, labels, materials, and key brand details.
Avoid distorted text, fake logos, wrong packaging, extra products, watermarks,
and unreadable labels unless the template intentionally transforms the product.
```

For apparel/accessory on-model requests, include the wearer/model intent only if
the template supports a character/model input or prompt field. Do not invent that
a template can preserve a model identity unless its contract supports the
required reference.

For white-background or catalog requests, prefer templates whose title,
description, or inputs imply studio/product photoshoot/catalog. If none appear,
fallback to an image edit model and prompt for a clean ecommerce studio result.

## When To Ask Questions

Always ask for template approval before running unless the user explicitly
delegated choice or asked to auto-run. After the template is approved, ask only
when:

- no product/reference image is available but the template requires one;
- a required select field needs a value and there is no obvious default;
- image roles are ambiguous, such as multiple files where one could be product,
  model, background, or style reference;
- the user requested a commercial constraint that could be violated without
  confirmation, such as exact label preservation or marketplace-specific rules.

After approval, choose sensible defaults for non-critical optional settings and
proceed.

## First Response Shape

For a request like "I want good ad campaign visuals of this product" with an
attached product image, the first user-facing response should look like:

```text
I found a few Nim product-ad templates that fit this:

1. Beverage ad (`beverage-lifestyle`) - image, 20 credits. Lifestyle drink ad; needs the product image.
2. Dynamic shot (`dynamic-ad`) - image, 30 credits. Cinematic hero product shot; needs the product image and optional logo.
3. Retro close-up (`retro-close-up`) - image, 270 credits. Stylized model-led commercial; needs product image, model image, and details.

I recommend Beverage ad for the first pass. Use that one?
```

Do not upload files or start generation before this confirmation unless the user
has explicitly asked to skip selection and run the best option.