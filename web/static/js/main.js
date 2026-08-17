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



  const chartDataElement = document.getElementById("dashboard-chart-data");

  if (chartDataElement && window.Chart) {
    try {
      const chartData = JSON.parse(chartDataElement.textContent || "{}");

      const createChart = (canvasId, config) => {
        const canvas = document.getElementById(canvasId);

        if (!canvas || !config) {
          return;
        }

        const labels = Array.isArray(config.labels) ? config.labels : [];
        const values = Array.isArray(config.values) ? config.values : [];

        if (!labels.length || !values.length) {
          return;
        }

        const context = canvas.getContext("2d");

        if (!context) {
          return;
        }

        const commonOptions = {
          responsive: true,
          maintainAspectRatio: false,
          animation: prefersReducedMotion
            ? false
            : {
                duration: 650,
                easing: "easeOutQuart",
              },
          plugins: {
            legend: {
              display: false,
            },
            tooltip: {
              callbacks: {
                label: (tooltipItem) => {
                  const value = tooltipItem.raw ?? 0;
                  return ` ${value}`;
                },
              },
            },
          },
        };

        return config.type === "doughnut"
          ? new window.Chart(context, {
              type: "doughnut",
              data: {
                labels,
                datasets: [
                  {
                    data: values,
                    borderWidth: 0,
                    hoverOffset: 6,
                  },
                ],
              },
              options: {
                ...commonOptions,
                cutout: "68%",
                plugins: {
                  ...commonOptions.plugins,
                  legend: {
                    display: true,
                    position: "bottom",
                    labels: {
                      usePointStyle: true,
                      padding: 18,
                    },
                  },
                },
              },
            })
          : new window.Chart(context, {
              type: config.type || "bar",
              data: {
                labels,
                datasets: [
                  {
                    label: config.label || "",
                    data: values,
                    borderWidth: 0,
                    borderRadius: 8,
                    tension: 0.35,
                    fill: config.type === "line",
                  },
                ],
              },
              options: {
                ...commonOptions,
                indexAxis: config.horizontal ? "y" : "x",
                scales: {
                  x: {
                    beginAtZero: true,
                    grid: {
                      display: false,
                    },
                    ticks: {
                      maxRotation: 0,
                      autoSkip: config.horizontal ? false : true,
                    },
                  },
                  y: {
                    beginAtZero: true,
                    grid: {
                      color: "rgba(148, 163, 184, 0.16)",
                    },
                  },
                },
              },
            });
      };

      createChart("dashboard-decision-chart", {
        ...chartData.decision_mix,
        type: "doughnut",
      });

      createChart("dashboard-cash-chart", {
        ...chartData.cash_distribution,
        type: "bar",
      });

      createChart("dashboard-trend-chart", {
        ...chartData.trend_momentum,
        type: "bar",
        horizontal: true,
        label: "Momentum",
      });

      createChart("dashboard-activity-chart", {
        ...chartData.recent_activity,
        type: "line",
        label: "Analyses",
      });
    } catch (error) {
      console.error("Dashboard chart initialization failed.", error);
    }
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


  const favoriteButtons = Array.from(
    document.querySelectorAll("[data-favorite-button]")
  );

  const setFavoriteButtonState = (button, isFavorite) => {
    button.classList.toggle("is-favorite", isFavorite);
    button.setAttribute("aria-pressed", isFavorite ? "true" : "false");
    button.setAttribute(
      "aria-label",
      isFavorite
        ? "Remove from My Opportunities"
        : "Add to My Opportunities"
    );
    button.setAttribute(
      "title",
      isFavorite
        ? "Remove from My Opportunities"
        : "Add to My Opportunities"
    );

    const label = button.querySelector(".favorite-button-label");
    if (label) {
      label.textContent = isFavorite ? "Saved" : "Save";
    }
  };

  favoriteButtons.forEach((button) => {
    button.addEventListener("click", async () => {
      if (button.classList.contains("is-saving")) {
        return;
      }

      const opportunityId = button.dataset.opportunityId;
      if (!opportunityId) {
        return;
      }

      button.classList.add("is-saving");

      try {
        const response = await fetch(
          `/favorites/${encodeURIComponent(opportunityId)}/toggle`,
          {
            method: "POST",
            headers: {
              Accept: "application/json",
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              cash_machine_score: Number(button.dataset.cashScore || 0),
              ranking_score: Number(button.dataset.rankingScore || 0),
              portfolio_status: button.dataset.portfolioStatus || "WATCH",
            }),
          }
        );

        if (!response.ok) {
          throw new Error(`Favorite request failed (${response.status}).`);
        }

        const payload = await response.json();

        setFavoriteButtonState(button, Boolean(payload.favorite));

        if (
          document.body.dataset.page === "favorites" &&
          !payload.favorite
        ) {
          const card = button.closest(".favorite-opportunity-card");
          if (card) {
            card.remove();
          }

          const remaining = document.querySelectorAll(
            ".favorite-opportunity-card"
          ).length;

          window.location.reload();
        }
      } catch (error) {
        console.error(error);
        window.alert(
          "Unable to update My Opportunities. Please try again."
        );
      } finally {
        button.classList.remove("is-saving");
      }
    });
  });

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
