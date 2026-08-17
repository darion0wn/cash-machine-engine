document.addEventListener("DOMContentLoaded", () => {
  const sidebar = document.getElementById("sidebar");
  const sidebarToggle = document.querySelector("[data-sidebar-toggle]");
  const sidebarOverlay = document.querySelector("[data-sidebar-overlay]");
  const body = document.body;
  const loadingOverlay = document.querySelector("[data-loading-overlay]");
  const prefersReducedMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)"
  ).matches;
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
        ".main-content .empty-state",
        ".main-content .report-empty",
        ".main-content .portfolio-empty",
        ".main-content .trend-band-empty",
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

  const showLoadingOverlay = () => {
    body.classList.add("is-loading");
    if (loadingOverlay) {
      loadingOverlay.hidden = false;
    }
  };

  const hideLoadingOverlay = () => {
    body.classList.remove("is-loading");
    if (loadingOverlay) {
      loadingOverlay.hidden = true;
    }
  };

  const shouldHandleLoadingNavigation = (link, event) => {
    if (!link) {
      return false;
    }

    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
      return false;
    }

    if (event.button !== 0) {
      return false;
    }

    if (link.hasAttribute("download")) {
      return false;
    }

    if (link.target && link.target !== "_self") {
      return false;
    }

    const href = link.getAttribute("href");

    if (
      !href ||
      href.startsWith("#") ||
      href.startsWith("mailto:") ||
      href.startsWith("tel:") ||
      href.startsWith("javascript:")
    ) {
      return false;
    }

    let url;

    try {
      url = new URL(link.href, window.location.origin);
    } catch {
      return false;
    }

    if (url.origin !== window.location.origin) {
      return false;
    }

    const current = `${window.location.pathname}${window.location.search}${window.location.hash}`;
    const target = `${url.pathname}${url.search}${url.hash}`;

    return current !== target;
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

  hideLoadingOverlay();

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

    const resetButtons = Array.from(
      document.querySelectorAll("[data-dashboard-search-reset]")
    );

    resetButtons.forEach((button) => {
      button.addEventListener("click", () => {
        searchInput.value = "";
        updateSearchState();
        searchInput.focus();
      });
    });

    updateSearchState();
  }


  const refreshTrigger = document.querySelector("[data-refresh-trigger]");

  if (refreshTrigger) {
    const refreshStartUrl = refreshTrigger.dataset.refreshStartUrl;
    const refreshStatusUrl = refreshTrigger.dataset.refreshStatusUrl;
    const loadingSubtitle = document.querySelector(".loading-panel-subtitle");
    const refreshDefaultText = refreshTrigger.textContent.trim();

    let refreshTimer = null;

    const setRefreshUi = (isRunning) => {
      refreshTrigger.disabled = isRunning;
      refreshTrigger.setAttribute("aria-busy", String(isRunning));
      refreshTrigger.textContent = isRunning ? "Refreshing…" : refreshDefaultText;

      if (loadingSubtitle && isRunning) {
        loadingSubtitle.textContent =
          "Refreshing crawler and analysis pipeline…";
      }
    };

    const clearRefreshTimer = () => {
      if (refreshTimer !== null) {
        window.clearTimeout(refreshTimer);
        refreshTimer = null;
      }
    };

    const pollRefreshStatus = async ({ reloadOnComplete = true } = {}) => {
      try {
        const response = await fetch(refreshStatusUrl, {
          headers: { Accept: "application/json" },
          cache: "no-store",
        });

        if (!response.ok) {
          throw new Error(`Status request failed (${response.status}).`);
        }

        const status = await response.json();

        if (status.state === "running") {
          setRefreshUi(true);
          showLoadingOverlay();
          refreshTimer = window.setTimeout(
            () => pollRefreshStatus({ reloadOnComplete }),
            1200
          );
          return;
        }

        clearRefreshTimer();
        setRefreshUi(false);

        if (status.state === "completed") {
          hideLoadingOverlay();

          if (reloadOnComplete) {
            window.location.reload();
          }

          return;
        }

        if (status.state === "failed") {
          hideLoadingOverlay();
          window.alert(
            status.message ||
              "Refresh failed. Check the terminal output for details."
          );
          return;
        }

        hideLoadingOverlay();
      } catch (error) {
        clearRefreshTimer();
        setRefreshUi(false);
        hideLoadingOverlay();
        window.alert(
          "Unable to check refresh status. Check the web server output."
        );
        console.error(error);
      }
    };

    refreshTrigger.addEventListener("click", async () => {
      if (refreshTrigger.disabled) {
        return;
      }

      setRefreshUi(true);

      if (loadingSubtitle) {
        loadingSubtitle.textContent =
          "Starting crawler and analysis pipeline…";
      }

      showLoadingOverlay();

      try {
        const response = await fetch(refreshStartUrl, {
          method: "POST",
          headers: {
            Accept: "application/json",
          },
        });

        if (response.status === 409) {
          await pollRefreshStatus({ reloadOnComplete: true });
          return;
        }

        if (!response.ok && response.status !== 202) {
          throw new Error(`Refresh request failed (${response.status}).`);
        }

        await pollRefreshStatus({ reloadOnComplete: true });
      } catch (error) {
        clearRefreshTimer();
        setRefreshUi(false);
        hideLoadingOverlay();
        window.alert(
          "Unable to start the refresh. Check the web server output."
        );
        console.error(error);
      }
    });

    // If another dashboard tab already started a refresh, pick it up.
    pollRefreshStatus({ reloadOnComplete: false });
  }

  const internalLinks = Array.from(document.querySelectorAll('a[href]'));

  internalLinks.forEach((link) => {
    link.addEventListener("click", (event) => {
      if (!shouldHandleLoadingNavigation(link, event)) {
        return;
      }

      event.preventDefault();
      body.classList.add("is-exiting");
      showLoadingOverlay();

      window.setTimeout(() => {
        window.location.assign(link.href);
      }, prefersReducedMotion ? 0 : 140);
    });
  });

  window.addEventListener("pageshow", () => {
    body.classList.remove("is-exiting");
    hideLoadingOverlay();
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
