import { ThemeToggle } from "./ThemeToggle";

type NavBarProps = {
  theme: "light" | "dark";
  onThemeChange: (theme: "light" | "dark") => void;
  onHome: () => void;
};

export function NavBar({ theme, onThemeChange, onHome }: NavBarProps) {
  return (
    <nav className="verifai-nav">
      <button className="nav-logo" type="button" onClick={onHome} aria-label="VerifAI home">
        <span className="shield-mark" aria-hidden="true">✓</span>
        Verif<span className="accent">AI</span>
      </button>
      <div className="nav-links">
        <a className="nav-link" href="#about">About</a>
        <a className="nav-link" href="#workflow">How It Works</a>
        <ThemeToggle theme={theme} onThemeChange={onThemeChange} />
      </div>
    </nav>
  );
}
