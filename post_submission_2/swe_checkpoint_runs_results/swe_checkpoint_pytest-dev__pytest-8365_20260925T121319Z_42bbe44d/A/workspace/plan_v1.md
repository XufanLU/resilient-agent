1. Locate the username-to-basetemp logic, likely in `_pytest/tmpdir.py`, especially where `getpass.getuser()` is used to form the default temp root.
2. Introduce a small sanitization step for the username before embedding it in a directory name. The safest patch is to normalize any path-separator or filesystem-illegal characters to a benign replacement (for example `-` or `_`) rather than letting them create nested paths or invalid names.
   - At minimum handle both `os.sep`/`os.altsep` and Windows-illegal filename characters such as `\\ / : * ? " < > |`.
   - Preserve existing behavior for ordinary usernames so current tempdir naming stays stable for most users.
3. Keep the sanitization narrowly scoped to the generated default temp directory name; do not alter `mktemp` validation behavior for user-supplied relative names, since many existing tests cover that separately.
4. Add/adjust regression tests in `testing/test_tmpdir.py`:
   - Cover the reported case by monkeypatching the username source to return `contoso\\john_doe` and asserting `tmp_path_factory` can create its basetemp/mktemp successfully.
   - Prefer asserting success and that the resulting basetemp path does not contain unintended nested components from the raw username.
   - If there is already a helper test around username fallback/sanitization, extend it instead of duplicating setup.
5. Regression checks to keep in mind while implementing:
   - Existing tests around custom `--basetemp`, numbered dir creation, cleanup, and relative-path rejection should remain unchanged.
   - Username fallback tests such as `test_tmpdir_fallback_tox_env` / `test_tmpdir_fallback_uid_not_found` should still pass, so sanitize after fallback resolution, not before the fallback logic itself.
   - Ensure the sanitized name is still deterministic so cleanup of `pytest-of-<user>` continues to work consistently.