1. Trace `get_backend()` end-to-end before changing behavior.
   - In `lib/matplotlib/__init__.py`, inspect the implementation of `matplotlib.get_backend()`.
   - Map exactly what it calls next: direct `rcParams` access, pyplot query helpers, backend-resolution helpers, or backend activation/switch helpers.
   - In `lib/matplotlib/pyplot.py`, inspect `_get_backend_mod`, `get_backend`, `switch_backend`, backend auto-selection helpers, and any setup paths that touch `_pylab_helpers.Gcf`, call `close('all')`, clear figure managers, or rebuild the interactive framework.
   - Compare the call path in the failing scenario against the cases that do not fail (`fig1` created before `rc_context`, or `plt.ion()` enabled) to isolate whether the destructive branch is tied to non-interactive lazy initialization.

2. Confirm the state mismatch after `rc_context()`.
   - Inspect `rc_context()` enter/exit handling in `lib/matplotlib/__init__.py`, specifically how `backend` is saved and restored.
   - Verify whether post-context state can legitimately be:
     - `rcParams['backend']` restored to the pre-context value, while
     - pyplot already has an initialized backend module / manager class from the figure created inside the context.
   - Determine whether `get_backend()` currently attempts to reconcile those two states by activating the rcParam backend, which would explain `Gcf.figs` being cleared.

3. Patch strategy centered on `get_backend()`, not `rc_context()`, unless tracing proves otherwise.
   - Make `matplotlib.get_backend()` side-effect free when pyplot already has an active backend.
   - Add/adjust logic so that if pyplot backend machinery is already initialized, `get_backend()` reports that active backend name from the loaded backend module/binding rather than forcing backend resolution from `rcParams['backend']`.
   - Allow lazy backend resolution only when no pyplot backend has been activated yet.
   - Ensure that any destructive backend re-sync remains reserved for explicit state-changing APIs such as `matplotlib.use()` or `pyplot.switch_backend()`, not for a read-only query.

4. Likely concrete code locations.
   - `lib/matplotlib/__init__.py`: update `get_backend()` to first consult active pyplot backend state, and avoid any helper that can trigger backend switching when a backend is already initialized.
   - `lib/matplotlib/pyplot.py`: if needed, factor or reuse a non-destructive helper that returns the current active backend module/name without invoking `switch_backend()` or full backend setup.
   - Only if tracing shows `rc_context()` is incorrectly invalidating backend state, make a narrow change there to avoid marking pyplot as needing backend reactivation on the next `get_backend()` call.

5. Regression coverage to add or strengthen in `lib/matplotlib/tests/test_rcparams.py`.
   - Keep/add `test_no_backend_reset_rccontext` covering the reported repro.
   - Strengthen it to assert both:
     - the backend string returned by `get_backend()` is stable/expected, and
     - the figure-manager identity is unchanged across the `get_backend()` call (for example, same `Gcf.figs` mapping and same manager object for the figure number), not just that the mapping stays non-empty.
   - Add a variant with a figure created before entering `rc_context()` to preserve the known non-failing case.
   - Add a variant asserting `plt.close(fig)` still succeeds after calling `get_backend()` in the repro scenario.
   - If practical, add a targeted comparison for interactive vs non-interactive setup paths, since `plt.ion()` reportedly avoids the bug.

6. Regression checks to run during implementation.
   - `lib/matplotlib/tests/test_rcparams.py::test_no_backend_reset_rccontext`
   - `lib/matplotlib/tests/test_rcparams.py::test_rcparams_reset_after_fail`
   - `lib/matplotlib/tests/test_rcparams.py::test_backend_fallback_headless`
   - Any nearby pyplot/backend state tests covering `switch_backend`, `use()`, and backend query semantics.