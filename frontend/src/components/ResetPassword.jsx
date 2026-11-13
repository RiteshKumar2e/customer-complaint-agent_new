import ForgotPassword from "./ForgotPassword";

// Password resets now use a 6-digit email code instead of a link. Old
// /reset-password links land on the same code-based flow.
export default function ResetPassword({ onNavigate }) {
    return <ForgotPassword onNavigate={onNavigate} />;
}
