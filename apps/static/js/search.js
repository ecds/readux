// Scripts to improve search functionality
// Adapted from Princeton-CDH/geniza project https://github.com/Princeton-CDH/geniza/

let textInput;
let sortElement;
let relevanceSortOption;
let defaultSortOption;
let resetFiltersButton;
let form;

$(document).ready(function() {
    sortElement = document.querySelector("select#id_sort");
    relevanceSortOption = sortElement.querySelector("option[value='_score']");
    defaultSortOption = sortElement.querySelector("option[value='label_alphabetical']");
    textInput = document.querySelector("input[type='search']");
    // Attach event listeners to text input to update sort
    textInput.addEventListener("input", autoUpdateSort);
    if (textInput.value.trim() == "") {
        disableRelevanceSort();
    }
    // Add reset filters event listener
    allFilters = document.querySelectorAll("#search-filters select");
    resetFiltersButton = document.querySelector("button#reset-filters");
    form = document.querySelector("form#search-form");
    resetFiltersButton.addEventListener("click", resetFilters);
});

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
    form.submit();
}