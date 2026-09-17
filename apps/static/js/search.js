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
    }

    // initialize elements
    form = document.querySelector("form#search-form");
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

    // "Show volumes without a published date" only exists when the current
    // result scope actually contains undated volumes (the template omits it
    // otherwise), so every reference to it has to be null-guarded. When it is
    // present it defaults to checked; a submitted search wins over that
    // default, so an unchecked box stays unchecked across page loads.
    if (includeUndatedCheckbox) {
        includeUndatedCheckbox.checked = urlParams
            ? urlParams.get("include_undated") === "on"
            : true;
    }

    // Reset button is absent alongside the year selects when nothing is dated.
    if (resetDateRangeButton) {
        resetDateRangeButton.addEventListener("click", resetDateRange);
    }

    // Add reset filters event listener
    allFilters = document.querySelectorAll("#search-filters select");
    document.querySelectorAll("button.reset-filters").forEach(button => {
        button.addEventListener("click", resetFilters);
    });
});

function setUpYearDropdowns() {
    // Prepare the start/end year dropdowns based on available data

    // The year selects are omitted when the current result scope has no dated
    // volumes at all (template gates them on date_range_has_dated). Nothing to
    // wire up in that case.
    if (!startYearSelect || !endYearSelect) return;

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
    if (!resetDateRangeButton || !startYearSelect || !endYearSelect) return;
    // Only offer the shortcut once the selection is actually narrower than
    // the full available range
    const isFullRange =
        parseInt(startYearSelect.value) === fullMinYear &&
        parseInt(endYearSelect.value) === fullMaxYear;
    resetDateRangeButton.hidden = isFullRange;
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
    // (absent when the result scope has no dated volumes)
    if (startYearSelect && endYearSelect) {
        setYearSelectValue(startYearSelect, startYearSelect.options[0].value);
        setYearSelectValue(endYearSelect, endYearSelect.options[endYearSelect.options.length - 1].value);
    }
    // "Show volumes without a published date" defaults to on, so restore it to
    // checked along with the rest of the filters.
    if (includeUndatedCheckbox) {
        includeUndatedCheckbox.checked = true;
    }
    form.submit();
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
