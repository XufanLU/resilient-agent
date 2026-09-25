1. Inspect `rc_context()` in `lib/matplotlib/__init__.py`.
- Check whether it snapshots and restores the `backend` rcParam unconditionally.
- Compare behavior when backend resolution happens inside the context (e.g. first `plt.figure()` under `rc_context`) versus outside.
- Determine whether restore logic writes back the backend sentinel / old config value in a way that makes pyplot think no backend is active or that a backend change is required.

2. Inspect `get_backend()` implementation and any pyplot/backend-resolution path it triggers.
- Verify whether `matplotlib.get_backend()` is meant to be read-only.
- Trace whether it consults `rcParams['backend']`, auto-resolves a backend, or calls into pyplot/backend-switching code.
- Identify where a backend switch clears `Gcf.figs` or rebinds pyplot globals.

3. Patch strategy: prevent `rc_context()` from restoring backend state in a way that invalidates an already-selected live backend.
- Likely fix: when `rc_context()` exits, preserve the currently selected backend if backend resolution occurred during the context, rather than blindly restoring the prior `backend` rcParam value/sentinel.
- Alternative acceptable fix: make `get_backend()` return the active backend without causing backend switching/reinitialization once pyplot has an active backend.
- Prefer the smallest change that keeps `get_backend()` side-effect free and avoids backend resets with existing figures.

4. Likely concrete edit points.
- In `lib/matplotlib/__init__.py`, adjust `rc_context()` restoration logic so backend-related state is excluded or specially handled.
- If needed, in `lib/matplotlib/pyplot.py`, guard lazy backend setup so `get_backend()` does not call `switch_backend()` when an active backend module/manager already exists.

5. Add/adjust regression coverage in `lib/matplotlib/tests/test_rcparams.py`.
- Ensure the existing failing test `test_no_backend_reset_rccontext` captures the reported sequence:
  - create first figure inside `rc_context()`
  - record `Gcf.figs`
  - call `matplotlib.get_backend()`
  - assert `Gcf.figs` unchanged
  - optionally assert `plt.close(fig)` still works.
- Consider adding a variant with a pre-existing figure outside the context to document the non-regression case already mentioned in the report.
- Consider a variant covering `plt.ion()` if the existing test matrix needs to protect that path, though this may be optional if one focused regression test suffices.

6. Regression checks to keep in mind.
- Existing rcParams tests listed in the task should still pass, especially:
  - `test_rcparams_reset_after_fail`
  - `test_backend_fallback_headless`
  - `test_rcparams`, `test_RcParams_class`, and deprecation tests.
- Watch for unintended behavior changes in legitimate backend switching APIs; the fix should only stop accidental reset/reinit on context exit or backend querying, not prevent explicit backend changes.