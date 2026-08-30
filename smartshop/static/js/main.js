document.addEventListener("DOMContentLoaded", function () {
  const toggle = document.getElementById("sidebarToggle");
  const sidebar = document.getElementById("sidebar");
  if (toggle && sidebar) {
    toggle.addEventListener("click", () => sidebar.classList.toggle("show"));
    document.addEventListener("click", (e) => {
      if (window.innerWidth < 992 && sidebar.classList.contains("show") &&
          !sidebar.contains(e.target) && e.target !== toggle) {
        sidebar.classList.remove("show");
      }
    });
  }
});
