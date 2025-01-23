console.log("HEY");

$( document ).ready(function() {
  console.log( "ready!" );
});


Vue.component("v-volume-image", {
  props: ["imgSrc", "volumeLabel"],
  template: `
    <div class="uk-text-center rx-volume-na" v-cloak v-if="!hasImage">
      <span class="rx-item-na" uk-icon="icon: image; ratio: 2"></span>
      <p>Volume is being added or cover is not available.</p>
    </div>
    <img class="rx-title-image" v-else="hasImage" :src="imgSrc" :alt="imgAlt">
  `,
  data: function () {
    return {
      hasImage: true, // visibility of image from src
    };
  },
  mounted() {
    var vm = this;
    var tester = new Image();
    tester.addEventListener("load", function () {
      vm.hasImage = true;
    });
    tester.addEventListener("error", function () {
      vm.hasImage = false;
    });
    tester.src = this.imgSrc;
  },
  computed: {
    imgAlt() {
      return `First page of ${this.volumeLabel}`;
    },
  },
});

Vue.component("v-volume-search", {
  template: `
  <div class="rx-volume-search">
    <div class="uk-search uk-search-default rx-page-search-container">
      <span uk-search-icon></span>
      <input class="uk-search-input" type="search" id="volume-search" placeholder="Search in volume text or annotations" name="q" 
        v-model="keyword" @keypress.enter="getSearchResults()"/>
    </div>
    <div class="uk-text-small uk-margin-small-top uk-margin-small-left">Use "" to match whole words.</div>
    
    <div v-if="hasResults">
        <ul class="uk-text-bold uk-text-large uk-tab" data-uk-tab="{connect:'#rx-search-panel'}">
          <li><a href="">Text ({{inText}})</a></li>
          <li><a href="">Annotation ({{inAnnotations}})</a></li>
        </ul>
        <ul id="rx-search-panel" class="uk-switcher uk-overflow-auto uk-width-expand" uk-height-viewport="offset-bottom: 100">
          <li>
              <div v-if="inText==0" class="rx-padding-extra-small uk-text-small"> No matches in text. </div>
              <div v-else v-for="(match, index) in textData" :key="index" class="rx-padding-extra-small">
                  <div class="uk-text-small">
                    <a :href="'/volume/' + pid + '/page/' + match.canvas_pid"><div class="uk-label rx-label-solid">Page {{match.canvas_index }}</div></a>
                    <div class="uk-inline-block" style="vertical-align: middle"> · {{ match.canvas_match_count }} match<span v-if="match.canvas_match_count > 1">es</span></div>
                  </div>
                  <ul class="uk-text-small rx-line-height-sm uk-margin-small-bottom uk-list uk-list-bullet">
                      <li v-for="(context, contextIndex) in match.context" :key="contextIndex" v-html="context" class="uk-margin-small-top"></li>
                  </ul>
              </div>
          </li>
          <li>
              <div v-if="inAnnotations==0" class="rx-padding-extra-small uk-text-small"> No matches in annotations. </div>
              <div v-else v-for="(match, index) in annotationData" :key="index" class="rx-padding-extra-small">
                  <div class="uk-text-small">
                    <a :href="'/volume/' + pid + '/page/' + match.canvas_pid"><div class="uk-label rx-label-solid">Page {{match.canvas_index }}</div></a>
                    <div class="uk-inline-block" style="vertical-align: middle"> · {{ match.canvas_match_count }} match<span v-if="match.canvas_match_count > 1">es</span></div>
                  </div>
                  <ul class="uk-text-small rx-line-height-sm uk-margin-small-bottom uk-list uk-list-bullet">
                      <li v-for="(context, contextIndex) in match.context" :key="contextIndex" v-html="context" class="uk-margin-small-top"></li>
                  </ul>
              </div>
          </li>
        </ul>
    </div>
    <div v-else>
      <div v-if="emptyMessage != ''" class="uk-alert uk-margin-small-top uk-margin-remove-bottom">{{emptyMessage}}</div>
    </div>
  </div>
  `,
  props: ['pid'],
  data() {
    return {
      searchResults: [],
      annotationData: [],
      textData: [],
      keyword: this.keyword,
      inAnnotations: 0,
      inText: 0,
      emptyMessage: ""
    };
  },
  methods: {
    getSearchResults() {
      try {
        if (this.keyword=="" || this.keyword==undefined) {
          this.emptyMessage =  "Type a keyword to search";
        } else {
          $this = this;
          axios.get('/search/volume/pages?keyword=' + this.keyword + '&volume_id=' + this.pid)
            .then(function (response) {
              this.searchResults = response.data; // Assuming data is an array of results
              if (this.searchResults.hasOwnProperty("matches_in_annotations")) {
                $this.inAnnotations = this.searchResults.matches_in_annotations.total_matches_in_volume;
                $this.inText = this.searchResults.matches_in_text.total_matches_in_volume;
                $this.annotationData = this.searchResults.matches_in_annotations.volume_matches;
                $this.textData = this.searchResults.matches_in_text.volume_matches;
              }
              $this.emptyMessage = ($this.hasResults == 0) ? "No matches in either annotations or text." : this.emptyMessage;
            })
            .catch(function (error) {
              console.log(error);
            });
        }
      } catch (error) {
        console.error('Error fetching volume search data via API call to ElasticSearch:', error);
      }
    }
  },
  computed: {
    hasResults: function () {
        return this.inAnnotations + this.inText;
    },
  },
});

