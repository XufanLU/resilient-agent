1. Inspect `sklearn/cluster/_affinity_propagation.py`, especially:
- the low-level `affinity_propagation(...)` function return logic,
- convergence detection variables (`converged`, `never_converged`, `n_iter`, etc.),
- `AffinityPropagation.fit` assignment of `cluster_centers_indices_`, `labels_`, and any predict-related state.

2. Patch the non-convergence branch to enforce the documented outputs:
- if the algorithm did not converge by `max_iter`, return an empty integer array for `cluster_centers_indices`;
- return `labels` as an `n_samples` array filled with `-1`;
- preserve the current warning behavior (`ConvergenceWarning`) and `n_iter_` reporting.

3. Ensure this branch is applied consistently for both dense/sparse or precomputed/euclidean entry paths if they share code, and that no later code recomputes labels from stale centers after the non-convergence decision.

4. Verify estimator state expectations in `fit`:
- `cluster_centers_indices_` should be empty on non-convergence;
- `labels_` should be all `-1`;
- if `cluster_centers_` is materialized from indices, confirm the empty-indices case is handled safely.

5. Add/adjust regression coverage in `sklearn/cluster/tests/test_affinity_propagation.py`:
- assert on a known non-converging setup that `cluster_centers_indices_` is empty and `labels_` are all `-1` after `fit`;
- keep/align with existing warning assertions.

6. Regression checks to consider:
- existing convergence tests should still return real centers/labels;
- `test_affinity_propagation_predict_non_convergence` should remain valid, especially if predict behavior depends on empty centers;
- dense/sparse convergence-warning tests should still only warn and not regress in output shape/types.