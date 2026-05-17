# ⬡ BOUNTY HUNTER
### Trustless Freelance on GenLayer · AI-Judged · Auto-Payout

![GenLayer](https://img.shields.io/badge/GenLayer-Studionet-e8f520?style=for-the-badge&labelColor=0c0c0e)
![Contract](https://img.shields.io/badge/Contract-0xD5D8...5444-20f5d4?style=for-the-badge&labelColor=0c0c0e)
![Status](https://img.shields.io/badge/Status-LIVE-20f550?style=for-the-badge&labelColor=0c0c0e)

**Live App:** https://kmgdz.github.io/bounty-hunter-genlayer  
**Explorer:** https://explorer-studio.genlayer.com/address/0xD5D822016E8db5072d9F4e989BAd11063E565444

---

## What is Bounty Hunter?

A fully trustless bounty platform built on **GenLayer Studionet**.  
Funds are locked in an Intelligent Contract and auto-released **only when the AI Judge** — powered by multi-validator LLM consensus — confirms the submitted work meets the spec.

No escrow agent. No human arbitrator. No trust required.

```
Poster locks GEN → Solver submits URL → AI fetches URL → LLM consensus → Auto-payout
```

---

## Contract

| Field | Value |
|-------|-------|
| **Address** | `0xD5D822016E8db5072d9F4e989BAd11063E565444` |
| **Network** | GenLayer Studionet |
| **RPC** | `https://studio.genlayer.com/api` |
| **Chain ID** | `61999` (0xF21F) |
| **Explorer** | https://explorer-studio.genlayer.com/address/0xD5D822016E8db5072d9F4e989BAd11063E565444 |

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
| `gl.message.sender` | Identity checks (poster cannot solve own bounty) |
| `TreeMap[u256, str]` | On-chain bounty storage as JSON strings |

---

## How judge_submission Works

```python
def fetch_and_judge():
    resp    = gl.nondet.web.get(submission_url)
    content = resp.body.decode("utf-8")[:3000]
    prompt  = f"Judge if this work PASSES the spec: {spec} ... {content}"
    return gl.nondet.exec_prompt(prompt)

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
get_bounty(bounty_id) -> dict
get_open_bounties()   -> list
get_stats()           -> dict
```

---

## Bounty Status Flow

```
open -> submitted -> judging -> paid      (solver wins, GEN auto-sent)
  |                    |------> failed    (poster can reclaim)
  |-----------------------------refunded  (cancel or reclaim_after_fail)
```

---

## Architecture

```
Off-chain (speed)              GenLayer Studionet (truth)
------------------             --------------------------
Vanilla HTML/CSS/JS   -->      bounty_hunter.py
- Browse bounties              - post_bounty()   [payable]
- Post bounties                - submit_solution()
- Submit URLs                  - judge_submission() [AI + web]
- View AI verdicts             - cancel_bounty()
- MetaMask wallet              - reclaim_after_fail()
                               - get_bounty() / get_stats()
```

Centralized for latency. Decentralized for correctness.

---

## Run Locally

```bash
python -m http.server 3000
# open http://localhost:3000
```

---

## Why This Matters

Traditional freelance platforms charge 5-20% fees and require a trusted arbitrator.
Bounty Hunter eliminates that: the AI judge reads the actual submitted URL,
compares it to the spec, and the economic settlement is atomic with the verdict.
All reasoning is committed on-chain and auditable forever.
