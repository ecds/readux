// Scripts to improve search functionality
// Partially adapted from Princeton-CDH/geniza project https://github.com/Princeton-CDH/geniza/

let textInput;
let sortElement;
let relevanceSortOption;
let defaultSortOption;
let form;
let slider;
let resetFiltersButton;
let allFilters;
let dateToggleSwitch;
let dateToggleState;
let urlParams;
let queryMinYear;
let queryMaxYear;
let authorsFilter;
let authorsMultiselect;
let dateRange;

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
    dateRange = document.querySelector(".noUi-tooltip");
    sortElement = document.querySelector("select#id_sort");
    relevanceSortOption = sortElement.querySelector("option[value='_score']");
    defaultSortOption = sortElement.querySelector("option[value='label_alphabetical']");
    textInput = document.querySelector("input[type='search']");
    // authorsFilter = document.querySelector("input[type='text']#authors-filter");
    authorsMultiselect = document.querySelector("select[name='author']");

    // Attach event listener to sort dropdown to auto-submit
    sortElement.addEventListener("change", handleSort);

    // Attach event listeners to text input to update sort
    textInput.addEventListener("input", autoUpdateSort);
    if (textInput.value.trim() == "") {
        disableRelevanceSort();
    }

    // Attach event listener to filter author multiselect options
    // authorsFilter.addEventListener("input", handleAuthorsFilter);

    // Set up slider
    slider = document.getElementById("date-range-slider");
    setUpSlider(slider);

    // Initialize date toggle switch and add event listener
    setDateFieldToggleState(dateToggleState);
    dateToggleSwitch.addEventListener("change", toggleDate);
 
    // Add reset filters event listener
    allFilters = document.querySelectorAll("#search-filters select");
    document.querySelectorAll("button.reset-filters").forEach(button => {
        button.addEventListener("click", resetFilters);
    });
    // Attach event listeners to form to handle slider input
    form.addEventListener("submit", handleSubmit);
    form.addEventListener("formdata", handleFormData);
});

function setUpSlider(slider) {
    // Prepare the date range slider based on available data

    // Get min and max from data attribute on Django form inputs
    const minDate = document.querySelector("input[name='start_date']").getAttribute("data-date-initial");
    const maxDate = document.querySelector("input[name='end_date']").getAttribute("data-date-initial");
    // Get year for slider purposes
    let minYear = parseInt(minDate.split("-")[0]); 
    let maxYear = parseInt(maxDate.split("-")[0]); 

    // If there is no min and max (i.e. query returned 0 results), use query params for date
    if (!maxYear && !minYear && urlParams) {
        if (queryMinYear) minYear = parseInt(queryMinYear.split("-")[0]);
        if (queryMaxYear) maxYear = parseInt(queryMaxYear.split("-")[0]);
    }
    
    // setup noUISlider
    noUiSlider.create(slider, {
        // fallback to range [1, current year] if necessary
        start: [minYear || 1, maxYear || new Date().getFullYear()],
        connect: true,
        range: {
            "min": minYear || 1,
            "max": maxYear || new Date().getFullYear()
        },
        step: 1,
        tooltips: true,
        format: {
            from: function(value) {
                return parseInt(value);
            },
            to: function(value) {
                return parseInt(value);
            }
        },
    });
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
    // Change the date toggle switch and slider to match toggle state
    if (state === false) {
        // dateToggleSwitch.removeAttribute("checked");
        slider.setAttribute("disabled", true);
    } else {
        // dateToggleSwitch.setAttribute("checked", true);
        slider.removeAttribute("disabled");
    }
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

function handleSubmit() {
    // construct a FormData object, which fires the formdata event
    new FormData(form);
}

function handleFormData(e) {
    const formData = e.formData; 
    if (dateToggleState === false) {
        // unset start and end date
        formData.delete("start_date");
        formData.delete("end_date");
    } else {
        // set start and end date on form, from slider values (year only)
        const dateRange = slider.noUiSlider.get();
        formData.set("start_date", `${String(dateRange[0]).padStart(4, "0")}-01-01`);
        formData.set("end_date", `${String(dateRange[1]).padStart(4, "0")}-12-31`);
    }
}
