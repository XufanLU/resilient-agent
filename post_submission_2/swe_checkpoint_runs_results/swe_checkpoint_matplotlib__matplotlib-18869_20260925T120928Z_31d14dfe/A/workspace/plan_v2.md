1. Inspect `lib/matplotlib/tests/test_matplotlib.py` and `lib/matplotlib/__init__.py` before editing to answer two concrete questions:
   - Do tests/assertions refer to `_parse_to_version_info`, `__version_info__`, or `version_info`?
   - Does `__init__.py` define `__all__`, and if so, should any new name be excluded or included intentionally?

2. In `lib/matplotlib/__init__.py`, add a small internal helper named `_parse_to_version_info` unless inspection proves the tests expect a different exact name. Implement it with one anchored regex covering only the known required forms:
   - `X.Y.Z`
   - `X.Y.ZrcN`
   - `X.Y.Z.devN` with optional `+local`
   - `X.Y.Z.postN` with optional `+local`
   Suggested capture structure: `major`, `minor`, `micro`, optional stage `(rc|dev|post)`, optional stage number, optional `+...` local suffix ignored in the result.

3. Define exact parsing behavior narrowly and explicitly:
   - `3.5.0` -> `(3, 5, 0)`
   - `3.5.0rc2` -> `(3, 5, 0, 'rc', 2)`
   - `3.5.0.dev820+g6768ef8c4c` -> `(3, 5, 0, 'dev', 820)`
   - `3.5.0.post820+g6768ef8c4c` -> `(3, 5, 0, 'post', 820)`
   - Ignore any `+local` metadata when present.
   - Reject unsupported strings with `ValueError` unless the inspected tests/code show a different expectation.
   - Do not broaden scope to forms like `X.Y` or other PEP 440 variants unless existing repository context clearly requires them.

4. Keep the helper module-visible in `matplotlib.__init__`, since the failing test names strongly suggest direct testing of `_parse_to_version_info`. Do not add a new public `version_info` or `__version_info__` attribute unless step 1 confirms the repository already expects it.

5. If inspection shows an existing top-level parsed-version attribute is also expected, derive it from `__version__` immediately after version initialization using the same helper, but keep this secondary to the helper itself.

6. Keep documentation churn minimal. Only add a short inline comment near the helper if needed to clarify supported version formats; avoid broader doc updates unless `__init__.py` already documents version exports.

7. Follow-up validation once code is available:
   - Confirm the four listed `test_parse_to_version_info[...]` cases align with the helper name and tuple outputs.
   - Re-check the listed pass-to-pass import tests conceptually for risk, since changes are in `__init__.py`.
   - If `__all__` exists, verify the helper/attribute export decision is explicit and consistent with the test expectations.