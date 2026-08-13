/**
 * Silences the console flood from Google Sign-In's popup watcher.
 *
 * Google's `gsi/client` polls `popup.closed` every few dozen milliseconds while
 * the sign-in popup is open, and `accounts.google.com` serves
 * `Cross-Origin-Opener-Policy-Report-Only: same-origin`. Chrome evaluates that
 * report-only policy on every poll and logs:
 *
 *   "Cross-Origin-Opener-Policy policy would block the window.closed call."
 *
 * Report-Only means nothing is actually blocked — sign-in works either way —
 * but the console fills with hundreds of identical lines. The message is
 * emitted by the browser rather than by JavaScript, so it cannot be caught,
 * suppressed, or overridden after the fact, and it references a header on
 * Google's origin that we do not control. The only way to stop it is to make
 * sure the real cross-origin `closed` property is never read at all.
 *
 * So for the duration of a sign-in we hand GIS a Proxy around the popup handle:
 * `closed` is answered from a local flag, everything else forwards untouched.
 *
 * The cost: that flag can no longer come from the popup itself, so dismissal is
 * inferred from the opener regaining focus for CLOSE_GRACE_MS. Both completing
 * and cancelling the popup hand focus back, so GIS still terminates its poll
 * and `onError` still fires on cancel. The known false positive is clicking
 * back onto this tab and leaving the popup open past the grace period — GIS
 * then gives up as though it had been cancelled and the user clicks again.
 */

// Long enough that a stray click on this tab does not read as a cancel, short
// enough that a real cancel still resolves promptly.
const CLOSE_GRACE_MS = 1500;

const PATCH_MARKER = "__googlePopupShield";

/**
 * Patches `window.open` until the returned disposer is called. Install it
 * synchronously inside the click handler, immediately before triggering the
 * GIS flow, and dispose it once the flow settles.
 *
 * @returns {() => void} disposer — safe to call more than once.
 */
export function installGooglePopupShield() {
    // Nothing to patch outside a browser, and re-entrancy would leak the
    // original reference and make the shield impossible to remove.
    if (typeof window === "undefined" || window.open?.[PATCH_MARKER]) {
        return () => { };
    }

    const nativeOpen = window.open;
    const teardowns = [];
    let disposed = false;

    const shieldedOpen = function shieldedOpen(...args) {
        const popup = nativeOpen.apply(window, args);
        // A blocked popup is `null`. GIS checks for that, so pass it straight
        // through rather than wrapping it.
        if (!popup) return popup;

        let closed = false;
        let timer = null;

        const armClose = () => {
            if (disposed || closed) return;
            clearTimeout(timer);
            timer = setTimeout(() => { closed = true; }, CLOSE_GRACE_MS);
        };
        // Focus returning to the popup means it is still open after all.
        const disarmClose = () => clearTimeout(timer);

        window.addEventListener("focus", armClose);
        window.addEventListener("blur", disarmClose);
        teardowns.push(() => {
            clearTimeout(timer);
            window.removeEventListener("focus", armClose);
            window.removeEventListener("blur", disarmClose);
        });

        return new Proxy(popup, {
            get(target, prop, receiver) {
                if (prop === "closed") return closed;
                const value = Reflect.get(target, prop, receiver);
                // `postMessage`/`close`/`focus` brand-check their `this`, which
                // would be the Proxy without this bind, and throw.
                return typeof value === "function" ? value.bind(target) : value;
            },
            set(target, prop, value) {
                return Reflect.set(target, prop, value);
            },
        });
    };

    // Marked so a second install cannot clobber `nativeOpen`.
    Object.defineProperty(shieldedOpen, PATCH_MARKER, { value: true });

    window.open = shieldedOpen;

    return function disposeGooglePopupShield() {
        if (disposed) return;
        disposed = true;
        // Only restore if nobody else patched on top of us in the meantime.
        if (window.open === shieldedOpen) window.open = nativeOpen;
        teardowns.forEach((teardown) => teardown());
        teardowns.length = 0;
    };
}
