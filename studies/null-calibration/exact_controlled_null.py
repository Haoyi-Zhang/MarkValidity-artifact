"""Part 1: exact correlated-null and multiple-query calibration of the controlled detector.

Standard library only. Usage (from the artifact root):
    python3 -B studies/null-calibration/exact_controlled_null.py --out results/null-calibration/controlled-correlated-null.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from fractions import Fraction
from math import comb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from covewm import benchmark  # noqa: E402

N_MAX = benchmark.PAYLOAD_BITS
ALPHA_EXACT = Fraction(benchmark.ALPHA)  # exact binary value of the float 1e-4 used by the implementation
RHO_GRID = ["0", "1/100", "1/50", "1/20", "1/10", "1/5", "3/10", "1/2", "1"]
BLOCK_GRID = [1, 2, 3, 4, 6, 8, 12, 24]
K_GRID = [1, 3, 16, 128, 1003, 1024, 16384]
DIGITS = 40


def frac_str(x: Fraction) -> str:
    return f"{x.numerator}/{x.denominator}"


def decimal_from_ratio(num: int, den: int, digits: int = DIGITS) -> str:
    """Round num/den (0 <= num/den) to `digits` significant digits, half-even, scientific notation."""
    if num == 0:
        return "0"
    # exponent e with 10^e <= num/den < 10^(e+1); estimate from bit lengths then correct.
    e = math.floor((num.bit_length() - den.bit_length()) * math.log10(2))
    def ge_pow10(k):  # num/den >= 10^k ?
        return num * 10 ** (-k) >= den if k < 0 else num >= den * 10 ** k
    while not ge_pow10(e):
        e -= 1
    while ge_pow10(e + 1):
        e += 1
    shift = digits - 1 - e
    if shift >= 0:
        q, r = divmod(num * 10 ** shift, den)
        twice_r, d2 = 2 * r, den
    else:
        q, r = divmod(num, den * 10 ** (-shift))
        twice_r, d2 = 2 * r, den * 10 ** (-shift)
    if twice_r > d2 or (twice_r == d2 and q % 2 == 1):
        q += 1
    s = str(q)
    if len(s) > digits:  # rounding carried into a new digit
        s = s[:-1]
        e += 1
    return f"{s[0]}.{s[1:]}e{e}"


def binomial_tail(n: int, m: int) -> Fraction:
    if n <= 0:
        return Fraction(1)
    return Fraction(sum(comb(n, i) for i in range(m, n + 1)), 2 ** n)


def kstar(n: int):
    for m in range(0, n + 1):
        if binomial_tail(n, m) <= ALPHA_EXACT:
            return m
    return None


def rising(x: Fraction, j: int) -> Fraction:
    out = Fraction(1)
    for i in range(j):
        out *= x + i
    return out


def beta_binomial_pmf(n: int, rho: Fraction) -> list[Fraction]:
    if rho == 0:
        return [Fraction(comb(n, k), 2 ** n) for k in range(n + 1)]
    if rho == 1:
        if n == 0:
            return [Fraction(1)]
        pmf = [Fraction(0)] * (n + 1)
        pmf[0] += Fraction(1, 2)
        pmf[n] += Fraction(1, 2)
        return pmf
    a = (1 - rho) / (2 * rho)
    denom = rising(2 * a, n)
    return [comb(n, k) * rising(a, k) * rising(a, n - k) / denom for k in range(n + 1)]


def accept_prob(pmf: list[Fraction], threshold) -> Fraction:
    if threshold is None:
        return Fraction(0)
    return sum(pmf[threshold:], Fraction(0))


def block_accept_prob(c: int, n: int = N_MAX) -> Fraction:
    blocks = n // c
    need = -(-kstar(n) // c)  # ceil
    return Fraction(sum(comb(blocks, b) for b in range(need, blocks + 1)), 2 ** blocks)


def render(x: Fraction) -> dict:
    return {"exact": frac_str(x), "decimal40": decimal_from_ratio(x.numerator, x.denominator), "float": float(x)}


def any_of_k(p: Fraction, K: int) -> dict:
    n_, d_ = p.numerator, p.denominator
    dk = d_ ** K
    num = dk - (d_ - n_) ** K
    union = min(Fraction(1), K * p)
    dec = decimal_from_ratio(num, dk)
    return {"K": K,
            "independent_any_accept_decimal40": dec,
            "independent_any_accept_float": float(dec),
            "arbitrary_dependence_lower": render(p),
            "arbitrary_dependence_upper_union": render(union)}


def detector_confirmation():
    rows = []
    for n in range(N_MAX + 1):
        ks = kstar(n)
        for m in range(n + 1):
            states = [benchmark.CarrierState(i, "lexical", 0, 0 if i < m else 1, i < n, "none") for i in range(N_MAX)]
            out = benchmark.detector(states)
            assert out["surviving_sites"] == n and out["match_count"] == m
            expected = int(ks is not None and m >= ks)
            rows.append({"n": n, "m": m, "detected": out["detected"], "rule_detected": expected})
            if out["detected"] != expected:
                raise SystemExit(f"detector disagrees with exact-tail rule at n={n}, m={m}")
    return rows


def build():
    thresholds = {n: kstar(n) for n in range(N_MAX + 1)}
    confirm = detector_confirmation()
    rho_tables = []
    p0 = {}
    for rho_s in RHO_GRID:
        rho = Fraction(rho_s)
        rows = []
        for n in range(N_MAX + 1):
            p = accept_prob(beta_binomial_pmf(n, rho), thresholds[n])
            if rho == 0:
                p0[n] = p
            rows.append({"n": n, "kstar": thresholds[n], "accept_probability": render(p),
                         "ratio_to_independent_fair": (render(p / p0[n]) if p0[n] > 0 else None)})
        rho_tables.append({"rho": rho_s, "beta_a": (frac_str((1 - rho) / (2 * rho)) if 0 < rho < 1 else None), "rows": rows})
    block_rows = []
    for c in BLOCK_GRID:
        p = block_accept_prob(c)
        block_rows.append({"c": c, "blocks": N_MAX // c, "blocks_needed": -(-thresholds[N_MAX] // c),
                           "accept_probability": render(p), "ratio_to_independent_fair": render(p / p0[N_MAX])})
    multi_n24_rho = []
    for t in rho_tables:
        p = Fraction(t["rows"][N_MAX]["accept_probability"]["exact"])
        multi_n24_rho.append({"rho": t["rho"], "n": N_MAX, "per_query": render(p), "K_table": [any_of_k(p, K) for K in K_GRID]})
    multi_n24_block = []
    for b in block_rows:
        p = Fraction(b["accept_probability"]["exact"])
        multi_n24_block.append({"c": b["c"], "n": N_MAX, "per_query": render(p), "K_table": [any_of_k(p, K) for K in K_GRID]})
    multi_fair_all_n = []
    for n in range(N_MAX + 1):
        if p0[n] > 0:
            multi_fair_all_n.append({"n": n, "per_query": render(p0[n]), "K_table": [any_of_k(p0[n], K) for K in K_GRID]})
    protocol = ROOT / "studies" / "null-calibration" / "protocol.json"
    return {
        "schema": "markvalidity-null-calibration-controlled-v1",
        "protocol_sha256": hashlib.sha256(protocol.read_bytes()).hexdigest(),
        "benchmark_sha256": hashlib.sha256((ROOT / "src" / "covewm" / "benchmark.py").read_bytes()).hexdigest(),
        "alpha_float": benchmark.ALPHA, "alpha_exact_binary_value": frac_str(ALPHA_EXACT),
        "payload_bits": N_MAX,
        "thresholds": [{"n": n, "kstar": thresholds[n],
                        "tail_at_kstar": (render(binomial_tail(n, thresholds[n])) if thresholds[n] is not None else None)}
                       for n in range(N_MAX + 1)],
        "detector_confirmation": {"calls": len(confirm), "all_agree": all(r["detected"] == r["rule_detected"] for r in confirm),
                                  "accepting_n_m_pairs": [[r["n"], r["m"]] for r in confirm if r["detected"]]},
        "rho_grid": RHO_GRID, "block_grid": BLOCK_GRID, "K_grid": K_GRID,
        "beta_binomial": rho_tables,
        "duplicated_site_blocks_n24": block_rows,
        "multiple_queries_n24_beta_binomial": multi_n24_rho,
        "multiple_queries_n24_blocks": multi_n24_block,
        "multiple_queries_fair_all_n": multi_fair_all_n,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    data = build()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"written": str(args.out), "n24_fair": data["beta_binomial"][0]["rows"][N_MAX]["accept_probability"]["exact"]}))


if __name__ == "__main__":
    main()
