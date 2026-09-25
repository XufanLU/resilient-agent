1. Inspect the `IsNull` lookup implementation in `django/db/models/lookups.py`.
   - Find where SQL is generated (`as_sql()` or equivalent) and where RHS is prepared.
   - Add strict type validation so only `True` or `False` are accepted.
   - Reject non-boolean RHS values before SQL compilation, e.g. raise `ValueError('__isnull lookup value must be True or False.')`.
   - Use `type(self.rhs) is bool` or `isinstance(..., bool)` carefully; exact intent is to reject integers like `0/1`, so exact-bool checking is safer.

2. Keep the change isolated to `IsNull`.
   - Do not alter generic lookup coercion.
   - Preserve existing support for `None` in other lookups that explicitly allow it (`can_use_none_as_rhs=True`).
   - Preserve transform behavior for `__exact=None` and existing null-related query semantics.

3. Check likely interaction points with join promotion.
   - If query-building code special-cases `isnull`, ensure it only sees validated boolean values.
   - Avoid changing INNER/OUTER join logic except insofar as invalid RHS no longer reaches it.

4. Add/adjust regression tests in `tests/lookup/tests.py`.
   - Add a test asserting `field__isnull=1`, `0`, `'true'`, `'false'`, `None`, or other non-bool values raise the expected exception.
   - Ensure the valid cases `field__isnull=True` and `field__isnull=False` still work.
   - If `test_iterator` covers queryset iteration over `isnull` filters, make sure there is explicit coverage that valid `__isnull` queries still iterate normally.

5. Regression checks to keep in mind.
   - Existing lookup tests listed as pass-to-pass should remain unaffected, especially `test_none`, `Transforms are used for __exact=None.`, and `Lookup.can_use_none_as_rhs=True allows None as a lookup value.`
   - Confirm no behavioral change for non-`isnull` lookups.
   - Confirm exact booleans still compile to `IS NULL` / `IS NOT NULL` SQL and queryset iteration remains intact.