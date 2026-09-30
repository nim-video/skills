# Price a motion-transfer run

Before spending, record the exact model/input mode, provider when exposed, output
duration, resolution, aspect ratio, audio setting, variant count, and each uploaded
video reference's actual duration and dimensions (including padding). Read the live
model estimate and balance. Prefer an authoritative full-input quote when a callable
tool exposes one. Do not invent a quote endpoint or submit a paid job to discover price.

## What can actually be calculated

- `perSecond`: output base = returned unit rate times output seconds. Check the returned
  estimate's duration and resolution match the requested values.
- `total`: use the returned total for those exact settings; do not multiply by seconds.
- `perMediaLength` or `unknown`: use the returned estimate only for its stated settings.
  Do not infer a linear rate or a rounding rule without documented pricing metadata.
- Add reference/input charges and rounding ONLY when the service supplies their rules.
  A reference count alone does not describe duration-based input charges.
- Split runs: sum the full price of every submitted fragment at its actual billed
  output duration, not the final trimmed duration. Variants multiply the corresponding
  per-job price. Include already accepted jobs separately as spent/committed cost.
- Keep depth-provider currency and Nim credits separate. Cached depth costs zero new
  depth calls. Verify the provider rate before a new depth calculation; do not add
  dollars numerically to credits.

If reference charges are not exposed, label the catalog amount **output base only**,
not a confirmed total. Use a previous service-reported job estimate as an empirical
planning estimate only for the same model, settings and references, with its date and
uncertainty. It is not a general pricing formula or a guaranteed maximum.

The catalog base leaves out reference charges, and their billing formula is not exposed.
Example: Seedance 2 Advanced Mode, 720p, 10-second output, one depth reference video and
two image references, generated audio off: catalog base 300 credits; running-job
`estimatedCreditCost` 400 credits. Do not assume the difference is a fixed fee or infer a
per-second rate from one example.

## Budget and disclosure

Calculate requested jobs, output base, reference charges, full estimate and remaining
balance internally. Present only settings and the approximate full cost in the single
confirmation specified in SKILL.md. Show separately billed processing currency without
explaining the depth step. Provide a breakdown only when asked or needed for a budget decision.
For heterogeneous jobs sum their prices individually. Do not call an estimated
remaining balance guaranteed. With a hard user budget, require a full quote or a
documented upper bound that fits before submission. Never compare an incomplete base
price to a hard cap and declare the job affordable.

Without a hard cap, an authorized generation can proceed after disclosing uncertainty
if a reasonable full-cost estimate and balance support it. If neither a full quote
nor a comparable prior estimate exists, ask for a spending decision rather than
silently assuming zero reference cost. A rejected or failed submission is not evidence
of zero charge; do not promise refunds or retry automatically.

After acceptance, record each `estimatedCreditCost` from submission/status (null means
unknown). Reconcile the estimate and check balance if actual spending is requested;
a job estimate is not a final invoice, and concurrent account activity can affect
balance differences. Report material changes before starting any remaining jobs.
