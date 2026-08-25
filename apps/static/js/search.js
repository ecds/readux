// Scripts to improve search functionality
// Partially adapted from Princeton-CDH/geniza project https://github.com/Princeton-CDH/geniza/

let textInput;
let sortElement;
let displayElement;
let relevanceSortOption;
let defaultSortOption;
let form;
let startYearSelect;
let endYearSelect;
let includeUndatedCheckbox;
let resetDateRangeButton;
let fullMinYear;
let fullMaxYear;
let resetFiltersButton;
let allFilters;
let dateToggleSwitch;
let dateToggleState;
let urlParams;
let queryMinYear;
let queryMaxYear;
let authorsFilter;
let authorsMultiselect;

window.addEventListener("DOMContentLoaded", () => {
    // Get URL params
    if (window.location.search) {
        urlParams = new URLSearchParams(window.location.search);
        queryMinYear = urlParams.get('start_date');
        queryMaxYear = urlParams.get('end_date');
        // If there's a min or max year, assume date toggle is on
        dateToggleState = Boolean(queryMinYear || queryMaxYear);
    } else {
        // If there's no search at all, turn date toggle off
        dateToggleState = false;
    }

    // initialize elements
    form = document.querySelector("form#search-form");
    dateToggleSwitch = document.querySelector("input[type='checkbox']#toggle-date");
    startYearSelect = document.getElementById("id_start_year");
    endYearSelect = document.getElementById("id_end_year");
    includeUndatedCheckbox = document.getElementById("id_include_undated");
    resetDateRangeButton = document.getElementById("reset-date-range");
    sortElement = document.querySelector("select#id_sort");
    displayElement = document.querySelector("select#id_display");
    relevanceSortOption = sortElement.querySelector("option[value='_score']");
    defaultSortOption = sortElement.querySelector("option[value='label_alphabetical']");
    textInput = document.querySelector("input[type='search']");
    // authorsFilter = document.querySelector("input[type='text']#authors-filter");
    authorsMultiselect = document.querySelector("select[name='author']");

    // Attach event listener to sort dropdown to auto-submit
    sortElement.addEventListener("change", handleSort);
    if (displayElement) {
        displayElement.addEventListener("change", () => form.submit());
    }

    // Attach event listeners to text input to update sort
    textInput.addEventListener("input", autoUpdateSort);
    if (textInput.value.trim() == "") {
        disableRelevanceSort();
    }

    // Attach event listener to filter author multiselect options
    // authorsFilter.addEventListener("input", handleAuthorsFilter);

    // Set up start/end year dropdowns
    setUpYearDropdowns();

    // "Show volumes without a published date" is a standing preference, not a
    // one-off filter: once someone turns it on they almost always want it on
    // for every future search, so it's stuck in localStorage rather than reset
    // whenever filters are cleared or a new search is run. An explicit
    // include_undated=on in the URL (e.g. a shared link) still wins and keeps
    // localStorage in sync.
    const urlHasIncludeUndated = Boolean(urlParams) && urlParams.get("include_undated") === "on";
    const storedIncludeUndated = localStorage.getItem("readux:includeUndated") === "true";
    includeUndatedCheckbox.checked = urlHasIncludeUndated || storedIncludeUndated;
    includeUndatedCheckbox.addEventListener("change", () => {
        localStorage.setItem("readux:includeUndated", includeUndatedCheckbox.checked);
    });

    resetDateRangeButton.addEventListener("click", resetDateRange);

    // Initialize date toggle switch and add event listener. The checkbox
    // itself isn't a bound Django form field, so its checked state has to be
    // synced here explicitly — otherwise a URL carrying start_date/end_date
    // (e.g. from a shared link) leaves the controls enabled while the
    // checkbox still visually reads "off".
    dateToggleSwitch.checked = dateToggleState;
    setDateFieldToggleState(dateToggleState);
    dateToggleSwitch.addEventListener("change", toggleDate);

    // Add reset filters event listener
    allFilters = document.querySelectorAll("#search-filters select");
    document.querySelectorAll("button.reset-filters").forEach(button => {
        button.addEventListener("click", resetFilters);
    });
});