Vue.component("v-volume-export-annotation-btn", {
  props: ["manifestCount"],
  template: `
  <div class="rx-info-content" v-if="isExportVisible">
    <slot></slot>
  </div>
  `,
  data: function () {
    return {
      localManifestCount: this.manifestCount,
      isExportVisible: true,
    };
  },
  mounted() {
    var vm = this;
    window.addEventListener("canvasswitch", function (event) {
      if (!event) return;

      if (event.detail.annotationsOnPage) {
        if (event.detail.annotationAdded) {
          vm.localManifestCount++;
        }
        if (event.detail.annotationDeleted) {
          vm.localManifestCount--;
        }
        vm.isExportVisible = vm.localManifestCount >= 1 ? true : false;
      }

      if (event.detail && event.detail.canvas && !location.pathname.includes(event.detail.canvas)) {
        history.pushState({}, '', event.detail.canvas);
      }
    });
    vm.isExportVisible = vm.localManifestCount >= 1 ? true : false;

  },
});


Vue.component("v-volume-annotations", {
  props: ["manifestCount", "pageCount"],
  template: `
  <div class="rx-info-content">
    <div class="rx-info-content-label rx-padding-bottom-10">Annotation Counts</div>
    <div class="rx-info-content-value rx-annotation-badge">{{localManifestCount}} in manifest</div>
    <div class="rx-info-content-value rx-annotation-badge">{{localPageCount}} on page</div>

    <ul uk-accordion class="rx-accordion-container">
      <li class="uk-open">
        <a class="rx-accordion-handle rx-info-content-label uk-accordion-title" href="#">Annotation Index</a>
        <div class="uk-accordion-content rx-accordion-content">
          <li v-for="annotation in annotationData" :key="annotation.canvas__pid" >
            <div v-if="annotation.canvas__position__count">
              <a :href="annotation.canvas__pid"><span class="rx-btn rx-fixed-width-100">Page {{ annotation.canvas__position }}</span></a> ‧ {{annotation.canvas__position__count}} annotations
            </div>
          </li>
        </div>
      </li>
    </ul>
  </div>
  `,
  data: function () {
    return {
      hasImage: false, // visibility of image from src
      localManifestCount: this.manifestCount,
      localPageCount: this.pageCount,
      annotationData: {},
    };
  },
  mounted() {
    var vm = this;
    this.annotationData = JSON.parse(
      document.getElementById("context").textContent
    ).json_data;
    window.addEventListener("canvasswitch", function (event) {
      if (event.detail.annotationAdded) {
        var createNewPage = true;
        for (var i = 0; i < vm.annotationData.length; i++) {
          if (vm.annotationData[i].canvas__pid === event.detail.canvas) {
            vm.annotationData[i].canvas__position__count++;
            createNewPage = false;
          }
        }
        if (createNewPage) {
          var canvas_pid_num = (event.detail.canvas.match(/\d+$/) || []).pop();
          vm.annotationData = vm.annotationData.concat({
            canvas__manifest__label:
              vm.annotationData[0].canvas__manifest__label,
            canvas__pid: event.detail.canvas,
            canvas__position: parseInt(canvas_pid_num) + 1,
            canvas__position__count: event.detail.annotationsOnPage,
          });
        }
        vm.localManifestCount++;
      }
      if (event.detail.annotationDeleted) {
        for (var i = 0; i < vm.annotationData.length; i++) {
          if (vm.annotationData[i].canvas__pid === event.detail.canvas)
            vm.annotationData[i].canvas__position__count--;
        }
        vm.localManifestCount--;
      }
      vm.localPageCount = event.detail.annotationsOnPage;
    });
  },
});


