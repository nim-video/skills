# UGC Prompt Patterns

This reference distills the local example set in `../../UGC prompts example/ugc_prompts_20.txt`. Use the source file when matching a specific example style.

## Shared Style Block

Use a compact version unless the user asks for a long master prompt:

```text
UGC mixed with documentary realism, social media ad, TikTok/Reels/Shorts, authentic creator content, smartphone footage, natural imperfections, unpolished capture, realistic practical lighting, natural color, vertical 9:16.
```

For hyper-real creator footage:

```text
Authentic iPhone footage with natural HDR, realistic skin pores, subtle autofocus breathing, tiny handheld wrist movement, realistic fabric movement, natural blinking and breathing.
```

## Direct-To-Camera Creator Ad

Best for one creator selling a product, tool, offer, or idea.

Reference roles:

```text
@image1 - main location.
@image2 - main character.
```

Shot logic:

- medium shot or medium close-up;
- desk, room, car, sofa, kitchen, or other ordinary location;
- eye contact with lens as if FaceTime;
- small gestures, shrugs, nods, natural blinks and pauses;
- emotional arc: frustration -> relief -> proof -> CTA.

Prompt clause:

```text
The delivery feels conversational, honest and unscripted, not like a commercial. The creator occasionally gestures with one hand, pauses where a real person would, briefly glances away while thinking, then returns to the lens.
```

## Multi-Cut Hook

Best for 6-10 second social hooks with a VO line split across cuts.

Structure:

```text
VO: "<exact line>"

0:00-0:02 - Medium shot, direct-to-camera...
HARD CUT.
0:02-0:05 - Medium close-up...
HARD CUT.
0:05-0:08 - Close-up or slight diagonal angle...
```

Rules:

- each cut should change scale or angle for story rhythm;
- do not change identity, location, wardrobe, or lighting unless stated;
- every cut must match the same spoken line timing;
- `HARD CUT` only, no morphs or hidden transitions.

## Selfie Walkthrough

Best for stores, restaurants, venues, travel, or event arrivals.

Structure:

```text
0:00-0:05 - Front-camera selfie while walking toward the entrance/location.
HARD CUT.
0:05-0:10 - Rear-camera POV showing what the creator sees, preserving the exact location reference.
```

Checks:

- storefront/signage/door/interior match the reference exactly when provided;
- path through the doorway is physically possible;
- camera hand and free hand are plausible;
- exposure adapts naturally between exterior and interior.

## Mirror Try-On

Best for fashion, outfit checks, fitting rooms, vintage stores, beauty and styling.

Required locks:

- face/hair/makeup from identity reference;
- outfit/body proportions from outfit reference;
- boutique/room layout from location reference;
- mirror reflection geometry remains consistent.

Useful actions:

- walks toward mirror;
- lowers phone slightly;
- checks fit from side to side;
- smooths fabric;
- adjusts hem, bag, jewelry, or hair;
- says one short natural line.

## Static Tripod Try-On Or Performance

Best for outfit changes, musical performance, demonstrations, or repeated comparisons.

Rules:

- camera is completely locked off;
- framing, lens, exposure, tripod position, and background remain identical;
- every transition is a hard cut;
- no zoom, pan, shake, reframing, or hidden edit;
- subject scale remains stable across cuts.

Use for outfit sequences:

```text
After every hard cut, the camera stays in the exact same position and the background remains perfectly unchanged. Outfit changes happen only through HARD CUTS.
```

## Street Interview

Best for spontaneous comedy, social proof, dating, vox-pop, or public reaction clips.

Ingredients:

- handheld iPhone by a friend/interviewer;
- interviewer may be partly off-camera or visible;
- reactions overlap naturally;
- people laugh, interrupt, and shift posture;
- framing is imperfect but readable.

Quality cue:

```text
The interaction feels spontaneous and unscripted, with real timing, small awkward pauses, overlapping laughter, and handheld framing from a friend filming nearby.
```

## Concert/Event Selfie

Best for live music, sports, nightlife, or crowded event reactions.

Important details:

- dense crowd around the creator, not an isolated VIP bubble;
- stage/crowd/live performer visible when relevant;
- changing exposure from lights, haze, phones, screens;
- live audio/crowd ambience only when supported;
- hair and clothing react to jumping or movement.

Use caution with lyrics or named songs if the user did not provide rights/clearance.

## Audio And Lip Sync

Use exact audio reference wording:

```text
@audio1 - use the voice, tone, cadence, pronunciation, pacing and vocal texture exactly.
Perfect lip sync. The spoken line is clearly synchronized with the mouth movement.
```

If the model does not support audio or lip sync fields, keep the line in the prompt but note that Nim contract support must be checked before generation.

## Negative Block

Use or adapt:

```text
No subtitles unless requested. No text overlays. No beauty filter. No skin smoothing. No CGI. No morphing. No hidden edits. No transition effects. No flickering. No ghosting. No duplicate faces. No warped hands. No fake readable text. No unsupported logos.
```

Add mode-specific negatives:

- static tripod: no camera shake, no zoom, no panning, no reframing;
- mirror: no impossible reflection, no duplicated phone, no broken mirror geometry;
- product/outfit: no redesign, no color drift, no material change, no logo drift;
- location: no layout changes, no invented signage, no background morphing.
