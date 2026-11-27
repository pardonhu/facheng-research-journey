"""Synthetic finite-field check; no hardware data or paper reproduction."""
import itertools
import json
import pathlib
import random

Q = 5

def rref(a):
    a = [[v % Q for v in row] for row in a]
    row = 0
    if not a:
        return a
    for col in range(len(a[0])):
        pivot = next((i for i in range(row, len(a)) if a[i][col]), None)
        if pivot is None:
            continue
        a[row], a[pivot] = a[pivot], a[row]
        inv = pow(a[row][col], -1, Q)
        a[row] = [v * inv % Q for v in a[row]]
        for i in range(len(a)):
            if i != row and a[i][col]:
                c = a[i][col]
                a[i] = [(x-c*y) % Q for x, y in zip(a[i], a[row])]
        row += 1
        if row == len(a):
            break
    return a

def rank(a):
    return sum(any(row) for row in rref(a))

def project_closed(a, oldcols):
    return [row[oldcols:] for row in rref(a) if not any(row[:oldcols]) and any(row[oldcols:])]

# Columns: a_old, a_new, b, c. Two old equations share a_old.
base = [[1,0,1,1], [1,0,2,1], [0,1,1,2]]
fresh = [0,1,0,1]
late_old = [1,0,0,2]
errors = 0
for a0, a1, b, c in itertools.product(range(Q), repeat=4):
    y1 = (a0+b+c) % Q
    y2 = (a0+2*b+c) % Q
    y3 = (a1+b+2*c) % Q
    y4 = (a1+c) % Q
    bhat = (y2-y1) % Q
    chat = (y3-bhat-y4) % Q
    a1hat = (y4-chat) % Q
    errors += (a1hat, bhat, chat) != (a1,b,c)

rng = random.Random(20261127)
identity_failures = 0
for _ in range(300):
    old = rng.randrange(1,9)
    rows = rng.randrange(4,21)
    a = [[rng.randrange(Q) for _ in range(old+4)] for _ in range(rows)]
    expected = rank(a)-rank([r[:old] for r in a])
    identity_failures += rank(project_closed(a,old)) != expected

result = {
    "synthetic": True, "field": "GF(5)",
    "enumerated_value_assignments": 625,
    "latest_state_errors_after_one_fresh_equation": errors,
    "latest_constraints_preserved_from_base": rank(project_closed(base,1)),
    "latest_constraints_if_discard_old_packets": rank([base[-1][1:]]),
    "full_version_elimination_latest_constraints": rank(base)-rank([r[:1] for r in base]),
    "random_algebra_identity_cases": 300,
    "random_algebra_identity_failures": identity_failures,
    "late_old_counterexample": {
        "full_cache_current_rank_after_late_packet": rank(project_closed(base+[late_old],1)),
        "prematurely_compacted_current_rank_after_late_packet": rank(project_closed([[0]+r for r in project_closed(base,1)]+[late_old],1)),
    },
    "interpretation": "Algebraic reuse is valid and equals full multi-version elimination; premature closure loses useful late equations. No new-protocol gain established.",
}
path = pathlib.Path(__file__).with_name('mixed-version-check.json')
path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf8')
print(json.dumps(result, indent=2, ensure_ascii=False))
