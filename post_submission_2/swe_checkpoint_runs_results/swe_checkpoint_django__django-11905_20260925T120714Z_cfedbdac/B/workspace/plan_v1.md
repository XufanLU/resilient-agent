1. Inspect the `IsNull` lookup class in `django/db/models/lookups.py`.
   - Look for `as_sql()`, `get_prep_lookup()`, or constructor logic that currently accepts any RHS and treats it by truthiness.
   - Identify whether the lookup is registered as `lookup_name = 'isnull'` and where its RHS is normalized.

2. Tighten RHS validation specifically for `__isnull`.
   - Add an explicit type check requiring `isinstance(rhs, bool)`.
   - Reject non-boolean values early, ideally in `get_prep_lookup()` or another lookup-preparation hook so invalid queries fail consistently before SQL generation/iteration.
   - Raise a clear exception message such as `The __isnull lookup requires a boolean value.`
   - Be careful not to treat integers as acceptable booleans just because `bool` subclasses `int`; a strict `isinstance(rhs, bool)` check still excludes plain `0`/`1` while accepting only `True`/`False`.

3. Ensure the SQL path continues to use the validated boolean.
   - After validation, `as_sql()` should keep its existing `IS NULL` / `IS NOT NULL` behavior based on `True` vs `False` only.
   - Avoid changing join-promotion logic except insofar as invalid RHS can no longer reach it.

4. Add/update tests in `lookup/tests.py`.
   - Implement/adjust `test_isnull_non_boolean_value` to assert that values like `1`, `0`, `'true'`, `'false'`, `None`, or other non-bools raise the expected exception.
   - Verify both `.filter(...__isnull=bad_value)` and actual evaluation if necessary, depending on when validation occurs.
   - Review `test_iterator` expectations: if iterator evaluation is where the exception should surface, align the validation point with Django’s existing lookup error timing. If the test is unrelated, make sure the change doesn’t alter normal iteration for valid boolean `isnull` filters.

5. Regression checks to keep in mind while patching.
   - `field__isnull=True` and `field__isnull=False` still compile and return expected rows.
   - Existing `None` semantics for `__exact=None` and custom lookups with `can_use_none_as_rhs=True` remain untouched.
   - No regression in queryset iteration, especially for lookups created before evaluation.
   - Error type/message should be consistent with Django’s existing invalid lookup validation patterns.

Likely files:
- `django/db/models/lookups.py` for the actual fix.
- `tests/lookup/tests.py` for regression coverage.
- Possibly related query-building code only if validation currently happens outside the lookup class.