Vue.component("v-info-content-url-single", {
  props: ["label", "url"],
  template: `
    <div class="rx-info-content">
      <div class="rx-info-content-label uk-flex-between rx-flex">
        <span>{{label}}</span>
        <div>
          <span class="uk-label rx-label-copy"
            v-clipboard:copy="url"
            v-clipboard:success="onCopy"
            v-clipboard:error="onError">Copy</span>
        </div>
      </div>
      <div class="rx-info-content-value">
        <a v-bind:href="url" class="rx-anchor"
          target="_blank">{{url}}</a>
      </div>
    </div>
  `,
  methods: {
    onCopy() {
      alert(`You have copied: ${this.url}`);
    },
    onError() {
      alert(`Something went wrong with copy.`);
    }
  }
});

Vue.component("v-info-content-url-unit", {
  props: ["url"],
  template: `
    <div class="rx-info-content-value uk-flex-between rx-flex">
      <a v-bind:href="url" class="rx-anchor"
        target="_blank">{{url}}</a>
      <div>
        <span class="uk-label rx-label-copy"
          v-clipboard:copy="url"
          v-clipboard:success="onCopy"
          v-clipboard:error="onError">Copy</span>
      </div>
    </div>
  `,
  methods: {
    onCopy() {
      alert(`You have copied: ${this.url}`);
    },
    onError() {
      alert(`Something went wrong with copy.`);
    }
  }
});

Vue.component("v-info-content-url-multiple", {
  props: ["label"],
  template: `
    <div class="rx-info-content">
      <div class="rx-info-content-label">
        <span>{{label}}</span>
      </div>
      <div>
        <slot></slot>
      </div>
    </div>
  `,
});

// url copy component made for when the url is modified externally (outside Vue.js)
Vue.component("v-info-content-url-external", {
  props: ["label", "url", "volume"],
  data: function () {
    return {
      localUrl: this.url,
    };
  },
  template: `
    <div class="rx-info-content">
      <div class="rx-info-content-label uk-flex-between rx-flex ">
        <span>{{label}}</span>
        <div>
          <span class="uk-label rx-label-copy"
            v-clipboard:copy="localUrl"
            v-clipboard:success="onCopy"
            v-clipboard:error="onError">Copy</span>
        </div>
      </div>
      <div class="rx-info-content-value">
        <a v-bind:href="localUrl" class="rx-anchor"
          target="_blank">{{localUrl}}</a>
      </div>
    </div>
  `,
  methods: {
    onCopy() {
      alert(`You have copied: ${this.localUrl}`);
    },
    onError() {
      alert(`Something went wrong with copy.`);
    },
  },
  mounted() {
    var vm = this;
    window.addEventListener("canvasswitch", function (event) {
      if (event.detail) {
        var protocol = window.location.protocol;
        var host = window.location.host;
        var canvas = event.detail.canvas;
        var volume = vm.volume;
        var url =
          protocol + "//" + host + volume + "/page/" + canvas;
        vm.localUrl = url;
        vm.vol = volume;
      }
    });
  },
});

// url copy component made for when the url is modified externally (outside Vue.js) - trying image link
Vue.component("v-info-content-url-image-link", {
  props: ["label", "pagelink"],
  data: function () {
    return {
      localUrls: this.url,
      pageresource: this.pageresource,
    };
  },
  template: `
    <div class="rx-info-content">
      <div class="rx-info-content-label uk-flex-between rx-flex ">
        <span v-if="localUrls !== undefined">{{label}}</span>
        <div>
          <span class="uk-label rx-label-copy"
            v-clipboard:copy="localUrls"
            v-clipboard:success="onCopy"
            v-clipboard:error="onError" v-if="localUrls !== undefined">Copy</span>
        </div>
      </div>
      <div class="rx-info-content-value">
        <a v-bind:href="pageresource" class="rx-anchor"
          target="_blank">{{pageresource}}</a>
      </div>
    </div>
  `,
  methods: {
    onCopy() {
      alert(`You have copied: ${this.localUrls}`);
    },
    onError() {
      alert(`Something went wrong with copy.`);
    },
  },
  mounted() {
    var vm = this;
    window.addEventListener("canvasswitch", function (event) {
      if (event.detail && vm.canvas !== event.detail.canvas) {
        var protocol = window.location.protocol;
        var host = window.location.host;
        vm.canvas = event.detail.canvas;
        var volume = event.detail.volume;
        var localpagelink = vm.pagelink;

        if (vm.canvas !== 'all') {
          axios.get(`iiif/resource/${event.detail.canvas}`)
            .then(response => {
              vm.pageresource = response.data.resource;
              vm.pagetext = response.data.text;
            }).catch(error => {
              console.error(error);
            });
          var url =
            localpagelink + "/" + vm.canvas + "/full/full/0/default.jpg";
          vm.localUrls = url;
          vm.can = vm.canvas;
        }
      }
    });
  },
});

