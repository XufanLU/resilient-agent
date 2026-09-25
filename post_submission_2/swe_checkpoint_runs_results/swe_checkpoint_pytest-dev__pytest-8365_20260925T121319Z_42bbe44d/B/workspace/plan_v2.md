1. Inspect the existing failing test `testing/test_tmpdir.py::test_tmp_path_factory_handles_invalid_dir_characters` first and copy its exact expected transformed directory name.
   - Do not invent a sanitization convention if the test already encodes one.
   - Pay attention to whether repeated invalid characters are expected to collapse or remain repeated.

2. Update `_pytest/tmpdir.py` where the default per-user temp root is computed.
   - Introduce a small helper, e.g. `_sanitize_username_for_path(name: str) -> str`.
   - Use it only for the final username/path-component interpolation that produces something like `pytest-of-<sanitized_user>`.
   - Keep the rest of tmpdir/tmp_path_factory logic unchanged.

3. Implement sanitization in that helper to match the test expectation exactly.
   - At minimum handle path separators (`/`, `\\`, plus `os.sep`/`os.altsep` as relevant) so the username remains a single path component.
   - Also cover Windows-invalid filename characters if that aligns with the existing test expectation.
   - If replacing character-by-character would create duplicated separators like `contoso--john`, either normalize runs in the helper or leave them intact only if the test clearly expects that behavior.

4. Preserve current fallback behavior.
   - If username lookup already falls back through existing code paths, keep that untouched.
   - Only sanitize the successful username string before path construction.
   - If sanitization yields an empty or effectively unusable component, fall back to the existing generic token or a minimal safe fallback used by nearby code, rather than producing an empty directory name.

5. Extend tests in `testing/test_tmpdir.py` alongside the existing failing test.
   - Keep/adjust the Windows-domain case using `contoso\\john_doe`, asserting basetemp creation succeeds.
   - Assert the computed basetemp stays under the system temp root and that the `pytest-of-...` portion remains a single path component, guarding against accidental separator injection.
   - Add an edge-case test where the mocked username sanitizes to empty or all punctuation/invalid characters, verifying fallback behavior rather than failure.
   - If practical within current test patterns, test the helper indirectly through basetemp computation rather than broad tmpdir behavior changes.

6. Regression checks to target conceptually.
   - Existing passing tests around `mktemp` relative-path validation must remain unchanged.
   - Numbered-dir creation/cleanup behavior should be unaffected.
   - UID/user fallback tests (`test_get_user_uid_not_found`, `test_tmpdir_fallback_uid_not_found`, related tox-env fallback) should continue to behave exactly as before.
   - No sanitization should be applied to arbitrary user-supplied `mktemp` names; scope remains limited to the username-derived basetemp component.