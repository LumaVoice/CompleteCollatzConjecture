#!/usr/bin/env python3
# ================================================================
#  Collatz Family ABS1/NON-ABS1 Checker (Accelerated O± version)
#  Author: Ryosuke Miyazawa
#  License: MIT
#
#  USER CONFIGURATION (edit these as needed)
#  ---------------------------------------------------------------
#  TYPE            : one of "W+1", "W-1", "B+1", "B-1"
#  RANGE           : inclusive integer range to check (lo, hi)
#  CAP             : max number of accelerated steps before aborting
#  EXAMPLES        : True to print one example ABS1 and NON-ABS1 cycle
#  PARALLEL        : True to enable multi-core processing
#  N_WORKERS       : number of worker processes if PARALLEL = True
#  REPORT_CYCLES   : True to aggregate and print unknown closed cycles
#  MAX_SAMPLES_PER_CYCLE : max starting values to keep per discovered cycle
#  FINGERPRINT_ABS : True => fingerprint cycles by absolute values (merge ± variants)
#  ---------------------------------------------------------------
#
#  HOW TO RUN:
#    $ python3 collatz_o_operator.py
#  (Edit the parameters above before running.)
#
#  WHAT THIS CHECKS:
#    - Iterates the accelerated odd-to-odd operators O_+ and O_-.
#    - Classifies each start n0 as:
#        ABS1     : reached the absolute-1 loop
#                   (accelerated form => [1] or [-1] ONLY IF the domain is A1-stable),
#                   or (raw form) exactly 1 -> 4 -> 2 -> 1.
#        NON-ABS1 : reached some other closed cycle (never visits ±1).
#        CAP      : hit the step cap without closing a cycle.
#    - Additionally records whether the trajectory ever hit 1 (Hit-1).
#
#  OUTPUT:
#    - Type / Range / Step cap / ABS1 definition
#    - Counts of ABS1, NON-ABS1, OTHER (= CAP)
#    - Hit-1 YES/NO counts
#    - Execution time
#    - Optional example cycles (if EXAMPLES=True)
#    - Optional list of unknown closed cycles (if REPORT_CYCLES=True)
#
#  NOTES:
#    - Accelerated step: odd m -> (3m±1) / 2^{v2(3m±1)}.
#      For Bridge (/-2), correct the sign by (-1)^{v2(3m±1)}.
#    - Zero is treated as odd (Odd-Zero): O_+(0)=+1, O_-(0)=-1.
# ================================================================

TYPE                   = "B+1"
RANGE                  = (-100000, 100000)
CAP                    = 1000
EXAMPLES               = True
PARALLEL               = True
N_WORKERS              = 4

REPORT_CYCLES          = True
MAX_SAMPLES_PER_CYCLE  = 3
FINGERPRINT_ABS        = False

# ================================================================
#  Implementation (no need to edit below)
# ================================================================
import time
from typing import Dict, List, Tuple, Optional
from multiprocessing import Pool, cpu_count

# ---------- utilities ----------
def v2(x: int) -> int:
    """2-adic valuation v2(x): largest k with 2^k | x (v2(0) unused)."""
    x = abs(x)
    return (x & -x).bit_length() - 1 if x else 0

def O_plus(m: int) -> int:
    """O_+(m) = (3m+1)/2^{v2(3m+1)} for odd m; extends O_+(0)=+1."""
    if m == 0: return 1
    x = 3*m + 1
    return x // (1 << v2(x))

def O_minus(m: int) -> int:
    """O_-(m) = (3m-1)/2^{v2(3m-1)} for odd m; extends O_-(0)=-1."""
    if m == 0: return -1
    x = 3*m - 1
    return x // (1 << v2(x))

def normalize_initial(n0: int, even_type: str) -> int:
    """
    Collapse the initial even-phase to get an odd starting value for accelerated iteration.
    For Bridge, apply sign flip if the number of /2 divisions is odd.
    """
    if n0 == 0: return 1  # Odd-Zero convention; O_- pushes to -1 on the first odd step if needed.
    n = n0
    if n % 2 == 0:
        k = v2(n)
        n //= (1 << k)
        if even_type == "B" and (k & 1):
            n = -n
    return n

def T_step_accel(n: int, even_type: str, odd_sign: int) -> int:
    """One accelerated step (odd -> next odd) using O_± with Bridge's sign correction."""
    nxt = O_plus(n) if odd_sign == +1 else O_minus(n)
    if even_type == "W":
        return nxt
    k = v2(3*n + (1 if odd_sign == +1 else -1))  # parity of /2 divisions
    return -nxt if (k & 1) else nxt

