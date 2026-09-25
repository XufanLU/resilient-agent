1. Trace the `__isnull` lookup lifecycle before choosing the patch hook.
   - Inspect `IsNull` in `django/db/models/lookups.py` and follow how `field__isnull=...` is turned into a lookup: lookup instantiation, RHS prep/normalization, query building, and SQL compilation.
   - Check whether current validation happens during queryset construction, query compilation (`str(qs.query)`), or evaluation/iteration.
   - Compare that timing to the failing `test_iterator` so the fix matches Django’s existing lazy/eager error behavior instead of moving exceptions arbitrarily.

2. Inspect existing exception patterns nearby.
   - Review neighboring lookup classes and tests in `tests/lookup/tests.py` for invalid RHS handling.
   - Reuse the same exception class Django already uses in comparable invalid-lookup situations if possible, and align wording with existing conventions rather than inventing a one-off message.
   - Confirm whether `ValueError` is the right outcome or whether another established exception type is expected by adjacent tests.

3. Implement strict RHS validation for `IsNull` at the confirmed correct stage.
   - Add an explicit check that only real booleans are accepted (`isinstance(rhs, bool)` if that matches Django style at the chosen hook).
   - Note this is intentionally strict: it rejects `0`/`1`, strings, `None`, and boolean-like custom objects that merely define truthiness via `__bool__`.
   - Place the check where step 1 shows it belongs: either during lookup preparation/construction if Django validates early, or in the SQL/evaluation path if `isnull` validation is currently lazy.

4. Preserve valid `isnull` behavior.
   - Keep existing SQL generation for `True` => `IS NULL` and `False` => `IS NOT NULL`.
   - Ensure valid boolean RHS still feeds whatever join-promotion logic exists today unchanged.
   - Invalid non-boolean RHS should fail before any `isnull`-specific join promotion can affect query shape.

5. Add focused regression coverage in `tests/lookup/tests.py`.
   - Update/add `test_isnull_non_boolean_value` to cover invalid RHS values such as `1`, `0`, `'true'`, `'false'`, `None`, and a custom truthy object implementing `__bool__`.
   - Split expectations based on actual validation timing discovered in step 1:
     * if validation is early, assert `.filter(...__isnull=bad_value)` raises;
     * if validation remains lazy, assert `str(qs.query)` and/or iteration raises, matching `test_iterator` expectations.
   - Add/retain positive checks that `__isnull=True` and `__isnull=False` still work normally.
   - Include a join-oriented regression check: valid boolean `isnull` filters must preserve current INNER/OUTER JOIN handling, while invalid RHS must error before that distinction becomes relevant.

6. Watch surrounding pass-to-pass behavior.
   - Confirm the change is isolated to `__isnull` and does not affect `__exact=None`, transforms using `__exact=None`, or lookups with `can_use_none_as_rhs=True`.
   - Avoid regressions in generic queryset iteration and lookup preparation code that could explain the existing `test_iterator` failure.

Likely files:
- `django/db/models/lookups.py` for `IsNull` validation.
- `tests/lookup/tests.py` for regression coverage.
- Possibly query-building code under `django/db/models/sql/` only if the trace shows `isnull` RHS handling occurs outside the lookup class.