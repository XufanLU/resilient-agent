1. Inspect `sklearn/cluster/_affinity_propagation.py`, focusing on:
- the iterative solver in `affinity_propagation(...)`;
- how `converged`/`never_converged`/`n_iter` are tracked;
- the code after the loop that computes exemplars, refines centers, assigns labels, and returns results;
- `AffinityPropagation.fit` handling of `cluster_centers_indices_`, `labels_`, and `cluster_centers_`.

2. Patch the post-loop control flow so there is one authoritative non-convergence path:
- after the iteration loop, check `if not converged` before any exemplar extraction, center refinement, or label recomputation based on the last iterates;
- in that path, keep the existing `ConvergenceWarning` behavior and preserve `n_iter`/`n_iter_`;
- return `cluster_centers_indices` as an empty integer array and `labels` as `np.full(n_samples, -1, dtype=int)`.

3. Patch the final return/assignment point, not only the warning branch:
- ensure any code that currently computes `I`, `K`, refined exemplars, or labels from provisional centers is skipped when non-converged;
- if the implementation structure makes early return awkward, explicitly overwrite outputs at the final return point so later code cannot replace `-1` labels with labels derived from stale exemplar indices.

4. Inspect estimator-state handling in `AffinityPropagation.fit` for empty-center outputs:
- `cluster_centers_indices_` should remain an empty integer array with shape `(0,)`;
- `labels_` should have shape `(n_samples,)` and all values `-1`;
- for `affinity='euclidean'`, `cluster_centers_` should become an empty array of shape `(0, n_features)`;
- for `affinity='precomputed'`, inspect current conventions so `cluster_centers_` is either absent or safely handled without assuming at least one center exists.

5. Inspect related code paths for center-dependent assumptions:
- check whether `fit`, `predict`, or helper routines index into centers without guarding the empty-center case;
- keep current non-convergence predict/error behavior consistent with existing tests, adjusting only if needed to safely handle empty centers.

6. Update regression tests in `sklearn/cluster/tests/test_affinity_propagation.py`:
- extend the non-convergence regression test to assert `cluster_centers_indices_` is empty, `labels_` are all `-1`, and warning behavior remains aligned with existing expectations;
- add dtype/shape assertions: `cluster_centers_indices_.dtype.kind == 'i'`, `cluster_centers_indices_.shape == (0,)`, and `labels_.shape == (n_samples,)`;
- for euclidean affinity, add an assertion that `cluster_centers_.shape == (0, n_features)` if that attribute is expected on fit.

7. Regression checks to encode in tests or code inspection:
- converged cases should still return real centers/labels unchanged;
- existing non-convergence tests such as `test_affinity_propagation_fit_non_convergence`, `test_affinity_propagation_predict_non_convergence`, and dense/sparse convergence-warning tests should continue to reflect preserved warnings and safe estimator state;
- ensure the fix applies wherever the shared solver is used so one path cannot still surface stale exemplar indices on non-convergence.