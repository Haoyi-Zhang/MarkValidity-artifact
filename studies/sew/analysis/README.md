# Shared-evidence comparison analysis

`conditional_bounds.py` implements the exact rational reference calculations. `natural_analysis.py` supplies incremental coefficient aggregation, disclosure policies, and comparison bounds. Independent receivers reconstruct decisions from the retained observation rows and public query history.

The matched-disclosure results are in `../../../results/sew/analysis-primary/` and `analysis-all-withheld/`. The all-withheld analysis measures the effect of withholding reference-identical initial admissions. The independently chosen query policies and actual native audit times are in the adjacent `comparison_costs/` implementation and `../../../results/comparisons/` data.

`generate_paper.py` supplies the SEW observation tables; `plot_comparisons.py` draws its joint comparison figure with Python. The current paired conditional tables and figures come from `studies/conditional/` and the current CREST matrices from `studies/crest/`. Run the single project entry point `python3 paper/generate_publication.py` from the project root to combine these inputs and lay out the selected figures at print width in color and grayscale.

Use the common artifact entry points for receiving and fresh executions. Supplementary methods and derivations state the assumptions behind each certificate and distinguish joint yield from conditional detection.
