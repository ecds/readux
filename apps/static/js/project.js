/* Project specific Javascript goes here. */
$(document).ready(function() {
  var bannerInfo = $(".collection-image-info");
  bannerInfo.on("click", function() {
    $(this).toggleClass("collasped");
  });
});

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


// use an a element to log out
function rxFormSubmit(formId) {
  $(`#${formId}`).submit();
}


// component resize
$(document).ready(function() {
  var offset = $(".rx-home-right-column").offset().top;
  $(".rx-splash").css("top", offset);

  if (document.URL.replace(/\/+$/, "") == window.location.origin) {
    $("#rx-nav").addClass("rx-sticky");
  } else {
    $("#rx-nav").removeClass("rx-sticky");
  }

  // if (window.location.href.includes("?q=")) {
  //   UIkit.offcanvas($('#offcanvas-usage')).show();
  // }
});

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
      userAnnotationIndexCount = data.user_annotations_index.length;
      ocrAnnotationUL = document.getElementById('ocr-annotation-results');
      ocrAnnotationUL.innerHTML = '';
      userAnnotationUL = document.getElementById('user-annotation-results');
      userAnnotationUL.innerHTML = '';
      userAnnotationIndexUL = document.getElementById('user-annotations-index-results');
      userAnnotationIndexUL.innerHTML = '';

      document.getElementById('annotation-count').innerText = `${ocrAnnotationCount}`;
      document.getElementById('user-annotation-count').innerText = `${userAnnotationCount}`;
      document.getElementById('user-annotations-index-count').innerText = `${userAnnotationIndexCount}`;


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
          resultA.innerText = `Canvas ${anno.canvas__position} - number of results ${anno.canvas__position__count}`;
          resultLi.appendChild(resultA);
          ocrAnnotationUL.appendChild(resultLi);
        });
      } else {
        const noResultsP = document.createElement('p');
        noResultsP.innerText = 'No results in the text in this volume';
        ocrAnnotationUL.appendChild(noResultsP);
      }

      if (userAnnotationIndexCount > 0) {
        data.user_annotations_index.forEach(result => {
          const annos = JSON.parse(result);
          const resultsLi = document.createElement('li');
          const resultsA = document.createElement('a');
          resultsA.href = '#';
          resultsA.addEventListener('click', event => {
            event.preventDefault();
            let parts = window.location.pathname.split('/');
            parts.pop();
            parts.push(annos.canvas__pid);
            history.pushState({}, '', `${window.location.origin}${parts.join('/')}`);
            dispatchEvent(popStateEvent);
          })
          resultsA.innerText = `Canvas ${annos.canvas__position} - number of results ${annos.canvas__position__count}`;
          resultsLi.appendChild(resultsA);
          userAnnotationIndexUL.appendChild(resultsLi);
        });
      } else {
        const noResultsPs = document.createElement('p');
        noResultsPs.innerText = 'No results in your annotations in this volume';
        userAnnotationIndexUL.appendChild(noResultsPs);
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
          resultA.innerText = `Canvas ${anno.canvas__position}`;
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

const popStateEvent = new PopStateEvent('popstate', { state: {} });
$(document).ready(function() {
  const searchForm = document.getElementById('manifest-search-form');
  if (searchForm) {
    searchForm.addEventListener('submit', function(event) {
      event.preventDefault();
      fetchResults();
    });
  }
});

/*
  Trigger a `popState` event when search result is clicked. We do this
  to 1) not have to make a full http call to jump to a different canvas
  2) make sure Mirador does all the stuff it needs to do to load a
  different canvas.
*/
function goToCanvas(canvas) {
  console.log("goToCanvas -> canvas", canvas)
  history.pushState({}, '', canvas);
  dispatchEvent(popStateEvent);
}
