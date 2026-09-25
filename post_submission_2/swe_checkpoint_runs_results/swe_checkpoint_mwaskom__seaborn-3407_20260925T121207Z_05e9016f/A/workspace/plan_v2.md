1. Inspect `seaborn/axisgrid.py` end-to-end for `PairGrid` variable lifecycle:
   - `pairplot(...)` variable inference / defaults.
   - `PairGrid.__init__` construction of `self.x_vars`, `self.y_vars`, and `self.diag_vars`.
   - Confirm whether tuple-valued labels from MultiIndex columns are preserved unchanged or transformed before plotting.

2. Inspect `PairGrid.map_diag` and neighboring code paths to identify every single-column access on `self.data`:
   - `self.data[var]` for diagonal vectors.
   - hue extraction such as `self.data[self._hue_var]`.
   - any per-variable logic used for labels, masks, or NA filtering.
   Determine which sites intend exact single-column lookup versus broader selection semantics.

3. Add a dedicated helper in `axisgrid.py` for exact single-column retrieval from a DataFrame by label, returning a Series and preserving tuple labels.
   - Design it only for the “one known column label” case.
   - Verify pandas behavior for MultiIndex columns so the helper avoids ambiguous `__getitem__` and avoids `.loc[:, var]` partial-selection pitfalls.
   - Likely implementation should use exact column index resolution rather than generic tuple indexing.

4. Search all `self.data[...]` / similar column lookups in `axisgrid.py` and classify them:
   - Exact single-column access → migrate to the helper.
   - Intentional multi-column / listlike selection → leave unchanged.
   This keeps the patch minimal and avoids unintended behavior changes outside the bug surface.

5. Inspect `dropna` / mask-construction paths in `PairGrid`:
   - Check whether they build lists from `x_vars`, `y_vars`, `diag_vars`, and possibly hue.
   - Verify tuple labels pass through unchanged and are not unpacked/coerced in ways that would break MultiIndex handling.
   - Only patch these paths if inspection shows the same exact-label bug there.

6. Update regression coverage in `tests/test_axisgrid.py` around `TestPairGrid::test_pairplot_column_multiindex`:
   - Keep the failing scenario with MultiIndex columns.
   - Add an assertion stronger than “does not raise”, such as verifying `grid.x_vars` / `grid.y_vars` (or relevant axis labels) still contain the original tuple labels.
   - If appropriate, include a hue-related MultiIndex case only if code inspection shows that path shares the same bug.

7. Regression checks to target when validating the patch:
   - Existing flat-column `PairGrid` / `pairplot` behavior unchanged.
   - Diagonal mapping still works for ordinary DataFrames.
   - Hue handling is unaffected for normal columns and robust for exact tuple-valued labels if touched.
   - No collateral changes to `FacetGrid` / `JointGrid` behavior, especially in tests listed as pass-to-pass.