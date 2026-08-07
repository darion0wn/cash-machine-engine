document.addEventListener("DOMContentLoaded", () => {
  const topicMeters = Array.from(
    document.querySelectorAll(".feed-topic-meter-fill[data-width]")
  );

  topicMeters.forEach((meter) => {
    const width = Number(meter.dataset.width || 0);
    const clamped = Math.max(0, Math.min(100, width));
    meter.style.width = `${clamped}%`;
  });

  const searchInput = document.querySelector("[data-dashboard-search]");

  if (!searchInput) {
    return;
  }

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
});
