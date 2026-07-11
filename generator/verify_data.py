#!/usr/bin/env python3
"""Sanity-check ../data.js after build_data.py. Exit 1 on failure.

Cross-source check: monthly CPA revenue computed from svod.csv (DATA.totals.rev)
must match Revenue CPA from fakt.csv (STREAMS.cpa) — two independent tables.
Plus structural checks: months present, totals non-zero, insights parse.
"""
import json, sys

TOL = 0.01  # 1% relative tolerance between the two sources

s = open("../data.js", encoding="utf-8").read()

def ex(name):
    key = f"const {name} = "
    i = s.find(key)
    assert i != -1, f"{name} missing in data.js"
    i += len(key); j = s.find("\n", i)
    return json.loads(s[i:j].rstrip()[:-1])

DATA = ex("DATA"); STREAMS = ex("STREAMS"); INSIGHTS = ex("INSIGHTS_LOG")
TAGSTATS = ex("TAGSTATS"); DRILL = ex("DRILLDOWN"); PART = ex("PARTNERS")

errors, warnings = [], []

# months sane and aligned
if not DATA["months"]: errors.append("DATA.months is empty")
if not STREAMS["months"]: errors.append("STREAMS.months is empty")
if DATA["months"] != STREAMS["months"]:
    warnings.append(f"month sets differ: svod={DATA['months']} vs fakt={STREAMS['months']}")

# cross-source: svod CPA revenue vs fakt Revenue CPA, per month
for m in DATA["months"]:
    a = DATA["totals"]["rev"].get(m, 0)
    b = STREAMS["cpa"].get(m)
    if b is None:
        warnings.append(f"{m}: no Revenue CPA in fakt.csv"); continue
    if b and abs(a - b) / b > TOL:
        errors.append(f"{m}: CPA mismatch svod={a:,.0f} vs fakt={b:,.0f} ({(a-b)/b*100:+.1f}%)")

# totals non-zero for every month
for m in DATA["months"]:
    if DATA["totals"]["gmv"].get(m, 0) <= 0: errors.append(f"{m}: GMV is zero in svod")
    if DATA["totals"]["cnt"].get(m, 0) <= 0: errors.append(f"{m}: sales count is zero in svod")

# structures non-empty
if len(PART) < 20: errors.append(f"suspiciously few partners: {len(PART)}")
if len(DATA["directions"]["rev"]) < 15: errors.append(f"suspiciously few directions: {len(DATA['directions']['rev'])}")
if not DRILL: errors.append("DRILLDOWN is empty")
if not isinstance(INSIGHTS, list) or not INSIGHTS: errors.append("INSIGHTS_LOG empty or invalid")
for e in INSIGHTS:
    for k in ("month", "findings", "hypotheses"):
        if k not in e: errors.append(f"insights entry missing '{k}': {str(e)[:60]}")

for w in warnings: print("WARN:", w)
if errors:
    for e in errors: print("FAIL:", e)
    sys.exit(1)
print(f"VERIFY OK | months: {DATA['months'][0]}–{DATA['months'][-1]} | partners: {len(PART)} | "
      f"last-month CPA: svod {DATA['totals']['rev'][DATA['months'][-1]]:,.0f} vs fakt {STREAMS['cpa'].get(DATA['months'][-1], 0):,.0f}")
