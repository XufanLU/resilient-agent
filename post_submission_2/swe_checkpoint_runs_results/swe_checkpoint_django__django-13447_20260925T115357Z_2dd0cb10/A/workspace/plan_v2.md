1. In `django/contrib/admin/sites.py`, split the change into two phases.

Phase (a): add the public API without changing behavior.
- Add `AdminSite.get_app_list(self, request, app_label=None)`.
- Implement it as a thin wrapper over existing logic, not a new code path: preserve `_build_app_dict(request, label=None)` semantics and have `get_app_list()` delegate to that logic, then return the same sorted list structure currently used by admin views/templates.
- Keep `_build_app_dict()` intact for compatibility with any internal callers.

Phase (b): only after parity is established, update callers conservatively.
- Switch `index()` and `app_index()` to use `get_app_list()` if the returned structure is confirmed to be identical to current expectations.
- Treat `each_context()` more carefully: only switch it to `get_app_list()` if that produces byte-for-byte equivalent `available_apps` structure apart from the new additive `model` key. Otherwise leave its current call path and just ensure the underlying entries are enriched.

2. Add the model class to each model entry at the existing construction point.
- In `_build_app_dict()` where each model dictionary is assembled, add `"model": model` (the actual model class object).
- Preserve all existing keys and values (`name`, `object_name`, `perms`, `admin_url`, `add_url`, etc.).
- Do not change permission filtering, app inclusion logic, or URL population behavior.

3. Preserve sorting and shape contracts exactly.
- Ensure `get_app_list()` returns apps in the same order as before.
- Ensure each app’s `models` list remains in the same order as before.
- For `get_app_list(request, app_label=...)`, mirror current `app_index()`/label-filtered behavior exactly, including error/empty handling as already implemented around `_build_app_dict()`.

4. Targeted regression coverage in `tests/admin_views/test_adminsite.py`.
- Update `SiteEachContextTest.test_available_apps` to assert the additive `model` key is present on model entries in `available_apps`.
- In that same test (or a nearby focused one), assert app order and model order are unchanged, not just that `model` exists.
- Add a dedicated test for `AdminSite.get_app_list(request)` verifying it returns the same app/model structure as current admin usage, plus the new `model` key.
- Add a dedicated test for `AdminSite.get_app_list(request, app_label=...)` to cover the new public parameter and the behavior relied on by `app_index()`.
- Keep the test plan additive: prioritize the known failing `test_available_apps`, and add `get_app_list()` coverage as regression protection rather than implying broader verified behavior.

5. Regression checks to keep in mind while implementing.
- Do not alter `_build_app_dict(request, label=None)` semantics during the first refactor.
- Do not replace model classes with strings or serialized identifiers.
- Avoid any template changes; the new key should be purely additive.
- Watch the pass-to-pass admin-site tests listed in the issue, especially `test_each_context` and action-related tests, since they depend on context stability rather than the new API.