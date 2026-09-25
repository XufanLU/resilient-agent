1. Inspect the refine dispatcher and existing handler naming in `sympy/assumptions/refine.py`.
- Confirm how function-specific handlers are registered/named (`refine_abs` vs `refine_Abs`, etc.).
- Check whether recursive refinement of subexpressions and `Piecewise` branch conditions already happens before planning any `Piecewise` changes.
- Review existing handlers for nearby functions (`Abs`, `sign`, `re`, `im`, `atan2`) to match style and avoid broad assumptions logic.

2. Add a minimal `arg`-specific refinement rule.
- In the existing dispatch pattern, add the `arg` handler in `sympy/assumptions/refine.py`.
- Implement only:
  - `refine(arg(x), Q.positive(x)) -> 0`
  - `refine(arg(x), Q.negative(x)) -> pi`
- Do not initially add rewrites for `Q.zero`, `Q.nonnegative`, `Q.nonpositive`, `Q.real`, or `Q.complex`.
- Keep the rule local to `arg`; do not add broader “real implies simplified argument” logic elsewhere.

3. Rely on existing recursive refinement first.
- After `arg(a)` refines, `Abs(arg(a))` should evaluate through normal expression refinement/evaluation, and `2*Abs(arg(a)) < pi` should then simplify accordingly.
- Treat any `Piecewise` work as a fallback only if inspection shows branch-condition refinement is not already performed.

4. Add focused regression tests, likely in the assumptions/refine test module.
Core direct tests:
- `refine(arg(a), Q.positive(a)) == 0`
- `refine(arg(a), Q.negative(a)) == pi`
- `refine(arg(a), Q.real(a)) == arg(a)`
- `refine(arg(a), Q.complex(a)) == arg(a)`
End-to-end regression from the report:
- Build the reported `Piecewise` result (or the integral expression that produces it) and assert that refining under `Q.positive(a)` collapses to `1/(a**2 + 1)` if branch-condition refinement is already working.

5. Regression checks to keep in mind while implementing.
- Preserve existing behavior for the listed pass-to-pass areas: `Abs`, `pow`, `exp`, `Piecewise`, `atan2`, `re`, `im`, `complex`, `sign`, `func_args`, `eval_refine`, and `test_refine_issue_12724`.
- Avoid over-eager simplification for generic complex or merely real symbols.
- Preserve principal-argument convention for negative reals (`pi`, not `-pi`).

6. Next execution step.
- Inspect `sympy/assumptions/refine.py` dispatch and existing handlers, then add the minimal `arg` rule plus focused regression tests for positive/negative real assumptions and the reported `Piecewise` simplification. Since repository contents/tests are unavailable here, this plan does not assume verification has been performed.