1. Update `django/contrib/admin/sites.py`:
- Introduce a public `get_app_list(self, request, app_label=None)` method as the supported wrapper around the existing app-dictionary construction logic.
- Have `index()`, `app_index()`, and `each_context()` call `get_app_list()` instead of duplicating/private access patterns.
- Keep `_build_app_dict()` as an internal helper if needed for compatibility, but move the public contract to `get_app_list()` rather than exposing the raw dict builder directly.

2. Extend the app/model metadata built for admin context:
- In the code path that assembles each model entry inside `_build_app_dict()` (or the refactored helper), add a `model` field containing the actual model class object.
- Preserve existing keys (`name`, `object_name`, `perms`, `admin_url`, `add_url`, etc.) so existing admin templates and action tests remain unaffected.

3. Ensure output shape remains stable:
- `get_app_list()` should continue returning the sorted list structure currently consumed by templates and tests.
- For `app_index(app_label)`, filter by app label while keeping the added `model` key in each model dict.
- Verify `each_context()` still sets `available_apps`, `site_header`, `site_title`, `site_url`, and related keys unchanged apart from the enriched model entries.

4. Likely regression coverage to add/update in `tests/admin_views/test_adminsite.py`:
- Update/confirm `SiteEachContextTest.test_available_apps` asserts each model entry includes its model class.
- Add a targeted test for `AdminSite.get_app_list()` returning model entries with `model` set correctly.
- Keep existing context and action tests passing by not changing ordering, permissions filtering, or disabled-action behavior.

5. Implementation cautions:
- Do not serialize the class name string; attach the actual class object.
- Avoid changing template expectations in a way that requires template edits; the new key should be additive.
- Preserve sorting of apps/models exactly as before to avoid unrelated test breakage.