function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  const toggleButton = document.getElementById("theme-toggle");
  if (toggleButton) {
    toggleButton.textContent = theme === "dark" ? "☀️ Светлая" : "🌙 Тёмная";
  }
}

function toggleTheme(event) {
  event.preventDefault();
  const currentTheme = document.documentElement.getAttribute("data-theme");
  const newTheme = currentTheme === "dark" ? "light" : "dark";
  localStorage.setItem("theme", newTheme);
  applyTheme(newTheme);
}

document.addEventListener("DOMContentLoaded", () => {
  const storedTheme = localStorage.getItem("theme") || "light";
  applyTheme(storedTheme);

  const toggleButton = document.getElementById("theme-toggle");
  if (toggleButton) {
    toggleButton.addEventListener("click", toggleTheme);
  }
});
