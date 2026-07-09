# Universal Prompt Generator Companion

This reference provides generator-agnostic prompt assembly rules for image and video prompts.

## Assembly Order

Use this order when building a master prompt:

1. Style or format
2. Main subject
3. Physical characteristics and concrete details
4. Distinctive traits
5. Action or pose
6. Background, setting, location, time, and weather
7. Camera skill
8. Lighting skills
9. Modifier skills
10. FX skills
11. Color or grade skills
12. Composition and perspective
13. Focus, depth of field, and exposure
14. Materials, wardrobe, and texture
15. Mood and energy
16. Quality markers
17. Constraints and negative prompt

## Selection Rules

- Use one primary camera skill. Add a second camera cue only when it reinforces the same look.
- Use two to four lighting skills. Avoid contradictory lighting such as flat catalog light plus deep noir unless the user asks for a deliberate contrast.
- Use zero to two modifiers. Use one to two FX cues unless the concept clearly needs more.
- Use one to two color or quality skills. Keep them coherent with the camera and lighting.
- Do not overload the prompt with technical filler. Every phrase should change the image or video result.
- Treat brand aesthetics as mood cues, not as instructions to create logos or protected marks.
- For photorealism, reinforce anatomy, material texture, skin, fabric, hair, metal, glass, smoke, fog, and realistic light behavior.

## Output Blocks

Return these blocks when useful:

- Master Prompt: detailed copy-ready English prompt.
- Compact Prompt: short copy-paste-friendly English prompt.
- Negative Prompt: one block of unwanted elements.
- Skill Stack: camera, lighting, modifiers, FX, color/quality.
