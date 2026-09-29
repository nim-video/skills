# Prompt Examples

These examples are starting points, not known passing prompts. Substitute the user's scene and supported reference syntax. Preserve requested dialogue; the examples omit dialogue because none is required by their scenes. Audio-on and audio-off examples are alternatives, not settings to combine.

## Character reference with rain and footsteps

```text
Use the attached character sheet as a visual reference for the character's appearance, hairstyle, and wardrobe. Keep the character visually consistent throughout the shot. The character walks along a rain-soaked sidewalk and pauses beneath an awning. A steady medium tracking shot follows at walking speed. Cool shop-window light reflects softly on the pavement.

Audio: soft footsteps synchronized with each step, light rain pattering on the awning, and quiet distant road noise. Natural scene sounds only. No music, background score, soundtrack, singing, or melodic elements. No dialogue.
```

If scene and character references are separate, map their real input roles first; do not submit the words “reference A” as an asset identifier.

## Neutral car scene

```text
A silver compact sedan drives at a steady speed along a quiet city street at dusk. A low side-tracking camera keeps the whole vehicle in frame. The car slows smoothly and stops beside the curb. Soft street lighting reflects across the body panels.

Audio: a subdued engine tone that falls as the car slows, gentle tire noise on asphalt, and a brief turn-signal click while pulling over. Natural scene sounds only. No music, background score, soundtrack, singing, or melodic elements. No dialogue.
```

For an optional translation comparison, translate this same scene faithfully; do not change the car, movement, sound instructions, or declared spoken language.

## Plush bear without an evaluative adjective

```text
A small plush bear with brown woven fabric, round ears, and stitched eyes sits on a wooden chair. The bear raises one soft paw, then settles back into its seated pose. A locked medium shot, warm window light, and shallow depth of field reveal the fabric texture.

Audio: a faint fabric rustle during the paw movement and quiet indoor room tone. Natural scene sounds only. No music, background score, soundtrack, singing, or melodic elements. No dialogue.
```

## Original theatrical costume

```text
An original theatrical performer wears an asymmetric ivory jacket, a pleated indigo collar, copper geometric fasteners, and tapered charcoal trousers. The performer turns slowly beneath a warm stage light, showing the layered fabric and independently designed silhouette. A steady full-body shot with a gentle camera push-in.

Audio: a soft footstep at the turn, a light cloth rustle, and quiet stage room tone. Natural scene sounds only. No music, background score, soundtrack, singing, or melodic elements. No dialogue.
```

Use a matching original reference; this text does not alter a recognizable costume still attached to the request.

## Decorative stage makeup

```text
An adult performer demonstrates decorative theatrical makeup on intact skin. A makeup brush adds a smooth cobalt-blue geometric stripe beside the cheekbone, with metallic-gold accents and clearly visible cosmetic brushwork. A close-up at eye level, soft studio lighting, and one slow brush movement. This is a cosmetic design demonstration with no wound or injury.

Audio: a faint brush sweep and quiet studio room tone. Natural scene sounds only. No music, background score, soundtrack, singing, or melodic elements. No dialogue.
```

Use only for an actual makeup design. The altered color is an explicit artistic revision.

## Original near-future scene without a work title

```text
In a quiet near-future apartment, an adult resident sets a cup on a table. A wall display lights up with a simple geometric pattern, then goes dark as the resident looks toward it. A restrained medium-wide shot, a gradual camera push-in, cool practical light, and understated tension. Use an original setting and visual design.

Audio: the cup touching the table, a faint ventilation hum, and the resident's sleeve moving. Natural scene sounds only. No music, background score, soundtrack, singing, or melodic elements. No dialogue.
```

## Fictional publication

```text
An adult reader opens a wholly fictional design magazine with an invented masthead and an original abstract landscape illustration on the cover. The publication has its own typography and layout, with no real-brand logo or celebrity image. A close-up follows one page turning beneath soft afternoon window light.

Audio: paper flexing, one crisp page turn, and quiet room ambience. Natural scene sounds only. No music, background score, soundtrack, singing, or melodic elements. No dialogue.
```

## Silent fallback

Keep the user's visual scene, using English by default or an explicitly requested language. Remove contradictory sound directions and append this instruction (translated if needed):

```text
Silent video. No generated audio, music, dialogue, ambience, or sound effects.
```

Apply the live contract's supported audio-off value if one exists. For example, a string enum might require `generate_audio: "off"`, while a boolean field might require `generateAudio: false`. Neither spelling is universal. If the mode has no audio control, report that limitation; a prompt-only request does not verify silence.
