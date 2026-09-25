1. Inspect `sympy/assumptions/refine.py` to confirm current `refine()` dispatch behavior for function handlers:
   - Check whether `arg` already has a handler.
   - Confirm whether defining `refine_arg` is sufficient by naming convention or whether a dispatch-table entry is also required.
   - Review `refine_abs`, `refine_sign`, and `refine_atan2` for coding style and related assumption logic.

2. Add or extend `refine_arg(expr, assumptions)` with minimal, assumption-driven rules:
   - Let `z = expr.args[0]`.
   - If `ask(Q.positive(z), assumptions)` is `True`, return `S.Zero`.
   - If `ask(Q.negative(z), assumptions)` is `True`, return `S.Pi` only after confirming this codepath’s assumptions semantics make that a negative real case (or by matching whatever real-negative pattern analogous handlers use).
   - If `ask(Q.zero(z), assumptions)` is `True`, do not introduce a new refined value unless existing SymPy `arg(0)` refinement semantics already define one; otherwise leave unchanged.
   - In all other cases, return the original expression.

3. Keep the change localized to refinement only:
   - Do not alter global `arg` evaluation/simplification semantics.
   - Rely on existing downstream `Abs`/relational/Piecewise refinement to collapse `2*Abs(arg(a)) < pi` once `arg(a)` refines to `0` or `pi`.

4. Add or extend refine-focused tests, likely in `sympy/assumptions/tests/test_refine.py` and/or existing `test_arg` coverage:
   - `refine(arg(a), Q.positive(a)) == 0`
   - `refine(arg(a), Q.negative(a)) == pi`
   - Direct regression for the bug-condition path: `refine(2*Abs(arg(a)) < pi, Q.positive(a)) is S.true` (or equivalent exact boolean assertion used in the test suite).
   - If feasible, also assert the enclosing `Piecewise` from `Integral(sin(x)*exp(-a*x), (x, 0, oo)).doit()` collapses under `Q.positive(a)` to `1/(a**2 + 1)`.
   - Add a no-overreach case such as `refine(arg(a), Q.real(a))` remaining unchanged unless existing supported canonical behavior says otherwise.
   - Add an explicit zero-safety assertion if there is an established expectation for `refine(arg(a), Q.zero(a))`; otherwise avoid asserting a new value.

5. Regression-check targets based on the task metadata:
   - Primary fail-to-pass target: `test_arg`.
   - Ensure the change is not intended to disturb `test_Abs`, `test_pow1`, `test_pow2`, `test_exp`, `test_Piecewise`, `test_atan2`, `test_re`, `test_im`, `test_complex`, `test_sign`, `test_func_args`, `test_eval_refine`, and `test_refine_issue_12724`.

6. Patch shape:
   - Small, localized addition/update in `sympy/assumptions/refine.py` plus focused refine tests.
   - Match existing handler conventions and imports (`ask`, `Q`, `S`) rather than introducing broader symbolic changes.