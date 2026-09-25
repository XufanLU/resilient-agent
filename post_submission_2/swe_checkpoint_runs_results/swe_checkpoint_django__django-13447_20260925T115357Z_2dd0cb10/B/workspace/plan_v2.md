1. Update `django/contrib/admin/sites.py` to separate responsibilities clearly.
   - Keep `_build_app_dict(request, app_label=None)` as the internal collector/filtering helper.
   - Ensure it continues to:
     - gather registered models,
     - apply existing permission checks,
     - omit apps with no visible models,
     - honor the `app_label` filter exactly as today.
   - When creating each model entry, add the raw model class as an additive field:
     - `'model': model`
   - Do not remove or rename any existing keys.
   - Do not make `_build_app_dict()` responsible for sorting; leave its output as an intermediate mapping/collection structure.

2. Add a new public API: `AdminSite.get_app_list(request, app_label=None)`.
   - Implement it as the single canonical source for template-facing app data.
   - It should:
     - call `_build_app_dict(request, app_label=app_label)`,
     - convert the intermediate data into the current list-of-app-dicts shape,
     - apply all current app/model sorting there, preserving existing ordering semantics.
   - API stability requirement:
     - return the same structure current templates expect,
     - with the only intentional additive change being `model` inside each model dict.

3. Refactor admin view/context code paths to use only `get_app_list()`.
   - `index()`:
     - populate its `app_list` context from `get_app_list(request)`.
   - `app_index()`:
     - populate its single-app `app_list` context from `get_app_list(request, app_label)`.
     - preserve current behavior when the filtered app is absent or has no visible models.
   - `each_context()`:
     - populate `available_apps` from `get_app_list(request)`.
   - Explicitly preserve context variable names:
     - `each_context()` continues exposing `available_apps`.
     - index/app-index views continue exposing `app_list` as expected.
   - This avoids leaving any caller on the old private/helper-derived structure.

4. Add/adjust tests in admin site/admin views coverage.
   - Add a direct test for `AdminSite.get_app_list()` to pin the new public API:
     - returns the expected list-of-app-dicts structure,
     - includes `model` in each model dict,
     - preserves existing keys/order.
   - Add a targeted regression for `get_app_list(request, app_label=...)`:
     - preserves current app-label filtering,
     - still omits an app when permission filtering leaves it with no visible models.
   - Keep/adjust context-facing tests to verify integration:
     - `SiteEachContextTest.test_available_apps` sees model classes in `available_apps`.
     - `test_each_context` and `test_each_context_site_url_with_script_name` remain unchanged in behavior.
   - Ensure pass-to-pass admin action tests remain unaffected, since they should not depend on app-list generation.

5. Implementation cautions.
   - Treat the new `model` entry as Python/template-facing data, not a serializable contract; avoid any unnecessary serialization assumptions.
   - Preserve non-breaking template behavior by keeping all existing keys and list ordering intact.
   - If this change warrants docs/release notes, mention the new public `AdminSite.get_app_list()` and that model dictionaries now include `model`.