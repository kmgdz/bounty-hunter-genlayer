# ⬡ BOUNTY HUNTER
### Trustless Freelance on GenLayer · AI-Judged · Auto-Payout

<div align="center">

![GenLayer](https://img.shields.io/badge/GenLayer-Bradbury_Testnet-e8f520?style=for-the-badge&labelColor=0c0c0e)
![Contract](https://img.shields.io/badge/Contract-0xD9d8...F4B9-20f5d4?style=for-the-badge&labelColor=0c0c0e)
![Status](https://img.shields.io/badge/Status-LIVE-20f550?style=for-the-badge&labelColor=0c0c0e)

**[→ Live App](https://bounty-hunter-gen.vercel.app)** · **[→ Explorer](https://explorer-bradbury.genlayer.com/address/0xD9d8fFec51956B4C96C1D1D7c072B0eb0E14F4B9)**

</div>

---

## What is Bounty Hunter?

A fully trustless bounty platform built on GenLayer's Bradbury Testnet.  
Funds are locked in an Intelligent Contract and auto-released **only when the AI Judge** — powered by multi-validator LLM consensus — confirms the submitted work meets the spec.

No escrow agent. No human arbitrator. No trust required.

```
Poster locks GEN → Solver submits URL → AI fetches URL → LLM consensus → Auto-payout
```

---

## GenLayer Primitives Used

| Primitive | Purpose |
|-----------|---------|
| `@gl.public.write.payable` | Lock GEN escrow when poster creates bounty |
| `gl.message.value` | Read escrowed GEN amount |
| `gl.nondet.web.get(url)` | AI fetches the solver's submitted URL live |
| `gl.nondet.exec_prompt(prompt)` | LLM judges fetched content against spec |
| `gl.eq_principle.prompt_comparative(fn, criteria)` | Multi-validator consensus on verdict |
| `emit_transfer(value=reward_wei)` | Trustless auto-payout to solver on PASS |
| `gl.message.sender` | Identity checks (poster ≠ solver) |
| `TreeMap` | On-chain bounty storage and poster index |

---

## Architecture

```
Off-chain (speed)                    GenLayer Contract (truth)
─────────────────                    ─────────────────────────
Vanilla HTML/CSS/JS            ──►   bounty_hunter.py
  • Browse open bounties              • post_bounty() [payable]
  • Post bounties                     • submit_solution()
  • Submit URLs                       • judge_submission() [AI + web]
  • View verdicts & reasoning         • cancel_bounty()
  • MetaMask wallet connect           • reclaim_after_fail()
                                      • get_bounty() / get_stats()
                                           │
                                      On-chain forever:
                                      • Verdict + AI reasoning
                                      • Escrow & payout history
                                      • Solver win counts
```

**Centralized for latency → Decentralized for correctness.**

---

## How `judge_submission` Works

```python
def fetch_and_judge():
    resp    = gl.nondet.web.get(submission_url)          # AI fetches live URL
    content = resp.body.decode("utf-8")[:3000]

    prompt = f"""Judge if this work PASSES the spec:
SPEC: {spec}
FETCHED CONTENT: {content}
Return JSON: {{"verdict": "pass"|"fail", "reasoning": "..."}}"""

    result = gl.nondet.exec_prompt(prompt)
    return result

# Multi-validator consensus: both leader and validator run independently.
# Funds only move if they agree on the verdict.
raw = gl.eq_principle.prompt_comparative(
    fetch_and_judge,
    'The "verdict" field must be the same in both responses'
)
```

---

## Contract Methods

```python
# Write
post_bounty(title, spec, deadline)    # @payable — locks GEN
submit_solution(bounty_id, sub_url)   # solver submits URL
judge_submission(bounty_id)           # triggers AI judge (anyone)
cancel_bounty(bounty_id)              # poster cancels open bounty
reclaim_after_fail(bounty_id)         # poster reclaims after FAIL

# View
get_bounty(bounty_id) → dict
get_open_bounties() → list
get_poster_bounties(poster) → list
get_stats() → dict
```

---

## Bounty Status Flow

```
open ──► submitted ──► judging ──► paid      ← solver wins, GEN auto-sent
  │                       └──────► failed    ← poster can reclaim
  └──────────────────────────────► refunded  ← cancel or reclaim
```

---

## Tech Stack

- **Contract:** Python · GenLayer SDK · Bradbury Testnet
- **Frontend:** Vanilla HTML + CSS + JS · Zero dependencies · Zero build step
- **Wallet:** MetaMask via `window.ethereum`
- **Design:** Industrial crypto-noir · Bebas Neue + Space Mono

---

## Deploy Locally

```bash
# No build step needed — just open the file
open index.html

# Or serve it
npx serve .
```

---

## Why This Matters

Traditional freelance platforms charge 5–20% fees and require trusting a centralized arbitrator. Bounty Hunter shows the GenLayer pattern for removing that trust:

> The judgment is done by LLM validators reading the actual deliverable URL.  
> The economic settlement is **atomic with the verdict**.  
> All reasoning is committed on-chain and auditable forever.
