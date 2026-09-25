1. Update the `IsNull` lookup implementation in `django/db/models/lookups.py`.
   - Prefer adding validation in `IsNull.get_prep_lookup()` or `process_rhs()` if that hook exists for this lookup path, so invalid RHS values fail early and consistently before compilation/join handling.
   - Enforce `type(self.rhs) is bool`.
   - Raise a targeted `ValueError('__isnull lookup value must be True or False.')` for anything else.
   - Do not rely on `isinstance(..., bool)`, because that would still admit `0`/`1` through Python’s `bool`/`int` subclassing.

2. Keep the change narrowly scoped to `IsNull`.
   - Do not change generic lookup coercion or broader NULL-handling behavior.
   - Treat `None` as invalid for `__isnull` specifically.
   - Preserve existing behavior for other lookups that intentionally support `None`, including `can_use_none_as_rhs=True` cases and `__exact=None` transform behavior.

3. Treat join behavior as a non-goal for code changes.
   - Do not plan any join-promotion or join-type logic edits absent source evidence.
   - The intended outcome is that invalid `__isnull` RHS values are rejected before join-planning paths matter.

4. Strengthen tests in `tests/lookup/tests.py` by separating validation from behavior.
   - Add distinct validation tests asserting the exact exception type/message for each invalid RHS category:
     - `field__isnull=1`
     - `field__isnull=0`
     - `field__isnull='true'`
     - `field__isnull='false'`
     - `field__isnull=None`
   - Add a separate regression test confirming valid `field__isnull=True` and `field__isnull=False` still return correct queryset results.
   - Add or preserve coverage that valid `__isnull` querysets still iterate normally, to align with the reported `test_iterator` regression target.

5. Regression checks to keep in mind.
   - Confirm the error message remains stable for `test_error_messages` expectations.
   - Confirm no behavior change for non-`isnull` lookups.
   - Confirm exact booleans still map to normal `IS NULL` / `IS NOT NULL` query behavior.
   - Confirm the distinction is explicit in tests: `None` is now invalid for `__isnull`, even though `None` may remain valid elsewhere.