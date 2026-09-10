import argparse, sys
from pathlib import Path
from .keys import load_or_create
from .token import issue, verify

def main(argv=None):
    p = argparse.ArgumentParser(prog="ir_attest")
    sub = p.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("issue")
    for a in ("--iss", "--sub", "--scope", "--incident"):
        i.add_argument(a, required=True)
    i.add_argument("--ttl", type=int, default=900)
    i.add_argument("--keys", default="keys")
    v = sub.add_parser("verify")
    v.add_argument("token"); v.add_argument("--scope", required=True); v.add_argument("--keys", default="keys")
    a = p.parse_args(argv)
    kp = load_or_create(Path(a.keys))
    if a.cmd == "issue":
        print(issue(kp.private, iss=a.iss, sub=a.sub, scope=a.scope,
                    incident_ref=a.incident, ttl_seconds=a.ttl))
    else:
        r = verify(a.token, kp.public, expected_scope=a.scope)
        print(r.as_channel_text())
        return 0 if r.valid else 1
