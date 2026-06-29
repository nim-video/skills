---
name: nim-credits
description: >-
  Check Nim credit balance, explain insufficient-credit generation failures, and
  help the user buy or upgrade Nim credits through the Nim MCP. Use when the user
  asks about credits, balance, pricing packs, buying more credits, upgrading, or
  when generate_image, generate_video, or run_template returns
  status="insufficient_credits".
---

# Nim Credits

Handle Nim credit balance and purchase flows. Do not start or retry expensive
generation while the user is out of credits.

## When To Use

- The user asks how many Nim credits they have.
- The user asks to buy credits, see packs, upgrade, or manage their plan.
- A Nim generation/template tool returns `status: "insufficient_credits"`.
- Before a deliberately expensive run, such as high resolution, long video, or
  multiple variations, when the active generation skill asks you to check first.

## Workflow

1. **Check balance.** Call `get_credit_balance` and summarize the current
   effective balance. Mention subscription, pack, grant, or creator-program
   credits only when the tool returns them.
2. **Handle insufficient credits.**
   - If the failed generation/template response already includes purchase
     options, present those options briefly.
   - If options are missing or the user asks what they can buy, call
     `purchase_credits` without `pack` to list available packs and the
     subscription/upgrade link.
3. **Checkout only after choice.** If the user chooses a pack, call
   `purchase_credits` with that exact `pack` value and give them the returned
   checkout link.
4. **Resume generation only after the user says credits are resolved.** Do not
   retry automatically while the balance is still insufficient.

## UX Rules

- Keep the answer practical: current balance, available action, relevant link.
- Do not invent prices, pack sizes, or checkout URLs. Use only tool output.
- Free-plan users may need to upgrade before packs are available; follow the
  `purchase_credits` response.
- Reply in the user's language.
