import Logo from "./Logo";

/** Shown for URLs the app does not know. */
export default function NotFound({ onHome }) {
  return (
    <main className="qf-notfound" aria-labelledby="nf-title">
      <Logo height={36} />
      <p className="qf-notfound-code">404</p>
      <h1 id="nf-title">Page not found</h1>
      <p>The page you are looking for doesn't exist or has moved.</p>
      <button type="button" className="qf-button" onClick={onHome}>Go to the home page</button>
    </main>
  );
}
