1. Update `django/forms/formsets.py` in `BaseFormSet.empty_form` only.
   - Build `kwargs` from a shallow copy of `self.get_form_kwargs(None)`.
   - Remove any user-provided `empty_permitted` via `kwargs.pop('empty_permitted', None)`.
   - Instantiate the empty form with the formset-controlled `empty_permitted=True` plus the remaining kwargs.
   - Do not change `_construct_form()` or normal form construction semantics.

2. Keep the behavioral boundary explicit.
   - `empty_form` must ignore caller-provided `form_kwargs['empty_permitted']`.
   - Non-empty forms constructed through the normal formset path should continue to honor `form_kwargs['empty_permitted']` if that is current behavior.

3. Add regression coverage in `tests/forms_tests/tests/test_formsets.py` for both `FormsFormsetTestCase` and `Jinja2FormsFormsetTestCase`.
   - For `form_kwargs={'empty_permitted': True}` and `False`, assert that:
     - `formset.empty_form` is accessible,
     - `str(formset.empty_form)` renders without error,
     - and `str(formset)` (or equivalent template/render path) also renders without error, since the bug report is about rendering crashes.
   - Assert `formset.empty_form.empty_permitted is True` to document intended empty-form behavior.
   - Add one focused non-regression test showing an ordinary constructed form still reflects `form_kwargs['empty_permitted']`, to confirm the fix is scoped to `empty_form`.

4. Regression checks to target.
   - Existing `test_form_kwargs_empty_form` behavior should remain intact.
   - Default and Jinja2 rendering paths should both cover `empty_form` and whole-formset rendering.
   - Avoid asserting a specific pre-fix exception type in the new test; assert successful access/rendering after the fix instead.