def parse_type(type_tag: str) -> Tuple[str, int]:
    """Map 'W±1'/'B±1' to (even_type, odd_sign)."""
    even_type = "W" if type_tag[0] == "W" else "B"
    odd_sign  = +1 if type_tag.endswith("+1") else -1
    return even_type, odd_sign

# ---------- A1-stable domain gating ----------
def is_a1_stable_domain(type_tag: str, fixed_sign: int) -> bool:
    """
    Return True iff the domain where the accelerated fixed-point [±1] lies is A1-stable.
    B±1: both domains stable
    W+1: only positive domain stable (fixed_sign = +1)
    W-1: only negative domain stable (fixed_sign = -1)
    """
    if type_tag in ("B+1", "B-1"): return True
    if type_tag == "W+1": return fixed_sign == +1
    if type_tag == "W-1": return fixed_sign == -1
    return False

def is_abs1_loop_from_cycle(cycle: List[int], type_tag: str) -> bool:
    """
    ABS1 if:
      - Accelerated fixed-point [1] or [-1] AND the domain is A1-stable; OR
      - (Raw-form safeguard) absolute values exactly [1,4,2,1].
    """
    if len(cycle) == 1 and cycle[0] in (1, -1):
        return is_a1_stable_domain(type_tag, +1 if cycle[0] == 1 else -1)
    return [abs(x) for x in cycle] == [1, 4, 2, 1]

def is_known_small_loop(cycle: List[int]) -> bool:
    """
    Known trivial loops to exclude from 'unknown':
      - accelerated fixed-point [±1]
      - short loop 1<->2 (raw) and absolute loop 1->4->2->1
    """
    if len(cycle) == 1 and cycle[0] in (1, -1):
        return True
    abs_cyc = [abs(x) for x in cycle]
    if len(abs_cyc) == 2 and set(abs_cyc) == {1, 2}:  # [1,2] or [2,1]
        return True
    return abs_cyc == [1, 4, 2, 1]

# ---------- cycle canonicalization ----------
def canonical_cycle(cyc: List[int], by_abs: bool = False) -> Tuple[int, ...]:
    """
    Rotate cycle so that its lexicographically smallest rotation is chosen.
    If by_abs=True, compare by absolute values (groups sign-flipped variants).
    Returns an immutable tuple as fingerprint.
    """
    L = len(cyc)
    if L == 0: return tuple()
    candidates = []
    for s in range(L):
        rot = cyc[s:] + cyc[:s]
        key = tuple(abs(x) for x in rot) if by_abs else tuple(rot)
        candidates.append((key, tuple(rot)))
    candidates.sort(key=lambda kv: kv[0])
    # return canonical rotation in chosen space (fingerprint space)
    return candidates[0][0] if by_abs else candidates[0][1]

# ---------- worker (accelerated detection with Hit-1 and cycle report) ----------
def worker(args):
    """
    Returns:
      lab         : "ABS1" | "NON-ABS1" | "CAP"
      example     : (start, cycle) or None, for first occurrence of a label
      hit1        : bool, whether 1 was ever visited during the trajectory
      unknown_fp  : fingerprint tuple for unknown cycles, or None
      unknown_cyc : the cycle values for that fingerprint (small), or None
    """
    n0, type_tag, even_type, odd_sign, cap, want_example, report_cycles, fp_abs = args
    hit1 = False
    n = normalize_initial(n0, even_type)
    seen: Dict[int, int] = {}
    seq: List[int] = []
    steps = 0
    while steps < cap:
        if n == 1:  # Hit-1 metric
            hit1 = True
        if n in seen:
            i = seen[n]
            cycle = seq[i:]  # pure cycle
            lab = "ABS1" if is_abs1_loop_from_cycle(cycle, type_tag) else "NON-ABS1"
            # Unknown cycle fingerprint (exclude known trivial ones)
            unknown_fp: Optional[Tuple[int, ...]] = None
            unknown_cyc: Optional[List[int]] = None
            if report_cycles and lab == "NON-ABS1" and not is_known_small_loop(cycle):
                unknown_fp = canonical_cycle(cycle, by_abs=fp_abs)
                unknown_cyc = cycle
            ex = (n0, cycle) if want_example and lab in ("ABS1", "NON-ABS1") else None
            return lab, ex, hit1, unknown_fp, unknown_cyc
        seen[n] = len(seq)
        seq.append(n)
        if n % 2 == 0:
            n = normalize_initial(n, even_type)  # safeguard
        else:
            n = T_step_accel(n, even_type, odd_sign)
        steps += 1
    return "CAP", None, hit1, None, None

