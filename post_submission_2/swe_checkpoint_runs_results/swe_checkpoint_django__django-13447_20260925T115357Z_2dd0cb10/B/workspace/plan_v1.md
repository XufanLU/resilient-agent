1. Update `django/contrib/admin/sites.py`:
   - In `_build_app_dict()`, when constructing each model entry, add the actual model class, e.g. `'model': model`.
   - Keep all existing keys and sort behavior intact.

2. Add a public API for app list retrieval:
   - Preferred: add `AdminSite.get_app_list(request, app_label=None)` that calls `_build_app_dict()`, performs the current app/model sorting, and returns the list structure used by templates.
   - Refactor `index()` and `app_index()` to use `get_app_list()` instead of duplicating/private access.
   - Leave `_build_app_dict()` in place as an internal helper to minimize risk.

3. Update context assembly:
   - Ensure `each_context()` and any admin views that expose `available_apps`/`app_list` use `get_app_list()` or otherwise return structures containing the new `model` key.
   - Be careful not to remove or rename existing context keys.

4. Regression checks to target:
   - `admin_views.test_adminsite.SiteEachContextTest.test_available_apps` should now see model classes in the app list.
   - Existing `each_context` tests should still pass, including script-name/site-url behavior.
   - Action-related tests should remain unaffected since this change is isolated to app list generation.
   - Confirm app/model ordering remains identical to current behavior.

5. Implementation cautions:
   - If model dicts are ever consumed in templates, adding `model` should be non-breaking.
   - If documentation or release notes are expected for a new public method, add a note describing `AdminSite.get_app_list()` and the presence of `model` in returned model dictionaries.