function setUpYearDropdowns() {
    // Prepare the start/end year dropdowns based on available data

    // Get min and max from data attributes set from Elasticsearch aggregations
    const container = document.getElementById("date-range-filter");
    const minDate = container.getAttribute("data-min-date");
    const maxDate = container.getAttribute("data-max-date");
    let minYear = minDate ? parseInt(minDate.split("-")[0]) : 0;
    let maxYear = maxDate ? parseInt(maxDate.split("-")[0]) : 0;

    // If there is no min and max (i.e. query returned 0 results), use query params for date
    if (!maxYear && !minYear && urlParams) {
        if (queryMinYear) minYear = parseInt(queryMinYear.split("-")[0]);
        if (queryMaxYear) maxYear = parseInt(queryMaxYear.split("-")[0]);
    }
    minYear = minYear || 1;
    maxYear = maxYear || new Date().getFullYear();
    fullMinYear = minYear;
    fullMaxYear = maxYear;

    const selectedStartYear = queryMinYear ? parseInt(queryMinYear.split("-")[0]) : minYear;
    const selectedEndYear = queryMaxYear ? parseInt(queryMaxYear.split("-")[0]) : maxYear;

    // Volumes dated before year 1 CE get clamped to year 1 on the backend
    // (there's no way to represent BCE with a plain JS/Python date), so make
    // that clear on the option itself rather than silently showing "1".
    const hasBce = container.getAttribute("data-has-bce") === "true";
    const minYearLabel = hasBce && minYear === 1 ? "1 or earlier (BCE)" : null;

    populateYearSelect(startYearSelect, minYear, maxYear, selectedStartYear, "01-01", minYearLabel);
    populateYearSelect(endYearSelect, minYear, maxYear, selectedEndYear, "12-31");

    // Turn the long year lists into type-to-filter dropdowns instead of
    // plain scrolling selects, which get unwieldy over a multi-century range.
    // Selectize propagates value changes via jQuery's synthetic "change"
    // event, which native addEventListener listeners never see — so the
    // start/end sync below has to be bound through jQuery too.
    [startYearSelect, endYearSelect].forEach((select) => {
        $(select).selectize({
            maxItems: 1,
            allowEmptyOption: false,
        });
    });

    // Keep start year <= end year at all times
    $(startYearSelect).on("change", () => {
        const startYear = parseInt(startYearSelect.value);
        if (startYear > parseInt(endYearSelect.value)) {
            setYearSelectValue(endYearSelect, `${String(startYear).padStart(4, "0")}-12-31`);
        }
        updateResetDateRangeVisibility();
    });
    $(endYearSelect).on("change", () => {
        const endYear = parseInt(endYearSelect.value);
        if (endYear < parseInt(startYearSelect.value)) {
            setYearSelectValue(startYearSelect, `${String(endYear).padStart(4, "0")}-01-01`);
        }
        updateResetDateRangeVisibility();
    });

    updateResetDateRangeVisibility();
}

function updateResetDateRangeVisibility() {
    // Only offer the shortcut once the selection is actually narrower than
    // the full available range
    const isFullRange =
        parseInt(startYearSelect.value) === fullMinYear &&
        parseInt(endYearSelect.value) === fullMaxYear;
    resetDateRangeButton.hidden = isFullRange || !dateToggleState;
}

function resetDateRange() {
    // Restore the start/end dropdowns to the full available range
    setYearSelectValue(startYearSelect, `${String(fullMinYear).padStart(4, "0")}-01-01`);
    setYearSelectValue(endYearSelect, `${String(fullMaxYear).padStart(4, "0")}-12-31`);
    form.submit();
}

function setYearSelectValue(select, value) {
    // Update a year <select>'s value whether or not selectize has wrapped it
    if (select.selectize) {
        select.selectize.setValue(value);
    } else {
        select.value = value;
    }
}

function populateYearSelect(select, minYear, maxYear, selectedYear, monthDay, firstYearLabel) {
    select.innerHTML = "";
    for (let year = minYear; year <= maxYear; year++) {
        const option = document.createElement("option");
        option.value = `${String(year).padStart(4, "0")}-${monthDay}`;
        option.textContent = year === minYear && firstYearLabel ? firstYearLabel : year;
        if (year === selectedYear) option.selected = true;
        select.appendChild(option);
    }
}

function autoUpdateSort() {
    // when query is empty, disable sort by relevance
    if (textInput.value.trim() == "") {
        disableRelevanceSort();
    // when query is entered, sort by relevance
    } else {
        sortByRelevance();
    }
}
function sortByRelevance() {
    // select and undisable relevance option
    relevanceSortOption.selected = true;
    relevanceSortOption.disabled = false;
    relevanceSortOption.ariaDisabled = false;
    sortElement.value = relevanceSortOption.value;
    // set all other options unselected
    [...sortElement.querySelectorAll("option")]
        .filter((el) => el.value !== "_score")
        .forEach((opt) => {
            opt.selected = false;
        });
}

