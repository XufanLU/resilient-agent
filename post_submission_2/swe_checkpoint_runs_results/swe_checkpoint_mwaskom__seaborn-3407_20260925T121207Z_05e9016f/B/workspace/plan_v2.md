1. Audit `seaborn/axisgrid.py` only for PairGrid-related handling of variable labels:
   - `pairplot(...)` default inference of `vars`, `x_vars`, `y_vars`, especially numeric-column selection when `data.columns` is a `MultiIndex`.
   - `PairGrid.__init__` storage/normalization of x/y/diag vars and hue.
   - every PairGrid column extraction site using `self.data[var]` or `data[var]`, including diagonal, off-diagonal, and hue paths.

2. Introduce a small PairGrid-local helper (or equivalent internal function in `axisgrid.py`) such as `_get_var_series(data, var)` and route all PairGrid variable extraction through it.
   - Intended behavior:
     - if `data.columns` is a `MultiIndex` and `var` is a tuple, select it as a single column key with `data.loc[:, var]` (or another scalar-column access pattern that preserves tuple-as-one-label semantics);
     - otherwise use the existing normal scalar lookup behavior.
   - Make the helper explicit about assumptions:
     - if the lookup returns a `DataFrame` because MultiIndex columns are duplicated, either preserve current downstream expectations only when a `Series` is returned or raise a clear error rather than silently proceeding.

3. Replace direct PairGrid lookups with the helper across all relevant paths, not just `map_diag`:
   - `map_diag`
   - off-diagonal mapping methods (`map_offdiag`, `map_upper`, `map_lower`, `map` as applicable)
   - any hue/vector extraction used during plotting callbacks.
   This ensures the fix covers the traceback site and other latent tuple-label failures.

4. Review PairGrid variable inference and filtering logic for tuple-label safety:
   - numeric column inference used by `pairplot`
   - membership/removal logic such as `if hue in numeric_cols` and list comprehensions excluding hue
   - any normalization that might accidentally iterate into tuple labels, stringify them, or otherwise break structural equality.

5. Add focused regression coverage in `tests/test_axisgrid.py`:
   - keep/extend `TestPairGrid::test_pairplot_column_multiindex` so `sns.pairplot(df)` succeeds with MultiIndex columns;
   - add a lower-level test separating construction from mapping, e.g. `PairGrid(df).map_diag(...)` and `map_offdiag(...)`, so failures in extraction vs high-level orchestration are distinguishable;
   - include explicit tuple-label `vars` / `x_vars` / `y_vars` cases if not already covered.

6. Regression checks to keep in mind while implementing:
   - ordinary single-level column PairGrid/pairplot behavior remains unchanged;
   - hue handling still works with and without hue present;
   - tuple labels compare structurally in inferred/excluded variable lists;
   - avoid broad helper changes in FacetGrid/JointGrid unless the PairGrid audit shows a necessary shared dependency.