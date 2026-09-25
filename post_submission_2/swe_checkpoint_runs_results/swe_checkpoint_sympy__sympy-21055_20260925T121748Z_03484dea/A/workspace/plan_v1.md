1. Inspect likely refine dispatch locations:
- `sympy/assumptions/refine.py`
- any existing `refine_Abs`, `refine_Pow`, `refine_exp`, `refine_sign`, or function-specific handlers
- `arg` definition in something like `sympy/functions/elementary/complexes.py`

2. Add a function-specific refine rule for `arg`.
Likely behavior:
- under `Q.positive(x)`: `arg(x) -> 0`
- under `Q.negative(x)`: `arg(x) -> pi`
- under `Q.zero(x)`: preserve `arg(0)` semantics used by SymPy; only simplify if existing conventions clearly define it
- under `Q.real(x)` alone: do not force a single value, since it could be `0` or `pi` depending on sign
- possibly under `Q.nonnegative(x)` / `Q.nonpositive(x)`: simplify only if SymPy’s `arg` conventions make this unambiguous and existing refine style accepts boundary-sensitive rewrites

3. Ensure the handler composes with existing refinement:
- `refine(Abs(arg(a)), Q.positive(a))` should become `0`
- inequalities such as `2*Abs(arg(a)) < pi` should then simplify through normal recursive refinement/evaluation, making the `Piecewise` condition become `True`
- verify whether `refine(Piecewise(...), assumptions)` already refines branch conditions; if not, inspect `refine_Piecewise` behavior as a secondary likely location

4. Add regression tests in the refine/assumptions test module, likely near existing tests for `Abs`, `sign`, `re`, `im`, `atan2`, or `Piecewise`:
- `refine(arg(a), Q.positive(a)) == 0`
- `refine(arg(a), Q.negative(a)) == pi`
- `refine(arg(a), Q.real(a))` remains unchanged
- refinement of the reported integral result under `Q.positive(a)` yields `1/(a**2 + 1)` rather than the original `Piecewise`
- keep coverage for existing pass-to-pass areas (`Abs`, `Piecewise`, `re`, `im`, `complex`, `sign`) to avoid regressions in related refine logic

5. Regression checks to consider conceptually:
- no over-eager simplification for generic complex symbols
- no incorrect rewrite for purely imaginary numbers or nonzero complex assumptions
- preserve existing principal-argument conventions (`arg(-x)` for positive `x` should land at `pi`, not `-pi`)
- confirm that any change does not interfere with `test_refine_issue_12724` or other branch-condition refinement behavior.