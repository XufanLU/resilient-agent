1. Inspect `seaborn/axisgrid.py` for how `pairplot` derives `vars`, `x_vars`, and `y_vars`, and how `PairGrid` stores `_x_vars` / `_y_vars` or `diag_vars` when columns are tuples.
2. In `PairGrid`, update column access so tuple-valued column labels from a `MultiIndex` are always treated as a single key, not as a listlike selector. The safest patch is to route variable lookup through a small helper used everywhere grid variables are fetched, e.g.:
   - if the label is a tuple and `self.data.columns` is a `MultiIndex`, access with `.loc[:, var]` or another form that preserves tuple-as-single-column semantics;
   - otherwise keep normal scalar lookup.
3. Replace direct `self.data[var]` usages in `map_diag` and any analogous `PairGrid` mapping methods that read columns by variable label, so behavior is consistent for diagonal and off-diagonal plotting.
4. Verify that any logic removing `hue` from inferred numeric vars also handles tuple column labels without flattening or stringifying them.
5. Add/adjust regression coverage in `tests/test_axisgrid.py` around `TestPairGrid::test_pairplot_column_multiindex`, ensuring `sns.pairplot(df)` succeeds for a MultiIndex-column frame and, ideally, that both diagonal and off-diagonal mappings execute.
6. Regression checks to consider from nearby behavior:
   - standard single-level column `pairplot` still works;
   - explicit `vars` / `x_vars` / `y_vars` using tuple labels works;
   - hue handling is unaffected when `hue` is absent/present;
   - no unintended changes to `FacetGrid` / `JointGrid` paths listed in pass-to-pass tests.