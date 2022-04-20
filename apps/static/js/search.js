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
let clearDateButton;
let shouldClearDate = false;
let urlParams;
let queryMinYear;
let queryMaxYear;

window.addEventListener("DOMContentLoaded", () => {
    form = document.querySelector("form#search-form");
    clearDateButton = document.getElementById("clear-date");

    // Get URL params
    if (window.location.search) {
        urlParams = new URLSearchParams(window.location.search);
        queryMinYear = urlParams.get('start_date');
        queryMaxYear = urlParams.get('end_date');
        // If there's no min and max year, disable date clear button
        if (!queryMinYear && !queryMaxYear) {
            clearDateButton.disabled = true;
        }
    } else {
        // If there's no search at all, disable date clear button
        clearDateButton.disabled = true;
    }

    sortElement = document.querySelector("select#id_sort");
    relevanceSortOption = sortElement.querySelector("option[value='_score']");
    defaultSortOption = sortElement.querySelector("option[value='label_alphabetical']");
    textInput = document.querySelector("input[type='search']");

    // Attach event listeners to text input to update sort
    textInput.addEventListener("input", autoUpdateSort);
    if (textInput.value.trim() == "") {
        disableRelevanceSort();
    }

    // Set up slider
    slider = document.getElementById("date-range-slider");
    setUpSlider(slider);

    // Add clear dates event listener
    clearDateButton.addEventListener("click", clearDateAndSubmit);

    // Add reset filters event listener
    allFilters = document.querySelectorAll("#search-filters select");
    resetFiltersButton = document.querySelector("button#reset-filters");
    resetFiltersButton.addEventListener("click", resetFilters);

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
    // Clears filters and submits the search
    allFilters.forEach((filter) => { 
        filter.selectedIndex = -1;
    });
    clearDateAndSubmit();
}

function clearDateAndSubmit() {
    shouldClearDate = true; // Needed to reset start and end date on form
    form.submit();
}

function handleSubmit() {
    // construct a FormData object, which fires the formdata event
    new FormData(form);
}

function handleFormData(e) {
    const formData = e.formData; 
    if (shouldClearDate === true) {
        // unset start and end date
        formData.set("start_date", "");
        formData.set("end_date", "");
    } else {
        // set start and end date on form, from slider values (year only)
        const dateRange = slider.noUiSlider.get();
        formData.set("start_date", `${String(dateRange[0]).padStart(4, "0")}-01-01`);
        formData.set("end_date", `${String(dateRange[1]).padStart(4, "0")}-12-31`);
    }
}
