# Evidence disclosure with measured complete labels

This is a retrospective evidence-budget study. All JavaScript outcomes were
already measured in `revision-native-completion`; this replay withholds labels
and discloses them one exact source group at a time. It executes no task
programs. The policy order uses source identities, configuration order and known
detection coefficients, never hidden behavioral outcomes.

## Fresh-contract seed

The initial policy contains 22,054 rechecked Python erasure proofs and fresh
JavaScript labels for 204 source identities selected by the original 252-row
execution inventory. Those JavaScript identities cover 2,946 configuration
rows. The seed therefore labels 40,962 of the full 76,032 configurations and
leaves 21,891 JavaScript source groups undisclosed. Old execution outcomes are
not used to label the new contract. The seed source selection is historical;
its behavioral values are read from the new actual observations.

`fresh_policy_bridge.csv` records that recomputing the seed from the new labels
reproduces the nine earlier combined pairwise interval endpoints. This is an
observed agreement for the frozen study, not a general implication between
stateful and fresh-input execution contracts.

## Compared orders and exact bounds

For each of nine combined workload/pair comparisons, the study uses the signed
coefficient of every unknown exact source. A nonzero coefficient indicates that
learning this source's validity can affect this pair's interval. All compared
orders use the same eligible set; zero-influence sources are excluded from
every order.

1. `largest-coefficient`: descending absolute coefficient, with source identity
   as the tie-breaker.
2. `configuration-first`: first occurrence in the frozen configuration table.
3. `sha-random`: sixteen fixed SHA-256-keyed orders with seeds 0 through 15.

Each disclosed label removes exactly the absolute coefficient from interval
width. Thus the largest-coefficient order minimizes the remaining width at a
fixed number of distinct source queries. It does **not** necessarily minimize
time to certify a winner, nor the number of task input calls. Query input cost
is that source's frozen domain size and is reported separately.

The balanced lexical-versus-structural comparison illustrates the distinction:

| Order | Additional source queries to certification | Additional input calls |
| --- | ---: | ---: |
| Largest coefficient | 2,699 | 7,517,997 |
| Configuration first | 2,590 | 7,372,918 |
| Sixteen fixed SHA orders, median | 2,717.5 | 7,534,100 |
| Sixteen fixed SHA orders, observed range | 2,688–2,724 | 7,375,564–7,551,272 |

There are 2,724 eligible sources in this comparison. Its completed lexical lead
is 7/10560. The coefficient order shrinks width optimally, but configuration
order reaches a positive lower bound sooner on these measured labels. The
sixteen-order range is descriptive and is not a confidence interval or a
significance test. Schedules for distinct pairs are separate experiments; their
query counts must not be summed and described as one shared audit without
deduplicating the requested source identities.

## Files and checks

- `registration.json`: the fixed order rules, contracts, hashes and seed policy.
- `python-proof-rechecks.jsonl.gz`: all saved Python sources re-admitted under
  the stated fresh-compatible erasure premises.
- `coefficients.csv.gz`: signed integer coefficients, exact denominators,
  source identities and costs for each pair.
- `traces.csv.gz`: every query, disclosed label, exact interval numerator,
  cumulative input-call cost and certification status.
- `schedule_summary.csv`: all 162 schedules and earliest certification points.
- `checkpoints.csv`: selected complete-trace points for plotting.
- `random_order_summary.csv`: descriptive ranges/medians for the sixteen orders.
- `verification.json`: independent coefficient/order reconstruction, all
  420,858 trace rows, 420,696 per-query width comparisons and 3,454 independent
  closed-form endpoint checks.
- `controls.log`: six controls, including all 363 coefficient tables over
  `{-2,0,3}` with one through five groups, exhaustive fixed-budget subset
  optimization, conditional-completion checks and a counterexample separating
  minimum interval width from earliest certification.

From `artifact/`:

```sh
python3 -B -S audit_source_budget.py --out /absolute/fresh/audit-budget
python3 -B -S verify_source_budget.py --out /absolute/fresh/audit-budget
python3 -B -S -m unittest discover -s tests -p 'test_source_budget.py' -v
```

The verifier does not import the producer's coefficient, order or update
functions. It explicitly reuses the AST admission rule for the source proofs;
all numerical coefficients and schedules are reconstructed independently from
configuration-level records and the completed labels.
