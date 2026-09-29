# Recovery Patterns

Use only the patterns relevant to the actual error and inputs. The scenarios below are reported observations, not independently reproduced tests or official explanations of moderation behavior. A successful retry does not establish which token, image feature, service change, or random variation caused the difference.

## Face or character replication language

**Pattern:** a prompt demands an exact face or identical character.

Replace replication commands with “Use the attached image as a visual reference for the character's appearance.” Add only the visible traits needed for continuity, such as hairstyle, clothing, and broad silhouette. Keep the intended character consistent without requesting a perfect duplicate. This wording change does not establish permission or remove a restriction on the reference image itself.

## A generated face is flagged as a real person

**Reported:** a synthetic face was rejected; a participant used a scene and clothing reference without the face, plus a separate character reference sheet, and described the face as a reference.

**Action:** inspect available images and the error first. Separate scene/wardrobe and character roles where supported. Use “Reference A supplies the environment and clothing direction; reference B supplies the character's visual design.” Bind these labels to the model's real reference syntax and upload order. If there is no usable separate sheet, request or prepare one within the authorized task. Do not assert that splitting references guarantees acceptance or that an uninspected face is synthetic.

## A harmless stuffed-bear prompt fails

**Reported:** removing the word `cute` from a plush-bear prompt was followed by a successful generation.

**Action:** remove the nonessential adjective and describe observable features instead: “a small plush bear with brown fabric, round ears, stitched eyes, and a soft woven texture.” Keep action and camera settings unchanged. Do not generalize this observation into a rule that `cute` is prohibited.

## A neutral car prompt fails in English

**Reported:** a faithful Chinese version of a neutral car description succeeded after the English version failed.

**Action:** first rule out schema, reference, and operational errors. If the scene is otherwise harmless and the reason remains unclear, a faithful Chinese translation can be offered as one diagnostic variant. Explain it in the user's language and retain the English version for comparison. Do not switch if the user requires an English-only generation prompt. Preserve vehicle details, shot, motion, no-music constraint, and any explicitly requested dialogue language. Do not translate exact spoken lines unless asked. Never describe Chinese as a guaranteed bypass or make the translation euphemistic.

## An original character resembles a recognizable franchise design

**Reported:** a purportedly original character looked similar to a Disney design; changes to appearance and clothing were followed by a successful generation.

**Action:** propose a genuinely new silhouette, facial proportions, hairstyle, clothing construction, palette, and accessories. Remove distinctive borrowed emblems or combinations. If the reference still depicts the rejected design, revise the reference too. Do not simply rename that design “original.” Explain any material departure from the user's character before submitting it.

## A cosplay costume is rejected even without a face

**Reported:** removing the face did not resolve a costume-related copyright rejection because the outfit remained recognizable.

**Action:** develop an original costume from broad design goals such as theatrical tailoring, layered textiles, or futuristic workwear. Change characteristic silhouette and decoration, not only colors or character names. Keep unrelated scene direction. A faceless image alone does not make a recognizable costume a new design.

## Stage makeup or a prop effect is mistaken for injury

**Reported:** theatrical makeup was interpreted as blood or injury.

**Action:** when accurate, describe intact skin, decorative cosmetic pigment, visible brushwork, and a makeup demonstration. A visibly different cosmetic palette—such as cobalt blue, lavender, or metallic gold—can make the revised artistic design clearer. A palette change is a real visual change, so disclose it.

For a genuine food gag involving ketchup, describe tomato ketchup or sauce accurately, preferably with the food or dispenser visible. Do not relabel actual blood, wounds, or injury as ketchup, makeup, or colored liquid. If the requested scene contains injury, offer an accurate non-graphic revision rather than hiding what it depicts.

## Generated music triggers an audio-copyright rejection

**Reported:** a model added music and the output was rejected; the same scene succeeded with natural sounds only and “no music.”

**Action:** preserve the visual prompt and specify the intended ambience and synchronized effects, followed by “No music, background score, soundtrack, singing, or melodic elements.” Keep requested speech. If a previous audio reference contains music, prompt text alone does not remove that music; use an appropriate replacement or an authorized edit.

If a silent result is acceptable, use the contract's audio-off setting with a visual prompt in English by default, preserving an explicitly requested language. It disables generated effects and speech too; it is not a selective music mute. Never promise that disabling generation removes retained source-video audio.

## A named work triggers a rejection

**Reported:** the title `Black Mirror` appeared in five rejected Seedance 2.5 variants; removing it and describing the team's own scene was followed by success.

**Action:** replace the title with concrete original scene direction: a near-future apartment, a wall display responding to its resident, cool practical lighting, or restrained social tension. Preserve the user's own story rather than reproducing distinctive characters, dialogue, props, or scenes. Do not claim the title is always blocked or repeat five trials as a recommended workflow.

## A magazine contains a real brand and celebrity photo

**Reported:** a branded magazine featuring a celebrity was rejected; a wholly fictional magazine without the celebrity face succeeded.

**Action:** propose an invented publication with original typography, generic editorial text, and original artwork or a clearly fictional illustrated portrait. Remove the real masthead and celebrity image from the actual reference asset as well as the prompt. Do not call an unchanged branded cover fictional. Preserve the magazine's role in the scene and disclose the substitution.
