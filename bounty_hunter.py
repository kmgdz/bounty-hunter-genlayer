# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *
import json


@gl.evm.contract_interface
class _Recipient:
    class View:
        pass
    class Write:
        pass


class BountyHunter(gl.Contract):

    next_id:        u256
    total_created:  u256
    total_paid_wei: u256
    bounties:       TreeMap[u256, str]   # bounty_id -> JSON string

    def __init__(self) -> None:
        self.next_id        = u256(0)
        self.total_created  = u256(0)
        self.total_paid_wei = u256(0)
        self.bounties       = TreeMap()

    def _load(self, bounty_id: u256) -> dict:
        return json.loads(self.bounties[bounty_id])

    def _save(self, bounty_id: u256, b: dict) -> None:
        self.bounties[bounty_id] = json.dumps(b)

    # ── post_bounty ───────────────────────────────────────────
    @gl.public.write.payable
    def post_bounty(self, title: str, spec: str, deadline: u256) -> u256:
        reward = gl.message.value
        if reward == u256(0):
            raise Exception("Must send GEN as the bounty reward")
        if len(title.strip()) == 0:
            raise Exception("Title cannot be empty")
        if len(spec.strip()) < 20:
            raise Exception("Spec must be at least 20 characters")

        bid    = self.next_id
        poster = str(gl.message.sender)

        self._save(bid, {
            "bounty_id":  int(bid),
            "poster":     poster,
            "title":      title,
            "spec":       spec,
            "reward_wei": int(reward),
            "deadline":   int(deadline),
            "status":     "open",
            "solver":     "",
            "sub_url":    "",
            "verdict":    "",
            "reasoning":  "",
        })

        self.next_id       = self.next_id + u256(1)
        self.total_created = self.total_created + u256(1)
        return bid

    # ── submit_solution ───────────────────────────────────────
    @gl.public.write
    def submit_solution(self, bounty_id: u256, sub_url: str) -> None:
        if bounty_id not in self.bounties:
            raise Exception("Bounty not found")
        b = self._load(bounty_id)
        if b["status"] != "open":
            raise Exception("Bounty is not open")
        if str(gl.message.sender) == b["poster"]:
            raise Exception("Poster cannot solve own bounty")
        if not (sub_url.startswith("http://") or sub_url.startswith("https://")):
            raise Exception("URL must start with http:// or https://")

        b["solver"]  = str(gl.message.sender)
        b["sub_url"] = sub_url
        b["status"]  = "submitted"
        self._save(bounty_id, b)

    # ── judge_submission ──────────────────────────────────────
    @gl.public.write
    def judge_submission(self, bounty_id: u256) -> None:
        if bounty_id not in self.bounties:
            raise Exception("Bounty not found")
        b = self._load(bounty_id)
        if b["status"] != "submitted":
            raise Exception("No pending submission")

        b["status"] = "judging"
        self._save(bounty_id, b)

        spec  = b["spec"]
        url   = b["sub_url"]
        MAXCH = 3000

        def fetch_and_judge():
            try:
                resp    = gl.nondet.web.get(url)
                content = resp.body.decode("utf-8", errors="replace")[:MAXCH]
            except Exception:
                content = "[URL could not be fetched]"

            prompt = f"""You are an impartial judge for a trustless bounty platform.
Decide if the submitted work PASSES or FAILS the spec.

SPEC (criteria for PASS):
{spec}

SUBMITTED URL: {url}

FETCHED CONTENT (first {MAXCH} chars):
{content}

RULES:
- Return ONLY a JSON object. No markdown. No text outside JSON.
- "verdict" must be exactly "pass" or "fail" (lowercase).
- "reasoning" must be one sentence under 120 characters.
- PASS only if work clearly meets all spec requirements.
- Return "fail" if the URL could not be fetched.

Required format:
{{"verdict": "pass", "reasoning": "The repo contains all required files and tests."}}"""

            result = gl.nondet.exec_prompt(prompt)
            result = result.replace("```json", "").replace("```", "").strip()
            return result

        raw = gl.eq_principle.prompt_comparative(
            fetch_and_judge,
            'The "verdict" field must be the same in both responses'
        )

        try:
            parsed    = json.loads(raw)
            verdict   = str(parsed.get("verdict", "fail")).strip().lower()
            reasoning = str(parsed.get("reasoning", ""))[:200]
        except Exception:
            verdict   = "fail"
            reasoning = "Could not parse AI response"

        if verdict not in ("pass", "fail"):
            verdict = "fail"

        b = self._load(bounty_id)
        b["verdict"]   = verdict
        b["reasoning"] = reasoning

        if verdict == "pass":
            b["status"] = "paid"
            self._save(bounty_id, b)
            self.total_paid_wei = self.total_paid_wei + u256(b["reward_wei"])
            _Recipient(Address(b["solver"])).emit_transfer(value=u256(b["reward_wei"]))
        else:
            b["status"] = "failed"
            self._save(bounty_id, b)

    # ── cancel_bounty ─────────────────────────────────────────
    @gl.public.write
    def cancel_bounty(self, bounty_id: u256) -> None:
        if bounty_id not in self.bounties:
            raise Exception("Bounty not found")
        b = self._load(bounty_id)
        if str(gl.message.sender) != b["poster"]:
            raise Exception("Only poster can cancel")
        if b["status"] != "open":
            raise Exception("Can only cancel open bounty")

        b["status"] = "refunded"
        self._save(bounty_id, b)
        _Recipient(Address(b["poster"])).emit_transfer(value=u256(b["reward_wei"]))

    # ── reclaim_after_fail ────────────────────────────────────
    @gl.public.write
    def reclaim_after_fail(self, bounty_id: u256) -> None:
        if bounty_id not in self.bounties:
            raise Exception("Bounty not found")
        b = self._load(bounty_id)
        if str(gl.message.sender) != b["poster"]:
            raise Exception("Only poster can reclaim")
        if b["status"] != "failed":
            raise Exception("Verdict is not failed")

        b["status"] = "refunded"
        self._save(bounty_id, b)
        _Recipient(Address(b["poster"])).emit_transfer(value=u256(b["reward_wei"]))

    # ── views ─────────────────────────────────────────────────
    @gl.public.view
    def get_bounty(self, bounty_id: u256) -> dict:
        if bounty_id not in self.bounties:
            raise Exception("Bounty not found")
        return self._load(bounty_id)

    @gl.public.view
    def get_open_bounties(self) -> list:
        result = []
        for i in range(int(self.next_id)):
            bid = u256(i)
            if bid in self.bounties:
                b = self._load(bid)
                if b["status"] == "open":
                    result.append({
                        "bounty_id":  b["bounty_id"],
                        "poster":     b["poster"],
                        "title":      b["title"],
                        "reward_wei": b["reward_wei"],
                        "deadline":   b["deadline"],
                        "spec":       b["spec"][:120] + ("..." if len(b["spec"]) > 120 else ""),
                    })
        return result

    @gl.public.view
    def get_stats(self) -> dict:
        return {
            "total_created":  int(self.total_created),
            "total_paid_wei": int(self.total_paid_wei),
            "next_id":        int(self.next_id),
        }
