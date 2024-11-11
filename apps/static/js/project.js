/* Project specific Javascript goes here. */
// Iterate through menu items and highlight the current page if it matches the URL
$.each($(".rx-nav-item"), function(index, navItem) {
    var segmentsInURL = (location.pathname.split('/').length - 1) - (location.pathname[location.pathname.length - 1] == '/' ? 1 : 0);
    var atModuleRoot = (segmentsInURL > 1) ? false:true;
    var activePage = window.location.pathname.replace(
      /^\/([^\/]*).*$/,
      "$1"
    );
    if (navItem.href.includes(activePage) && (activePage != "") && atModuleRoot) {
      navItem.classList.add("uk-active");
    }
});


// sort items displayed by appending/updating search params in URL
function ascaddURL(element) {
  $(element).attr("href", function() {
    if (window.location.search.length == 0) {
      this.href = this.href + "?sort=title&order=asc";
      return this.href;
    } else if (window.location.search.match(/[?&]order=asc/gi)) {
      this.href = this.href.replace("order=asc", "order=asc");
      return this.href;
    } else if (window.location.search.match(/[?&]order=desc/gi)) {
      this.href = this.href.replace("order=desc", "order=asc");
      return this.href;
    } else {
      this.href = this.href + "&order=asc";
      return this.href;
    }
  });
}

window.ascaddURL = ascaddURL;

// sort items displayed by appending/updating search params in URL
function descaddURL(element) {
  $(element).attr("href", function() {
    if (window.location.search.length == 0) {
      this.href = this.href + "?sort=title&order=desc";
      return this.href;
    } else if (window.location.search.match(/[?&]order=asc/gi)) {
      this.href = this.href.replace("order=asc", "order=desc");
      return this.href;
    } else if (window.location.search.match(/[?&]order=desc/gi)) {
      this.href = this.href.replace("order=desc", "order=desc");
      return this.href;
    } else {
      this.href = this.href + "&order=desc";
      return this.href;
    }
  });
}

window.descaddURL = descaddURL;


// use an a element to log out
const rxFormSubmit = function(formId) {
 document.getElementById(formId).submit();
}

window.rxFormSubmit = rxFormSubmit;

function fetchResults() {
  const resultsPane = document.getElementById('rdx-search-results');
  const volumePid  = document.getElementById('search-volume-pid').value;
  const query  = document.getElementById('search-query-text').value;
  let searchType = 'partial';
  if (document.getElementById('search-exact').checked) {
    searchType = 'exact';
  }
  url = `/search/volume/pages?volume=${volumePid}&query=${query}&type=${searchType}`;
  fetch(url)
    .then(response => response.json())
    .then(data => {
      ocrAnnotationCount = data.ocr_annotations.length;
      userAnnotationCount = data.user_annotations.length;
      ocrAnnotationUL = document.getElementById('ocr-annotation-results');
      ocrAnnotationUL.innerHTML = '';
      userAnnotationUL = document.getElementById('user-annotation-results');
      userAnnotationUL.innerHTML = '';

      document.getElementById('annotation-count').innerText = `${ocrAnnotationCount}`;
      document.getElementById('user-annotation-count').innerText = `${userAnnotationCount}`;


      if (ocrAnnotationCount > 0) {
        data.ocr_annotations.forEach(result => {
          const anno = JSON.parse(result);
          const resultLi = document.createElement('li');
          const resultA = document.createElement('a');
          resultA.href = '#';
          resultA.addEventListener('click', event => {
            event.preventDefault();
            let parts = window.location.pathname.split('/');
            parts.pop();
            parts.push(anno.canvas__pid);
            history.pushState({}, '', `${window.location.origin}${parts.join('/')}`);
            dispatchEvent(popStateEvent);
          })
          resultA.innerText = `Page ${anno.canvas__position} - number of results ${anno.canvas__position__count}`;
          resultLi.appendChild(resultA);
          ocrAnnotationUL.appendChild(resultLi);
        });
      } else {
        const noResultsP = document.createElement('p');
        noResultsP.innerText = 'No results in the text in this volume';
        ocrAnnotationUL.appendChild(noResultsP);
      }

      if (userAnnotationCount > 0) {
        data.user_annotations.forEach(result => {
          const anno = JSON.parse(result);
          const resultLi = document.createElement('li');
          const resultA = document.createElement('a');
          resultA.href = '#';
          resultA.addEventListener('click', event => {
            event.preventDefault();
            let parts = window.location.pathname.split('/');
            parts.pop();
            parts.push(anno.canvas__pid);
            history.pushState({}, '', `${window.location.origin}${parts.join('/')}`);
            dispatchEvent(popStateEvent);
          })
          resultA.innerText = `Page ${anno.canvas__position}`;
          resultLi.appendChild(resultA);
          userAnnotationUL.appendChild(resultLi);
        });
      } else {
        const noResultsP = document.createElement('p');
        noResultsP.innerText = 'No results in your annotations in this volume';
        userAnnotationUL.appendChild(noResultsP);
      }
      resultsPane.classList.remove('uk-hidden');
    });
}

window.fetchResults = fetchResults;

const popStateEvent = new PopStateEvent('popstate', { state: {} });

const documentReady = function() {
  const searchForm = document.getElementById('manifest-search-form');
  if (searchForm) {
    searchForm.addEventListener('submit', function(event) {
      event.preventDefault();
      fetchResults();
    });
  }

  // component resize
  const rightColumn = document.querySelector('.rx-home-right-column');
  if (rightColumn) {
    const offset = rightColumn.offsetTop;
    document.querySelector('.rx-splash').css('top', offset);
  }

  if (document.URL.replace(/\/+$/, "") == window.location.origin) {
    document.getElementById('rx-nav').classList.add('rx-sticky');
  } else {
    document.getElementById('rx-nav').classList.remove('rx-sticky');
  }

  // show/hide collection info
  var bannerInfo = document.querySelector('.collection-image-info');
  if (bannerInfo) {
    bannerInfo.addEventListener('click', () => {
      if (bannerInfo.classList.contains('collapsed')) {
        bannerInfo.classList.remove('collapsed');
      } else {
        bannerInfo.classList.add('collapsed');
      }
    })
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', documentReady);
} else {
  documentReady();
}
