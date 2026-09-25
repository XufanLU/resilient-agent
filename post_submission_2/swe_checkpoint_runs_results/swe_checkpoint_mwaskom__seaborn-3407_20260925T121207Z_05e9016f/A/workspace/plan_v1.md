1. Inspect `seaborn/axisgrid.py`, especially:
   - `PairGrid.map_diag`
   - any helper methods used to extract vectors for plotting
   - `pairplot` setup that determines `x_vars` / `y_vars`
2. Update the column-access logic so single-variable extraction is robust for tuple-valued column labels / MultiIndex columns. Most likely patch:
   - replace direct `self.data[var]` access in `map_diag` with label-based scalar column selection that preserves tuple labels, e.g. `self.data.loc[:, var]` or a small helper used consistently for single-column lookup.
   - if hue lookup uses the same pattern (`self.data[self._hue_var]`), apply the same fix there to avoid analogous MultiIndex failures.
3. Check whether other `PairGrid` methods use the same fragile access pattern for single columns (`map_offdiag`, axis label setup, dropna prep, etc.). If so, consider centralizing a helper like `_get_column(data, key)` to avoid one-off fixes and keep behavior consistent.
4. Add/adjust regression coverage in `tests/test_axisgrid.py` around `TestPairGrid::test_pairplot_column_multiindex` to ensure:
   - `sns.pairplot(df)` succeeds with MultiIndex columns
   - diagonal mapping works without raising
   - optionally verify the grid variables correspond to the original tuple column labels rather than flattened strings.
5. Regression checks to keep in mind while patching:
   - ordinary flat string column names still work
   - explicit `hue` access is unaffected
   - existing `PairGrid` shape/variable-selection behavior remains unchanged for non-MultiIndex data
   - no unintended changes to `FacetGrid` / `JointGrid`, which are covered by the listed pass-to-pass tests.