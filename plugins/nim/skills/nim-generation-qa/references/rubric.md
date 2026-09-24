# Eight quality criteria

Judge against the intended aesthetic, not universal photorealism. Pass only properties supported by actual inspection.

| Criterion | Checks | Evidence and caveats |
|---|---|---|
| Character and clothing / Персонаж и одежда | Face, build, apparent age, hairstyle, facial hair, clothing and accessories; persistence across shots. | Compare correct reference roles across visible views. Occluded features are unknown. |
| Location / Локация | Photographic credibility when requested; stable geometry, scale, materials, layout and landmarks. | Track landmarks during movement and cuts. Different perspectives need not be different rooms. |
| Camera physics / Физика камеры | Plausible operator/mount, height, trajectory, acceleration, settling, parallax, selfie/mirror logic. | Temporal evidence required. Motivated handheld shake or whip-pan blur is not a defect by itself. |
| Human movement / Движения людей | Anatomy, joints, weight, balance, gestures, pace; rubber deformation, jerks, theatricality. | Inspect starts/stops and occlusion across time. Performance must match the brief; a still cannot prove smoothness. |
| Interactions / Взаимодействия | Hand/object grips, contact, support, scale, trajectories, reaction forces, animals, fluids, occlusion. | Check cause → contact → force → response → settling. Static images support spatial plausibility, not dynamic validity. |
| Lighting and texture / Свет и фактура | Light direction, shadows, reflections, exposure/color consistency, skin/fur/fabric/glass, compositing and CGI gloss. | Metallic fabric may properly shine. Compare target materials; do not mistake motion blur for melting. |
| Timing and continuity / Тайминг и непрерывность | Required beats/order/duration, dialogue windows, state changes, props, caps, fill, labels, outfits, positions and causality. | Compare actual timeline and checklist. A deliberate time jump differs from an unexplained reset. Keep exact vs approximate timing distinct. |
| Sound and speech / Звук и речь | Requested presence/absence, exact words, pronunciation, voice, delivery, room acoustics, event sync, lip sync, unwanted sounds/music. | Listening or capable audiovisual analysis required. ASR supports words, metadata supports streams only. Requested silence must be verified; still-image sound is N/A. |

## Findings

Issue types:
- brief_prompt_gap: approved requirement omitted/contradicted by submitted prompt.
- adherence: output violates an explicit requirement.
- artifact: synthesis defect supported by visual/audio evidence.
- technical: actual delivery fails an established technical requirement.
- coverage_gap: cannot evaluate; not a generated defect.
- preference: optional refinement, not an objective failure.

Severity:
- critical: unusable for the stated purpose, such as wrong required identity or missing essential content.
- major: materially harms continuity, believability, branding or a required action.
- minor: localized imperfection without meaningful loss of intent.

Confidence: high / medium / low. Low-confidence suspicions need more evidence or an uncertainty label, not a confident failure. Avoid fabricated scores or percentages.

## Sampling

Cover every shot and transitions; adapt sampling density to motion and clip length. Inspect handoffs, contact, drinking, label turns, dialogue endings and final frames closely. No fixed sampling rate proves the absence of artifacts. Label approximate timecodes and record the actual reviewed source/version.

Separate identity, outfit, prop and environment references. A portrait background need not be reproduced if it was only an identity reference. Identify contradictory references rather than silently resolving conflicts.
