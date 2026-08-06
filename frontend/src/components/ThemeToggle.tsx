type ThemeToggleProps = {
  theme: "light" | "dark";
  onThemeChange: (theme: "light" | "dark") => void;
};

export function ThemeToggle({ theme, onThemeChange }: ThemeToggleProps) {
  return (
    <div className="theme-toggle-btn" aria-label="Theme">
      <button
        className={theme === "light" ? "active" : ""}
        title="Light theme"
        type="button"
        onClick={() => onThemeChange("light")}
      >
        <span aria-hidden="true">Sun</span>
      </button>
      <button
        className={theme === "dark" ? "active" : ""}
        title="Dark theme"
        type="button"
        onClick={() => onThemeChange("dark")}
      >
        <span aria-hidden="true">Moon</span>
      </button>
    </div>
  );
}
