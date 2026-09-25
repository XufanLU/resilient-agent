1. Reproduce conceptually by isolating the transition points.
- Inspect state at four checkpoints in the failing sequence:
  - before entering `rc_context()`
  - inside the context after `plt.figure()`
  - immediately after context exit
  - after `matplotlib.get_backend()`
- At each checkpoint compare:
  - `matplotlib.rcParams['backend']`
  - any backend sentinel/default representation used before lazy resolution
  - pyplot’s active backend/module state in `pyplot.py`
  - `plt._pylab_helpers.Gcf.figs`
- Goal: determine whether `Gcf.figs` is only cleared after `get_backend()` and whether the real inconsistency is introduced earlier by `rc_context().__exit__`.

2. Inspect `lib/matplotlib/__init__.py`.
- Read `rc_context()` enter/exit logic to see whether it snapshots and restores `backend` unconditionally.
- Identify whether the restored value can be a pre-resolution sentinel/default rather than the now-active resolved backend.
- Inspect `get_backend()` to see whether it is expected to be read-only or whether it can force backend resolution from `rcParams['backend']`.

3. Inspect the lazy backend initialization path in `lib/matplotlib/pyplot.py`.
- Trace the path used by `plt.figure()` when no backend has yet been fully initialized.
- Identify the active-backend bookkeeping pyplot uses once that path completes.
- Inspect `switch_backend()` and find the exact branch/condition that clears or rebuilds state such as `Gcf.figs`.
- Confirm whether the harmful action is a redundant switch caused by `rcParams['backend']` no longer matching pyplot’s already-live backend module/state.

4. Apply a narrow fix based on the observed branch.
- Preferred fix site: `rc_context()` restoration in `lib/matplotlib/__init__.py`.
- Decision rule:
  - if no backend was resolved during the context, restore `backend` normally;
  - if a backend *was* resolved during the context, do not restore `rcParams['backend']` to the pre-resolution sentinel/default that would later trigger backend reinitialization.
- Concretely, special-case backend restoration so the exit path preserves a resolved backend value once pyplot has become live during the context, instead of blindly reinstating the old unresolved/default token.
- Only consider a `get_backend()`/pyplot guard if inspection shows `rc_context()` cannot safely own this invariant.

5. Avoid scope creep.
- Do not alter explicit backend-switch semantics for `matplotlib.use()` or `pyplot.switch_backend()`.
- The fix should only prevent accidental backend reinitialization from `rc_context()` restoration and/or `get_backend()` query paths when pyplot is already using a backend.

6. Regression coverage in `lib/matplotlib/tests/test_rcparams.py`.
- Keep/add the focused failing test for the reported sequence:
  - create first figure inside `rc_context()`
  - snapshot `Gcf.figs`
  - call `matplotlib.get_backend()`
  - assert `Gcf.figs` is unchanged
  - then call `plt.close(fig)` and assert the figure is removed normally afterward
- This should verify the two external behaviors from the report:
  - `get_backend()` does not clear figure registration
  - closing the figure still works
- If helpful, add assertions around backend state before/after exit only insofar as needed to lock in the user-visible bug mechanism without overfitting to private internals.

7. Regression checks to keep in mind.
- Existing rcParams tests named in the task should remain unaffected, especially:
  - `test_rcparams`
  - `test_RcParams_class`
  - `test_rcparams_reset_after_fail`
  - `test_backend_fallback_headless`
  - `test_deprecation`
- Watch specifically for unintended changes in backend restoration behavior when no pyplot backend was resolved inside the context.