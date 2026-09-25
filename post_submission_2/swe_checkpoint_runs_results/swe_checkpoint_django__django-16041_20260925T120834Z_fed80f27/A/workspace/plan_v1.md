1. Inspect `django/forms/formsets.py`, especially `BaseFormSet.empty_form` and `get_form_kwargs()` usage.
2. Update `empty_form` construction to strip or override any user-supplied `empty_permitted` before instantiating the form. A safe pattern is:
   - start from `self.get_form_kwargs(None)` (copy if needed),
   - remove `empty_permitted` from that dict if present,
   - instantiate the form with the formset-controlled `empty_permitted=True`.
   This keeps existing behavior for normal forms while making `empty_form` immune to conflicting `form_kwargs`.
3. Avoid changing behavior for regular form instances created by `_construct_form()`; only `empty_form` should ignore the passed value.
4. Add regression tests in `tests/forms_tests/tests/test_formsets.py` for both standard and Jinja2 formset test classes, matching the reported failures:
   - construct a formset with `form_kwargs={'empty_permitted': True}` and access/render `empty_form` without error;
   - repeat with `False`;
   - optionally assert `formset.empty_form.empty_permitted is True` to document the intended behavior.
5. Regression checks to keep in mind:
   - existing `test_form_kwargs_empty_form` coverage should still pass;
   - ensure no impact on normal `form_kwargs` propagation to non-empty forms;
   - ensure rendering `{{ formset }}` and `{{ formset.empty_form }}` still works in both default and Jinja2 renderers.