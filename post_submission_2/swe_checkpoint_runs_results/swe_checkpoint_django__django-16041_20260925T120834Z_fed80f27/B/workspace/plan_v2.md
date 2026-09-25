1. Update `django/forms/formsets.py` in `BaseFormSet.empty_form`.
   - Take a copy of `self.get_form_kwargs(None)` before instantiating the form.
   - Remove `empty_permitted` from that copied dict with `pop('empty_permitted', None)`.
   - Instantiate the empty form with the sanitized kwargs plus the formset-controlled `empty_permitted=True`.
   - Add a short comment explaining that `empty_form` is always controlled by the formset and must not inherit caller-supplied `empty_permitted`.

2. Keep the change tightly scoped.
   - Do not alter `get_form_kwargs()` generally.
   - Do not refactor normal form construction paths.
   - Preserve existing behavior for non-`empty_form` code paths.

3. Add regression tests in `tests/forms_tests/tests/test_formsets.py`.
   - Extend both `FormsFormsetTestCase` and `Jinja2FormsFormsetTestCase` coverage.
   - For each renderer variant, create a formset with `form_kwargs={'empty_permitted': True}` and another with `form_kwargs={'empty_permitted': False}`.
   - Access `formset.empty_form` and assert `formset.empty_form.empty_permitted is True` in both cases.
   - Also exercise the reported crash path by rendering the empty form, e.g. `str(formset.empty_form)` or the equivalent renderer/template path used in that test class, so the test directly covers rendering rather than only construction/no-exception.

4. Regression checks to expect.
   - Existing `test_form_kwargs_empty_form` behavior should remain intact.
   - Standard and Jinja2 formset rendering should continue to work.
   - Management-form and general formset rendering tests already provide surrounding coverage, so no broader new tests are needed beyond the targeted empty-form conflict cases.