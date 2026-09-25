1. Inspect `sklearn/cluster/_affinity_propagation.py`, especially:
   - the low-level `affinity_propagation(...)` function return logic,
   - how convergence is detected (`n_iter`, `max_iter`, exemplars `I/K`),
   - `AffinityPropagation.fit` assignment of `cluster_centers_indices_`, `labels_`, and any special handling for degenerate/equal-similarity cases.
2. Patch the non-converged branch so that when convergence is not reached:
   - return `cluster_centers_indices` as an empty integer array,
   - return `labels` as `-1 * np.ones(n_samples, dtype=np.intp)` (or estimator-side equivalent),
   - keep `n_iter_` reflecting actual iterations and preserve the `ConvergenceWarning`.
   This should apply only to true non-convergence, not to the separate “no exemplars / degenerate preferences” logic if that already has defined behavior.
3. Verify estimator-level consistency:
   - `AffinityPropagation.fit` should expose the same sentinel values as the function API,
   - `predict` on a non-converged fitted estimator should continue matching existing tests (likely warning/error behavior based on empty centers).
4. Add/adjust regression coverage in `sklearn/cluster/tests/test_affinity_propagation.py`:
   - strengthen `test_affinity_propagation_non_convergence_regressiontest` to assert empty `cluster_centers_indices_` and all-`-1` labels on the reported non-converging example/configuration,
   - if needed, also assert the function-level API returns the same sentinels.
5. Regression checks to keep in mind:
   - converged cases still produce previous centers/labels,
   - existing non-convergence warning tests still pass,
   - equal-similarity / equal-preference edge cases are unchanged unless they are actually routed through the same incorrect non-converged branch.