function disableRelevanceSort() {
    // if relevance sort was selected, set back to default
    if (relevanceSortOption.selected) {
        relevanceSortOption.selected = false;
        defaultSortOption.selected = true;
        sortElement.value = defaultSortOption.value;
    }
    // disable relevance sort
    relevanceSortOption.disabled = true;
    relevanceSortOption.ariaDisabled = true;
}

function resetFilters() {
    // Clear filters and submit the search
    allFilters.forEach((filter) => {
        filter.selectedIndex = -1;
    });
    // start/end year selects should fall back to the full range, not blank
    setYearSelectValue(startYearSelect, startYearSelect.options[0].value);
    setYearSelectValue(endYearSelect, endYearSelect.options[endYearSelect.options.length - 1].value);
    // "Show volumes without a published date" is a standing preference — leave
    // it as-is rather than clearing it along with the rest of the filters.
    dateToggleState = false;
    setDateFieldToggleState(false);
    form.submit();
}

function toggleDate(e) {
    // Use state of toggle button to turn on/off date filter
    dateToggleState = e.currentTarget.checked;
    setDateFieldToggleState(dateToggleState);
}

function setDateFieldToggleState(state) {
    // Change the year dropdowns (and their labels) to match toggle state.
    // Disabled fields are automatically excluded from form submission.
    [startYearSelect, endYearSelect].forEach((select) => {
        if (select.selectize) {
            state ? select.selectize.enable() : select.selectize.disable();
        } else {
            select.disabled = !state;
        }
    });
    includeUndatedCheckbox.disabled = !state;
    document.querySelectorAll("#date-range-filter .date-range-filter-label").forEach((label) => {
        label.classList.toggle("is-disabled", !state);
    });
    document.querySelector("#date-range-filter .date-range-bce-note").classList.toggle("is-disabled", !state);
    updateResetDateRangeVisibility();
}

function handleSort(e) {
    // Submits the form on sort change
    form.submit();
}

function handleAuthorsFilter(e) {
    // Simple "exact match" filter for authors multiselect;
    // hides non-matching entries from the multiselect options
    const term = e.currentTarget.value.toLowerCase();
    const authors = Array.apply(null, authorsMultiselect.options)
    authorsMultiselect.options = authors.filter(opt => opt.value.toLowerCase().includes(term));
    for (let i = 0; i < authorsMultiselect.length; i++) {
        let txt = authorsMultiselect.options[i].text.toLowerCase();
        if (!txt.match(term)) {
            authorsMultiselect.options[i].style.display = 'none';
        } else {
            authorsMultiselect.options[i].style.display = 'block';
        }

    }
}

// Core fix: prevent focus loss
$(document).on('mousedown', '.selectize-dropdown', function(e) {
    e.preventDefault();
});

// initializeSelectize stays the same
function initializeSelectize() {
    $(".custom-search-selectize").each(function () {
        if (!$(this).hasClass("selectized")) {
            $(this).selectize({
                plugins: ["clear_button"],
                placeholder: "Select one or more..."
            });
        }
    });
}

$(function () {
    // 1) Initial setup: your static selects...
    $("#id_collection, #id_author, #id_language").selectize({
        plugins: ["clear_button"],
        placeholder: "Select one or more..."
    });

    // 2) …and any .custom-search-selectize already in the DOM
    initializeSelectize();

    // 3) Watch for dynamically inserted selects
    const observer = new MutationObserver((mutations) => {
        mutations.forEach(mutation => {
            mutation.addedNodes.forEach(node => {
                // only care about element nodes
                if (node.nodeType !== Node.ELEMENT_NODE) return;

                // if the added node *is* a custom-search-selectize, or *contains* one…
                if (node.matches('.custom-search-selectize') ||
                    node.querySelector('.custom-search-selectize')
                ) {
                    initializeSelectize();
                }
            });
        });
    });

    // Scope this to a tighter container if you know where new selects appear;
    // using document.body will catch everything, but you can replace
    // document.body with document.querySelector('#your-results-container')
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });

    // Optional: if at some point you no longer need to observe:
    // observer.disconnect();
});
