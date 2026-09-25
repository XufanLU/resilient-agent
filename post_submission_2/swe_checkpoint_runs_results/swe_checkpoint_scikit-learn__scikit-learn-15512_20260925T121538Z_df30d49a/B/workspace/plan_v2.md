1. Inspect `sklearn/cluster/_affinity_propagation.py` in both layers.
   - In the low-level `affinity_propagation(...)` function, trace:
     - convergence detection and loop exit conditions,
     - where `n_iter` is finalized,
     - the branch taken when `max_iter` is reached without convergence,
     - any fallback/post-loop code that still computes exemplars or labels from provisional `I`, `K`, or message matrices after failure.
   - In `AffinityPropagation.fit`, trace how function outputs are converted into:
     - `cluster_centers_indices_`,
     - `labels_`,
     - `cluster_centers_`,
     - estimator state relevant to `predict` and fittedness checks.

2. Patch the implementation with explicit outcome separation.
   - Converged case: keep existing center/label derivation unchanged.
   - Non-converged due to hitting `max_iter`:
     - bypass any fallback exemplar/label derivation,
     - return `cluster_centers_indices` as an empty integer array,
     - return `labels` as length-`n_samples` integer array filled with `-1`,
     - preserve the existing `ConvergenceWarning`,
     - preserve `n_iter`/`n_iter_` as the actual iteration count, which should remain `max_iter` for the reproducer if that is the intended setup.
   - Degenerate/equal-similarity cases:
     - keep their existing dedicated behavior untouched unless inspection shows they are incorrectly routed through the same non-converged branch.
   - Be explicit in code/comments that “non-converged” and “degenerate/no exemplars” are distinct outcomes.

3. Verify estimator-level consistency after the low-level fix.
   - Ensure `AffinityPropagation.fit` exposes the same sentinel outputs as the function API on true non-convergence.
   - Review how empty `cluster_centers_indices_` affects `cluster_centers_` construction and downstream `predict` checks.
   - Do not assume warning vs error behavior for `predict`; instead, make sure the post-fit estimator state remains consistent with the existing `test_affinity_propagation_predict_non_convergence` expectation.

4. Add/adjust regression coverage in `sklearn/cluster/tests/test_affinity_propagation.py`.
   - Strengthen `test_affinity_propagation_non_convergence_regressiontest` to assert, on the documented non-converging fixture:
     - `cluster_centers_indices_` is empty,
     - `cluster_centers_indices_` has integer dtype,
     - `labels_` equals all `-1`,
     - `labels_` has length `n_samples` and integer dtype,
     - `n_iter_ == max_iter` if that matches the current fixture’s intended non-converged path.
   - If not already covered, add a function-level regression for `affinity_propagation(...)` asserting the same sentinel outputs and iteration count so estimator/function behavior stays aligned.

5. Regression checks to keep in mind while patching.
   - Existing converged tests must remain unchanged.
   - Existing non-convergence warning tests must still observe the warning behavior.
   - Equal-similarity/equal-preference tests listed in `pass_to_pass` must keep their documented outputs.
   - Existing predict tests, especially non-convergence behavior, must continue to match the estimator state produced by the fix.