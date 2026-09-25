1. In `_pytest/tmpdir.py` (or the module that computes the default temp root), find the helper/path construction that produces the per-user directory name `pytest-of-<user>`.
2. Add a small dedicated helper, e.g. `_sanitize_username_for_basetemp(user: str) -> str`, used only when forming that `pytest-of-<user>` component.
   - Call it after the existing username resolution/fallback helper has already returned the effective username.
   - Replace path separators (`os.sep` and `os.altsep` when present) and Windows-invalid filename characters (`\\ / : * ? " < > |`) with a safe delimiter such as `-` or `_`.
   - Collapse or otherwise handle degenerate output so the sanitized token cannot be empty; if the username sanitizes to nothing, fall back to a deterministic token like `unknown`.
   - Keep the helper scoped to the default basetemp naming path only; do not change `mktemp` validation or custom `--basetemp` behavior.
3. Update tests in `testing/test_tmpdir.py`.
   - Add a focused unit-style test for the sanitization helper with parametrized bad usernames, including representative cases like:
     - `contoso\\john_doe`
     - `user:name`
     - `user?name`
     - a string made only of invalid characters, asserting fallback to the safe default token
   - Add/adjust the regression around tempdir creation so monkeypatching the username source to `contoso\\john_doe` yields a basetemp whose parent user component is a single path segment such as `pytest-of-contoso-john_doe` or `pytest-of-contoso-john_doe`/`pytest-of-contoso_john_doe` depending on chosen replacement policy, and that `mktemp` succeeds.
   - Assert concretely that the resulting path does not split into `pytest-of-contoso/john_doe`; the sanitized value should remain one directory component.
4. Preserve and mentally re-check nearby fallback coverage:
   - `test_tmpdir_fallback_tox_env`
   - `test_tmpdir_fallback_uid_not_found`
   These should keep validating fallback selection, with sanitization applied only to the final returned username.
5. Regression checks to keep in mind while implementing:
   - No behavior change for ordinary usernames.
   - Existing custom `--basetemp`, numbered-dir creation/cleanup, and relative-path rejection tests should remain unaffected.
   - The sanitized directory name should stay deterministic so repeated runs target the same `pytest-of-<sanitized-user>` root for cleanup/retention logic.