// adapted from (url copy component made for when the url is modified externally (outside Vue.js)) - now page text modal
Vue.component("v-info-content-url-page-text", {
  props: [],
  data: function () {
    return {
      pagetext: this.pagetext,
    };
  },
  template: `
  <div id="text-overlay-modal" uk-modal>
    <div class="uk-modal-dialog uk-modal-body">
        <button class="uk-modal-close-default" type="button" uk-close></button>
        <h2 class="uk-modal-title">Text</h2>
        <p>{{pagetext}}</p>
    </div>
  </div>
  `,
  methods: {
  },
  mounted() {
    var vm = this;
    window.addEventListener("canvasswitch", function (event) {
      if (event.detail && vm.canvas !== event.detail.canvas) {
        var protocol = window.location.protocol;
        var host = window.location.host;
        vm.canvas = event.detail.canvas;
        var volume = event.detail.volume;
        var localpagelink = vm.pagelink;
        if (event.detail.canvas && event.detail.canvas !== 'all') {
          axios.get(`iiif/resource/${event.detail.canvas}`)
            .then(response => {
              vm.pageresource = response.data.resource;
              vm.pagetext = response.data.text;
            }).catch(error => { console.log(error); })
        }
        var url =
          localpagelink + "/" + vm.canvas + "/full/full/0/default.jpg";
        vm.localUrls = url;
        vm.can = vm.canvas;
      }
    });
  },
});

var readux = new Vue({
  el: "#v-readux",
  delimiters: ["[[", "]]"],
  component: {
    VueClipboard
  },
  data: {
    options: ["title", "author", "date published", "date added"],
    searchPrefix: "?sort=",
    currentSelection: null,
    itemNotFound: false,
    showMoreInfo: false,
  },
  methods: {
    sortBy: function (selection) {
      var value = this.searchPrefix + selection;
      if (window.location !== value) {
        window.location = value;
      }
    },

    toggleMoreInfo: function () {
      this.showMoreInfo = !this.showMoreInfo
    }

    // ascaddURL: function(element) {
    // 	$(element).attr('href', function () {
    // 		if (window.location.search.length == 0) {
    // 			return this.href + '?sort=title&order=asc';
    // 		} else if (window.location.search.match(/[?&]order=asc/gi)) {
    // 			this.href = this.href.replace('order=asc', 'order=asc');
    // 			return this.href;
    // 		} else if (window.location.search.match(/[?&]order=desc/gi)) {
    // 			this.href = this.href.replace('order=desc', 'order=asc');
    // 			return this.href;
    // 		} else {
    // 			return this.href + '&order=asc';
    // 		}
    // 	});
    // },

    // descaddURL: function(element) {
    // 	$(element).attr('href', function () {
    // 		if (window.location.search.length == 0) {
    // 			return this.href + '?sort=title&order=desc';
    // 		} else if (window.location.search.match(/[?&]order=asc/gi)) {
    // 			this.href = this.href.replace('order=asc', 'order=desc');
    // 			return this.href;
    // 		} else if (window.location.search.match(/[?&]order=desc/gi)) {
    // 			this.href = this.href.replace('order=desc', 'order=desc');
    // 			return this.href;
    // 		} else {
    // 			return this.href + '&order=desc';
    // 		}
    // 	});
    // }
  },

  mounted: function () {
    if (this.$refs["v-attr-sort"]) {
      this.currentSelection = this.$refs["v-attr-sort"].getAttribute(
        "data-sort"
      );
    }

    if (window.location.href.includes("?q=")) {
      this.showMoreInfo = true;
    }
  }
});

// Initialize selectize for search filters
jQuery(function () {
  jQuery("#id_collection").selectize({
    plugins: ["clear_button"],
    placeholder: 'Select one or more...',
  });
  jQuery("#id_author").selectize({
    plugins: ["clear_button"],
    placeholder: 'Select one or more...',
  });
  jQuery("#id_language").selectize({
    plugins: ["clear_button"],
    placeholder: 'Select one or more...'
  });
});