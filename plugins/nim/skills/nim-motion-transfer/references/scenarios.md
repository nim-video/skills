# Scenarios and activation from user intent

Examples illustrate meaning regardless of the user's language; they are not keyword
lists. Conditions combine: "same dance, but my mascot, on a night street" means one
source performance, one identity swap, and one environment change.

## Intent map

| No. | The user wants | Mode and decision |
|---|---|---|
| 1 | "Make my character do this dance" + a clip | Full flow. Depth reference, then reference-to-video |
| 2 | "Transfer this motion to my character" | Same as 1; "transfer" and "recast" are the same job here |
| 3 | "Same moves, different person" | Same as 1 |
| 4 | "Put my character in this video" | Ambiguous. Ask whether the whole scene is being rebuilt or only the performer replaced. A whole-scene rebuild is this skill; replacing one element in place is an edit, not this |
| 5 | "The original character kept showing up in my output" | The raw clip was used as the motion reference. Build the depth reference and explain why |
| 6 | "Just use the original video as the reference, it's simpler" | Explain what the raw clip carries, then build the depth reference. Do not silently comply |
| 7 | "Only a prompt / do not generate" | Prepare the prompt and the depth plan as text. Start no paid work |
| 8 | "How would this work?" | Explain the depth step and the role split. No generation |
| 9 | "Now do it with the second character" | Reuse the existing depth clip. Change only the identity input |
| 10 | "Same dance, different outfit" | Reuse the depth clip. Change only the wardrobe descriptors |
| 11 | "Do it in Spanish / Japanese / French" | Reuse the depth clip. State the language with an accent and a delivery, not just a country. Only meaningful if the source has lip-sync motion |
| 12 | "Give me three options" | Three separate generations with the same references and different prompts, or a supported `batchSize` when the contract allows it. Batching repeats one prompt; it does not create three different characters |
| 13 | "This is from an anime / a 3D render / a game" | The depth step is optional. Animated and CGI sources carry no real likeness, so the raw clip is often usable directly. Offer both and say which is cheaper |
| 14 | "There are two people in the clip" | Map by position or distinguishing feature. Reference count must equal distinct people. Expect 2-4 regeneration cycles and verify on a contact sheet |
| 15 | "The clip has several shots / jump cuts" | Read [Multi-shot sources](#multi-shot-sources) before spending. Splitting is a choice with a price, not a rule |
| 15b | A source clip longer than 15 seconds | Not a blocker. Split into 4-15 s parts at scene cuts, generate each with Seedance 2, stitch, restore the original sound once, deliver one final file. Warn about the total cost of all parts before starting. See [long-videos.md](long-videos.md) |
| 16 | "Make it longer than the clip" | Refuse the extra length as motion transfer. The tail is invented. Offer either a shorter clip or a separate continuation task on its own contract |
| 17 | "Use a clip I found online" | Use the supplied clip as task input; do not ask routine ownership questions. Do not claim that upload proves rights or that moderation verifies them |
| 18 | "The clip has music / someone talking" | State whether the source audio is wanted. Recasting lip-sync needs the source's phrasing timing, which the clip already carries |
| 19 | "Make the character hold a sword / kick a ball" | Assess contact reliability internally and state contact explicitly in the prompt. Mention only a material feasibility issue briefly |
| 20 | "Make the face more expressive" | Expression is not carried by a depth reference. Offer an animated or CGI source, or a separate performance task |
| 21 | "Keep the original background" | This skill rebuilds the scene. Preserving the source background exactly is an edit, not a motion transfer. Say so rather than promising it |
| 22 | "Now upscale / add sound / publish it" | Separate operations with their own skills and contracts. Do not fold them into this task |
| 23 | "Save the result / the depth map" | Save what is actually available and say where. Do not promise cross-session history or a gallery |
| 24 | Nim MCP is unavailable | Prepare the prompt and depth plan as text; explain that a connected Nim service is required. Do not silently switch services |

## Multi-shot sources

A single generation is one submitted job and one output file; it is not necessarily
one continuous camera take. It can contain scene cuts. Exact cut timing and continuity
are generation quality targets, not guarantees. Inspect them in the output.

Honor an explicit request for one pass: pass the full depth reference to one job when
it fits the live contract. Do not split merely because the source contains cuts.
For a short source that fits, prefer one job unless the user requests separate shots.
If the full source exceeds 15 s, split it into parts as described in
[long-videos.md](long-videos.md) and state the part count and total cost in the single
confirmation; do not ask the user to trim it.

For one-pass work, include source cut timestamps and a short shot order when useful.
Preserve motion timing and keep identity, object appearance and location consistent
across cuts. Do not turn "one pass" into an instruction for a single unbroken take.

Splitting can help isolate a failed shot or reconstruct exact editorial timing, but
multiplies minimum-duration charges and risks appearance drift. It needs a deliberate
choice before submission. Measure EACH shot's duration, not an average: cuts need not
be evenly spaced and N cuts usually divide a clip into N+1 shots.

A shot shorter than the output minimum is not automatically impossible: a supported
padding-and-trimming approach can preserve its useful interval, but the full generated
minimum is billed. Do not introduce that workaround by default or claim the discarded
frames are free. Ask about an alternative only when the user's chosen approach cannot
meet the contract; previously specified choices remain valid.

If splitting is authorized, keep one shared identity reference, verbatim environment
description, fixed casting order and original timeline. Concatenate trimmed picture
fragments, then attach one continuous original soundtrack using
[final-audio.md](final-audio.md). Do not concatenate generated audio beds.

### What must be announced before submitting

State the shot count, the per-fragment duration, the number of generations, N x price,
and which option is proposed. Then wait or proceed according to the budget rules in
[nim-workflow.md](nim-workflow.md). Launching five paid generations and explaining
afterwards is a process failure even when the output is good.

## When a source clip is usable

Vet before spending anything. A source that cannot produce a usable reference should be
reported, not generated from.

| Condition | Reads well | Triggers a report |
|---|---|---|
| Shots | One continuous take | Jump cuts, dissolves, montage |
| Subject | One clearly separated performer | Overlapping people, subject leaving frame |
| Motion | Readable body movement, deliberate pacing | Motion blur, darkness, accidental shake |
| Camera | One deliberate move, or a locked frame | Several competing moves |
| Length | Roughly 3-8 seconds of usable motion per job | Past 15 seconds: split into parts ([long-videos.md](long-videos.md)); this is not a reason to refuse |
| Framing | Full body or consistent head-to-toe | Subject cropped differently across the clip |
| Contact | Self-contained motion | Motion that depends on a prop or another person |

These thresholds are rules of thumb, not Nim contract values. Verify what the live contract accepts; report the specific failure rather than
"the clip did not work".

## Depth reference or raw clip

| Source | Depth reference | Raw clip |
|---|---|---|
| Real human performer | Required. The raw clip carries the original face and wardrobe, which is the most common cause of appearance bleed | Only for camera-motion-only jobs |
| Anime, CGI, 3D render | Optional, and it costs money for nothing | Preferred. No real likeness to leak |
| Source already abstracted | Skip it | Use directly |
| Client wants the original background preserved | Wrong tool entirely; that is an edit | Not applicable |

Choosing depth is about giving the model fewer decisions, not about avoiding review.
State it that way rather than framing it as a compliance trick.

## What a depth reference cannot carry

Assess these limits internally. Mention only a material feasibility issue briefly, without explaining preprocessing unless asked:

- finger detail and hand dexterity
- facial expression and micro-performance
- cloth simulation and fabric behaviour beyond silhouette
- human-object interaction such as holding, throwing, or striking something

Depth keeps silhouette, height, screen position, body mass, timing, and camera movement.
That list is what makes it accurate at choreography and useless at close-up performance.

## Continuation

Keep in context: the source clip path or URL, the depth clip path, the role map, the
chosen model, the aspect ratio and duration, and every job identifier. Then "same dance,
another character" and "make the second one again" continue the correct work without
rebuilding the depth map.

If the depth clip is gone, rebuild it from the source; do not substitute the raw clip to
save a step, because that reintroduces the exact failure the depth step exists to prevent.
