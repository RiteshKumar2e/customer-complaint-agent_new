// Brand logo. Both variants are rendered and CSS shows the one that contrasts
// with the current theme (dark by default, `body.light-theme` for light).
export default function Logo({ height = 32, variant = "full", onClick, className = "", label = "Quickfix AI home" }) {
  const isMark = variant === "mark";
  const content = isMark ? (
    <img src="/icon-192.png" alt="Quickfix AI" height={height} width={height} className="qf-logo-img" />
  ) : (
    <>
      <img src="/logo-white.png" alt="Quickfix AI" height={height} className="qf-logo-img qf-logo-on-dark" />
      <img src="/logo.png" alt="" aria-hidden="true" height={height} className="qf-logo-img qf-logo-on-light" />
    </>
  );
  if (onClick) {
    return (
      <button type="button" className={`qf-logo qf-logo-button ${className}`} onClick={onClick} aria-label={label}>
        {content}
      </button>
    );
  }
  return <span className={`qf-logo ${className}`}>{content}</span>;
}
