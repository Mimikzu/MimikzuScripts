"""Explain simple suspicious-message indicators; no automatic moderation."""

from __future__ import annotations

import argparse
import json
import re


SIGNALS = (
    ("credential request", re.compile(r"\b(password|passcode|login details|seed phrase|recovery phrase)\b", re.I)),
    ("urgent pressure", re.compile(r"\b(urgent|act now|immediately|expires in|last chance)\b", re.I)),
    ("prize or giveaway lure", re.compile(r"\b(free nitro|claim your prize|you won|giveaway winner)\b", re.I)),
    ("suspicious short link", re.compile(r"https?://(?:bit\.ly|tinyurl\.com|t\.co|is\.gd)/\S+", re.I)),
    ("Discord invite link", re.compile(r"(?:discord\.gg/|discord(?:app)?\.com/invite/)\S+", re.I)),
    ("payment or crypto request", re.compile(r"\b(send (?:me )?(?:money|crypto)|wallet address|payment required)\b", re.I)),
    ("impersonation language", re.compile(r"\b(admin|moderator|support team|staff)\b.{0,30}\b(verify|password|account)\b", re.I)),
)


def explain(message: str) -> dict[str, object]:
    findings = [{"signal": name, "evidence": match.group(0)} for name, pattern in SIGNALS if (match := pattern.search(message))]
    score = min(len(findings), 4)
    return {
        "assessment": "review suggested" if findings else "no configured signals found",
        "signals": findings,
        "heuristic_score": score,
        "score_note": "Count of matched heuristic categories, capped at 4; not a probability or proof of a scam.",
        "action": "Human review only. No member was warned, punished, or contacted.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text", required=True, help="Message text to inspect locally.")
    args = parser.parse_args()
    print(json.dumps(explain(args.text), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
