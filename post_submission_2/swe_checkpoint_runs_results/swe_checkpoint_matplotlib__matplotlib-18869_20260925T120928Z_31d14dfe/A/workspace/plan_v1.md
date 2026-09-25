1. Inspect `lib/matplotlib/__init__.py` for where `__version__` is imported/set and what names are exported.
2. Add a small internal parser near the version definition, e.g. `_parse_to_version_info(version_str)`, that handles the forms covered by the issue/tests:
   - `X.Y.Z` -> `(X, Y, Z)`
   - `X.Y.ZrcN` -> `(X, Y, Z, 'rc', N)`
   - `X.Y.Z.devN+...` -> `(X, Y, Z, 'dev', N)`
   - `X.Y.Z.postN+...` -> `(X, Y, Z, 'post', N)`
   Ignore local version metadata after `+`.
3. Expose the parsed result at top level immediately after `__version__` is defined, using the exact attribute name expected by tests/documentation (most likely `__version_info__` if tests reference a parser helper, otherwise `version_info`; if both are reasonable, prefer the public `__version_info__`/`version_info` choice already implied by surrounding code style).
4. Keep the representation easy to compare lexicographically as requested by the issue; avoid returning packaging objects or `LooseVersion` unless existing code already depends on them.
5. If the tests reference the helper directly (`test_parse_to_version_info` suggests they might), make `_parse_to_version_info` module-visible in `matplotlib.__init__`.
6. Update any top-level docs/comments in `__init__.py` if needed to explain the tuple shape for prerelease/dev/postrelease versions.
7. Regression checks to run once code is available:
   - The four new `test_parse_to_version_info[...]` cases.
   - Existing import-related tests listed in pass-to-pass to ensure adding the attribute does not affect import behavior.
   - Optionally, add/verify one malformed-version behavior test if the helper is public (e.g. raises `ValueError` on unsupported strings), but only if consistent with existing test style.