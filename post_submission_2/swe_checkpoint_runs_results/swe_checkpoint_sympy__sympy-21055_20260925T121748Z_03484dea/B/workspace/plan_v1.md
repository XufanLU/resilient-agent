1. Inspect `sympy/assumptions/refine.py` for existing `refine_*` handlers and confirm whether `arg` has no handler or an incomplete one.
2. Add/extend `refine_arg(expr, assumptions)` logic along these lines:
   - Let `z = expr.args[0]`.
   - If `ask(Q.positive(z), assumptions)` is True: return `S.Zero`.
   - If `ask(Q.negative(z), assumptions)` is True: return `S.Pi`.
   - Optionally, if `ask(Q.zero(z), assumptions)` is True, preserve existing behavior unless SymPy already defines a canonical `arg(0)` result in refinement paths; avoid changing semantics unnecessarily.
   - Otherwise return the original expression.
3. Register the handler so `refine(arg(a), ...)` uses it.
4. Ensure imports/constants needed by the handler are present (`ask`, `Q`, `S`, maybe `pi` via `S.Pi`).
5. Add regression tests covering the issue directly:
   - `refine(arg(a), Q.positive(a)) == 0`
   - `refine(arg(a), Q.negative(a)) == pi`
   - The reported integral case: refining `Integral(sin(x)*exp(-a*x),(x,0,oo)).doit()` under `Q.positive(a)` gives `1/(a**2 + 1)`.
6. Add safety tests to avoid regressions in related behavior:
   - Existing `Abs` refine behavior remains unchanged.
   - A case with no useful assumption, e.g. `refine(arg(a), Q.real(a))`, should only be changed if there is already a supported canonical rule; otherwise leave unchanged.
7. Regression checks to target based on the provided suite:
   - `test_arg` should pass.
   - Verify no behavior changes are intended for `test_Abs`, `test_pow1`, `test_pow2`, `test_exp`, `test_Piecewise`, `test_atan2`, `test_re`, `test_im`, `test_complex`, `test_sign`, `test_func_args`, `test_eval_refine`, and `test_refine_issue_12724`.

Suggested patch shape:
- Small, localized refine-handler addition rather than changing `arg` evaluation itself.
- Keep the fix assumption-driven so it only applies during `refine()` and does not alter general symbolic simplification semantics.