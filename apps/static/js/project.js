/* Project specific Javascript goes here. */

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

  // Handle collection title and description truncation with tooltips
  const titleElement = document.getElementById('collection-title');
  if (titleElement) {
    const fullTitle = titleElement.textContent.trim();
    const titleLength = fullTitle.length;
    
    // Title is "really long" - reduce font size
    if (titleLength > 60) {
      titleElement.classList.add('title-long');
    }
    
    // Title is "super long" - truncate and add tooltip
    if (titleLength > 100) {
      titleElement.classList.add('title-truncated');
      const truncatedTitle = fullTitle.substring(0, 80) + '...';
      titleElement.textContent = truncatedTitle;
      titleElement.setAttribute('uk-tooltip', `title: ${fullTitle}; pos: bottom; delay: 500`);
      // Reinitialize UIKit tooltip
      if (window.UIkit) {
        window.UIkit.util.ready(() => {
          window.UIkit.tooltip(titleElement);
        });
      }
    }
  }

  // Handle collection description truncation with tooltip
  const descriptionElement = document.getElementById('collection-description');
  if (descriptionElement) {
    const descriptionTextSpan = descriptionElement.querySelector('.description-text');
    if (descriptionTextSpan) {
      const fullDescription = descriptionTextSpan.textContent.trim();
      const descriptionLength = fullDescription.length;
      
      // Description is long - check if it's already truncated or add tooltip
      if (descriptionLength > 300) {
        descriptionElement.classList.add('description-truncated');
        // Check if text ends with ellipsis (already truncated by Django template)
        if (fullDescription.endsWith('...')) {
          // Already truncated, add tooltip with full text
          const untruncatedText = fullDescription.replace(/\.\.\.$/, '');
          descriptionElement.setAttribute('uk-tooltip', `title: ${untruncatedText}; pos: top; delay: 500`);
          if (window.UIkit) {
            window.UIkit.util.ready(() => {
              window.UIkit.tooltip(descriptionElement);
            });
          }
        }
      }
    }
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', documentReady);
} else {
  documentReady();
}