# ---------- sweep ----------
def run_sweep(lo: int, hi: int, type_tag: str, cap: int = 1000,
              examples: bool = False, parallel: bool = False, n_workers: int = 4):
    even_type, odd_sign = parse_type(type_tag)

    print("=== Collatz Family Sweep ===")
    print(f"Type        : {type_tag}  (even={even_type}, odd_sign={'+1' if odd_sign==1 else '-1'})")
    print(f"Range       : [{lo}, {hi}]  (count={hi-lo+1})")
    print(f"Step cap    : {cap}  (accelerated O_±)")
    print(f"ABS1 def.   : [1] or [-1] ONLY if the domain is A1-stable  (raw: 1 -> 4 -> 2 -> 1)\n")

    t0 = time.perf_counter()
    counts = {"ABS1": 0, "NON-ABS1": 0, "CAP": 0}
    hit1_yes = 0
    hit1_no  = 0
    examples_found: Dict[str, Tuple[int, List[int]]] = {}
    cycle_registry: Dict[Tuple[int, ...], Dict] = {}  # fingerprint -> info dict

    def add_unknown_cycle(fp: Optional[Tuple[int, ...]], starter: Optional[int], cyc: Optional[List[int]]):
        if fp is None or cyc is None:
            return
        info = cycle_registry.get(fp)
        if info is None:
            cycle_registry[fp] = {"count": 1, "len": len(cyc), "samples": ([starter] if starter is not None else []), "cycle": cyc}
        else:
            info["count"] += 1
            if starter is not None and len(info["samples"]) < MAX_SAMPLES_PER_CYCLE:
                info["samples"].append(starter)

    if parallel:
        n_workers = max(1, min(n_workers, cpu_count()))
        with Pool(processes=n_workers) as pool:
            args_iter = ((n0, type_tag, even_type, odd_sign, cap, examples, REPORT_CYCLES, FINGERPRINT_ABS)
                         for n0 in range(lo, hi+1))
            for lab, ex, hit1, fp, cyc in pool.imap_unordered(worker, args_iter, chunksize=1024):
                counts[lab] = counts.get(lab, 0) + 1
                hit1_yes += int(hit1)
                if not hit1:
                    hit1_no += 1
                if examples and ex and lab not in examples_found:
                    examples_found[lab] = ex
                if REPORT_CYCLES:
                    starter = ex[0] if ex else None
                    add_unknown_cycle(fp, starter, cyc)
    else:
        for n0 in range(lo, hi+1):
            lab, ex, hit1, fp, cyc = worker((n0, type_tag, even_type, odd_sign, cap, examples, REPORT_CYCLES, FINGERPRINT_ABS))
            counts[lab] = counts.get(lab, 0) + 1
            hit1_yes += int(hit1)
            if not hit1:
                hit1_no += 1
            if examples and ex and lab not in examples_found:
                examples_found[lab] = ex
            if REPORT_CYCLES:
                starter = ex[0] if ex else n0
                add_unknown_cycle(fp, starter, cyc)

    t1 = time.perf_counter()
    total = hi - lo + 1
    print(f"Results     : ABS1={counts.get('ABS1',0)}  NON-ABS1={counts.get('NON-ABS1',0)}  OTHER={total - counts.get('ABS1',0) - counts.get('NON-ABS1',0)}")
    print(f"Hit-1       : YES={hit1_yes}  NO={hit1_no}")
    print(f"Time        : {t1 - t0:.3f}s")

    if examples:
        if "ABS1" in examples_found:
            n0, cyc = examples_found["ABS1"]
            print(f"\nExample ABS1 start {n0}: cycle {cyc}")
        if "NON-ABS1" in examples_found:
            n0, cyc = examples_found["NON-ABS1"]
            print(f"Example NON-ABS1 start {n0}: cycle {cyc}")

    if REPORT_CYCLES and cycle_registry:
        print("\nUnknown closed cycles (excluding [±1], 1<->2, and 1->4->2->1):")
        for fp, info in sorted(cycle_registry.items(), key=lambda kv: (-kv[1]["count"], kv[1]["len"])):
            cyc_show = list(fp) if FINGERPRINT_ABS else info["cycle"]
            print(f"  len={info['len']:>2}  count={info['count']:>6}  sample_starts={info['samples']}  cycle={cyc_show}")

# ---------- entry ----------
def main():
    lo, hi = RANGE
    run_sweep(lo, hi, TYPE, cap=CAP, examples=EXAMPLES, parallel=PARALLEL, n_workers=N_WORKERS)

if __name__ == "__main__":
    main()
