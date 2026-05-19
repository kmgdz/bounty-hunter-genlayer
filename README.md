# ⬡ Bounty Hunter

**Trustless AI-judged freelance platform built on GenLayer Studionet.**

Posters lock GEN in escrow. Solvers submit a URL as proof of work. The AI Judge fetches the URL live, verdicts against the spec via LLM consensus, and auto-releases funds on PASS — with no middleman, no arbitrator, no trust required.

---

## Links

| | |
|--|--|
| **Live App** | https://bounty-hunter-genlayer.vercel.app |
| **Contract** | `0xD5D822016E8db5072d9F4e989BAd11063E565444` |
| **Explorer** | https://explorer-studio.genlayer.com/address/0xD5D822016E8db5072d9F4e989BAd11063E565444 |
| **Network** | GenLayer Studionet |
| **RPC** | `https://studio.genlayer.com/api` |
| **Chain ID** | `61999` (`0xf22f`) |

---

## How It Works

```
Poster locks GEN
      ↓
Solver submits URL
      ↓
AI fetches URL (gl.nondet.web.get)
      ↓
LLM judges content vs spec (gl.nondet.exec_prompt)
      ↓
Multi-validator consensus (gl.eq_principle.prompt_comparative)
      ↓
PASS → GEN auto-transfers to solver
FAIL → Poster reclaims funds
```

---

## GenLayer Primitives Used

| Primitive | Where | Purpose |
|-----------|-------|---------|
| `@gl.public.write.payable` | `post_bounty` | Accept GEN escrow from poster |
| `gl.message.value` | `post_bounty` | Read the escrowed amount |
| `gl.message.sender` | All write methods | Identity checks |
| `gl.nondet.web.get(url)` | `judge_submission` | AI fetches solver's submitted URL live |
| `gl.nondet.exec_prompt(prompt)` | `judge_submission` | LLM judges fetched content against spec |
| `gl.eq_principle.prompt_comparative` | `judge_submission` | Multi-validator consensus on verdict |
| `emit_transfer(value=reward_wei)` | `judge_submission` | Trustless auto-payout to solver on PASS |
| `TreeMap[u256, str]` | Contract storage | All bounty state as JSON strings on-chain |

---

## Contract Methods

```python
# ── Write ──────────────────────────────────────────────────────────────
post_bounty(title: str, spec: str, deadline: u256) -> u256
# @payable — locks GEN in escrow, returns bounty_id

submit_solution(bounty_id: u256, sub_url: str) -> None
# Solver submits a public URL as proof of work

judge_submission(bounty_id: u256) -> None
# Anyone triggers the AI judge:
#   1. Fetches sub_url via gl.nondet.web.get
#   2. LLM verdicts content vs spec via gl.nondet.exec_prompt
#   3. Consensus via gl.eq_principle.prompt_comparative
#   4. PASS → emit_transfer to solver | FAIL → poster can reclaim

cancel_bounty(bounty_id: u256) -> None
# Poster cancels open bounty (no submissions yet), reclaims GEN

reclaim_after_fail(bounty_id: u256) -> None
# Poster reclaims GEN after a FAIL verdict

# ── View ───────────────────────────────────────────────────────────────
get_bounty(bounty_id: u256) -> dict
get_open_bounties() -> list
get_stats() -> dict  # {total_created, total_paid_wei, next_id}
```

---

## Bounty State Machine

```
         post_bounty()
open ──────────────────► submitted ──► judging ──► paid      ✓ solver wins
 │     submit_solution()                  │
 │                                        └──────► failed    ✗ poster reclaims
 └─────────────────────────────────────────────► refunded    cancel / reclaim
```

---

## The AI Judge (core logic)

```python
def fetch_and_judge():
    # Step 1: AI fetches the solver's submitted URL live
    resp    = gl.nondet.web.get(url)
    content = resp.body.decode("utf-8", errors="replace")[:3000]

    # Step 2: LLM judges fetched content against the bounty spec
    prompt = f"""You are an impartial judge for a trustless bounty platform.
Decide if the submitted work PASSES or FAILS the spec.

SPEC: {spec}
FETCHED CONTENT: {content}

Return ONLY JSON:
{{"verdict": "pass"|"fail", "reasoning": "<one sentence>"}}"""

    return gl.nondet.exec_prompt(prompt)

# Step 3: Multi-validator consensus
# Both leader and validator independently fetch + judge.
# Funds only move if they agree on the verdict.
raw = gl.eq_principle.prompt_comparative(
    fetch_and_judge,
    'The "verdict" field must be the same in both responses'
)
```

---

## Architecture

```
Off-chain (speed)                 GenLayer Studionet (truth)
─────────────────                 ──────────────────────────
Vanilla HTML + CSS + JS   ──►     bounty_hunter.py
  Connect wallet                    post_bounty()    ← @payable, locks GEN
  Post bounties                     submit_solution()
  Submit URLs                       judge_submission() ← AI + web fetch
  View verdicts                     cancel_bounty()
  TX links → explorer               reclaim_after_fail()
                                    get_bounty() / get_stats()
                                           │
                                    On-chain forever:
                                    verdict + AI reasoning
                                    escrow & payout history
```

**Centralized for latency. Decentralized for correctness.**

The only decision that goes on-chain is the one that cannot be faked: did this work actually meet the spec? Everything else (wallet UI, form inputs) is off-chain for speed.

---

## Why This Matters

Traditional freelance platforms (Upwork, Fiverr) charge 5–20% and require trusting a centralized arbitrator. Bounty Hunter removes that trust requirement entirely:

- The AI judge reads the **actual URL** the solver submitted
- Judgment happens via **multi-validator LLM consensus** — no single node can corrupt it
- Payment is **atomic with the verdict** — no manual release needed
- All verdicts and reasoning are **committed on-chain** and auditable forever

---

## Stack

- **Contract:** Python · GenLayer SDK · Studionet
- **Frontend:** Vanilla HTML + CSS + JS · Zero dependencies · Zero build step
- **Proxy:** Vercel serverless function (`api/rpc.js`) for RPC relay
- **Wallet:** MetaMask via `window.ethereum`

---

## Run Locally

```bash
git clone https://github.com/kmgdz/bounty-hunter-genlayer
cd bounty-hunter-genlayer
python -m http.server 3000
# Open http://localhost:3000
```

Add GenLayer Studionet to MetaMask:
- RPC: `https://studio.genlayer.com/api`
- Chain ID: `61999`
- Symbol: `GEN`
