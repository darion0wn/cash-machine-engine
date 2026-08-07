document.addEventListener("DOMContentLoaded", () => {
  const sidebar = document.getElementById("sidebar");
  const sidebarToggle = document.querySelector("[data-sidebar-toggle]");
  const sidebarOverlay = document.querySelector("[data-sidebar-overlay]");
  const body = document.body;
  const topicMeters = Array.from(
    document.querySelectorAll(".feed-topic-meter-fill[data-width]")
  );

  const revealTargets = Array.from(
    document.querySelectorAll(
      [
        ".main-content .mobile-topbar",
        ".main-content .dashboard-topbar",
        ".main-content .hero",
        ".main-content .metric",
        ".main-content .card",
        ".main-content .page-placeholder",
        ".main-content .feed-section-card",
        ".main-content .trend-band-card",
        ".main-content .trend-band-item",
        ".main-content .trend-opportunity-item",
        ".main-content .portfolio-section-card",
        ".main-content .portfolio-item",
        ".main-content .portfolio-recent-item",
        ".main-content .report-archive-item",
        ".main-content .reports-source-item",
      ].join(", ")
    )
  );

  revealTargets.forEach((element, index) => {
    element.classList.add("reveal-item");
    element.style.setProperty("--reveal-delay", `${Math.min(index * 35, 420)}ms`);
  });

  const setSidebarOpen = (isOpen) => {
    if (!sidebar || !sidebarToggle) {
      return;
    }

    body.classList.toggle("sidebar-open", isOpen);
    sidebarToggle.setAttribute("aria-expanded", String(isOpen));

    if (sidebarOverlay) {
      sidebarOverlay.tabIndex = isOpen ? 0 : -1;
    }
  };

  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener("click", () => {
      setSidebarOpen(!body.classList.contains("sidebar-open"));
    });
  }

  if (sidebarOverlay) {
    sidebarOverlay.addEventListener("click", () => {
      setSidebarOpen(false);
    });
  }

  if (sidebar) {
    sidebar.querySelectorAll("a.nav-link").forEach((link) => {
      link.addEventListener("click", () => {
        if (window.matchMedia("(max-width: 991.98px)").matches) {
          setSidebarOpen(false);
        }
      });
    });
  }

  window.addEventListener("resize", () => {
    if (window.matchMedia("(min-width: 992px)").matches) {
      setSidebarOpen(false);
    }
  });

  requestAnimationFrame(() => {
    body.classList.add("is-loaded");
  });

  topicMeters.forEach((meter) => {
    const width = Number(meter.dataset.width || 0);
    const clamped = Math.max(0, Math.min(100, width));

    meter.style.width = "0%";

    requestAnimationFrame(() => {
      meter.style.width = `${clamped}%`;
    });
  });

  const searchInput = document.querySelector("[data-dashboard-search]");

  if (searchInput) {
    const tables = Array.from(
      document.querySelectorAll(".dashboard-searchable-table tbody[data-dashboard-table]")
    );

    const visibleCount = document.querySelector("[data-dashboard-search-count]");

    const updateSearchState = () => {
      const query = searchInput.value.trim().toLowerCase();
      let totalVisible = 0;

      tables.forEach((tbody) => {
        const rows = Array.from(tbody.querySelectorAll("tr[data-dashboard-row]"));
        const emptyRow = tbody.querySelector("tr[data-dashboard-filter-empty]");
        const defaultEmptyRows = Array.from(
          tbody.querySelectorAll("tr[data-dashboard-default-empty]")
        );

        let visibleInTable = 0;

        defaultEmptyRows.forEach((row) => {
          row.classList.toggle("d-none", query.length > 0);
        });

        rows.forEach((row) => {
          const searchText = (row.dataset.search || "").toLowerCase();
          const isVisible = !query || searchText.includes(query);

          row.classList.toggle("d-none", !isVisible);

          if (isVisible) {
            visibleInTable += 1;
          }
        });

        if (emptyRow) {
          emptyRow.classList.toggle("d-none", !(query.length > 0 && visibleInTable === 0));
        }

        totalVisible += visibleInTable;
      });

      if (visibleCount) {
        visibleCount.textContent = totalVisible;
      }
    };

    searchInput.addEventListener("input", updateSearchState);
    updateSearchState();
  }

  const shouldAnimate = window.matchMedia("(prefers-reduced-motion: no-preference)").matches;

  if (shouldAnimate) {
    const internalLinks = Array.from(document.querySelectorAll('a[href]'));

    internalLinks.forEach((link) => {
      const href = link.getAttribute("href");

      if (
        !href ||
        href.startsWith("#") ||
        href.startsWith("mailto:") ||
        href.startsWith("tel:") ||
        href.startsWith("javascript:")
      ) {
        return;
      }

      if (link.hasAttribute("download") || (link.target && link.target !== "_self")) {
        return;
      }

      let url;

      try {
        url = new URL(link.href, window.location.origin);
      } catch {
        return;
      }

      if (url.origin !== window.location.origin) {
        return;
      }

      link.addEventListener("click", (event) => {
        if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
          return;
        }

        const current = `${window.location.pathname}${window.location.search}${window.location.hash}`;
        const target = `${url.pathname}${url.search}${url.hash}`;

        if (current === target) {
          return;
        }

        event.preventDefault();
        body.classList.add("is-exiting");

        window.setTimeout(() => {
          window.location.assign(link.href);
        }, 110);
      });
    });
  }

  window.addEventListener("pageshow", () => {
    body.classList.remove("is-exiting");
    body.classList.add("is-loaded");
    if (window.matchMedia("(min-width: 992px)").matches) {
      setSidebarOpen(false);
    }
  });

  window.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      setSidebarOpen(false);
    }
  });
});
