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
        <ul id="rx-search-panel" class="uk-switcher uk-panel-scrollable uk-resize-vertical" uk-height-viewport="offset-bottom: 100">
          <li>
              <div v-if="inText==0" class="rx-padding-extra-small uk-text-small"> No matches in text. </div>
              <div v-else v-for="(match, index) in textData" :key="index" class="rx-padding-extra-small">
                  <div class="uk-text-small">
                    <a :href="'/volume/' + pid + '/page/' + match.canvas_pid"><div class="uk-label rx-label-copy">Page {{match.canvas_index }}</div></a>
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
                    <a :href="'/volume/' + pid + '/page/' + match.canvas_pid"><div class="uk-label rx-label-copy">Page {{match.canvas_index }}</div></a>
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
    <ul uk-accordion class="rx-accordion-container">
      <li class="uk-open">
        <a class="uk-accordion-title uk-label rx-accordion-head" href>Annotation Counts</a>
        <div class="uk-accordion-content rx-accordion-content uk-margin-small-left uk-margin-small-top">
          <div class="rx-info-content-value rx-annotation-badge">{{localManifestCount}} in manifest</div>
          <div class="rx-info-content-value rx-annotation-badge">{{localPageCount}} on page</div>
        </div>
      </li>
    </ul>

    <ul uk-accordion class="rx-accordion-container uk-margin-small-top">
      <li class="uk-open">
        <a class="uk-accordion-title uk-label rx-accordion-head" href>Annotation Index</a>
        <div class="uk-accordion-content rx-accordion-content uk-margin-small-left uk-margin-small-top">
          <div v-if="annotationData.length === 0">
            <span>No annotations to show</span>
          </div>
          <ul v-else>
            <li v-for="annotation in annotationData" :key="annotation.canvas__pid" >
              <div v-if="annotation.canvas__position__count">
                <a :href="annotation.canvas__pid"><span class="uk-label rx-label-copy">Page {{ annotation.canvas__position }}</span></a> ‧ {{annotation.canvas__position__count}} annotations
              </div>
            </li>
          </ul>
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
        <span>{{ label }}</span>
        <div>
          <span class="uk-label rx-label-copy" @click="copyToClipboard">Copy</span>
        </div>
      </div>
      <div class="rx-info-content-value">
        <a :href="url" class="rx-anchor" target="_blank">{{ url }}</a>
      </div>
    </div>
  `,
  methods: {
    copyToClipboard() {
      if (navigator.clipboard) {
        navigator.clipboard.writeText(this.url)
          .then(() => {
            alert(`You have copied: ${this.url}`);
          })
          .catch(() => {
            alert("Something went wrong with copy.");
          });
      } else {
        alert("Clipboard API not supported in this browser.");
      }
    }
  }
});

Vue.component("v-info-content-url-unit", {
  props: ["url"],
  template: `
    <div class="rx-info-content-value uk-flex-between rx-flex">
      <a :href="url" class="rx-anchor" target="_blank">{{ url }}</a>
      <div>
        <span class="uk-label rx-label-copy" @click="copyToClipboard">Copy</span>
      </div>
    </div>
  `,
  methods: {
    copyToClipboard() {
      if (navigator.clipboard) {
        navigator.clipboard.writeText(this.url)
          .then(() => {
            alert(`You have copied: ${this.url}`);
          })
          .catch(() => {
            alert("Something went wrong with copy.");
          });
      } else {
        alert("Clipboard API not supported in this browser.");
      }
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
        <span>{{ label }}</span>
        <div>
          <span class="uk-label rx-label-copy" @click="copyToClipboard">Copy</span>
        </div>
      </div>
      <div class="rx-info-content-value">
        <a :href="localUrl" class="rx-anchor" target="_blank">{{ localUrl }}</a>
      </div>
    </div>
  `,
  methods: {
    copyToClipboard() {
      if (navigator.clipboard) {
        navigator.clipboard.writeText(this.localUrl)
          .then(() => {
            alert(`You have copied: ${this.localUrl}`);
          })
          .catch(() => {
            alert("Something went wrong with copy.");
          });
      } else {
        alert("Clipboard API not supported in this browser.");
      }
    }
  },
  mounted() {
    var vm = this;
    window.addEventListener("canvasswitch", function (event) {
      if (event.detail) {
        var protocol = window.location.protocol;
        var host = window.location.host;
        var canvas = event.detail.canvas;
        var volume = vm.volume;
        var url = protocol + "//" + host + volume + "/page/" + canvas;
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
        <span v-if="localUrls !== undefined">{{ label }}</span>
        <div>
          <span class="uk-label rx-label-copy" @click="copyToClipboard" v-if="localUrls !== undefined">Copy</span>
        </div>
      </div>
      <div class="rx-info-content-value">
        <a :href="pageresource" class="rx-anchor" target="_blank">{{ pageresource }}</a>
      </div>
    </div>
  `,
  methods: {
    copyToClipboard() {
      if (navigator.clipboard) {
        navigator.clipboard.writeText(this.localUrls)
          .then(() => {
            alert(`You have copied: ${this.localUrls}`);
          })
          .catch(() => {
            alert("Something went wrong with copy.");
          });
      } else {
        alert("Clipboard API not supported in this browser.");
      }
    }
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
          var url = localpagelink + "/" + vm.canvas + "/full/full/0/default.jpg";
          vm.localUrls = url;
          vm.can = vm.canvas;
        }
      }
    });
  },
});

Vue.component("v-ocr-inspector", {
  props: { pagelink: { type: String, default: "" } },
  data() {
    return {
      pagetext: "",
      isLoading: false,
      canvas: null,
      pageresource: null,
      localUrls: "",
      can: null,
      overlayChecked: false,
      hasOcrAvailable: false,
      nodeHandlers: null
    };
  },
  created() { this.nodeHandlers = new WeakMap(); },
  computed: {
    hasText() {
      return !!(this.pagetext && this.pagetext.trim().length);
    },
    copyDisabled() {
      return this.isLoading || !this.hasText;
    },
    // ✅ Disable the toggle if loading OR no OCR available OR no text
    overlayDisabled() {
      return this.isLoading || !this.hasOcrAvailable || !this.hasText;
    }
  },
  template: `
  <div class="rx-info-content">

    <div class="ocr-notification uk-margin-small-bottom" v-if="!isLoading && !hasText">
      This page does not have any usable OCR.
    </div>

    <div class="rx-info-content-label uk-flex-between rx-flex" style="align-items:center;">
      <span>Overlay OCR on Page</span>
      <div>
        <label class="uk-switch" for="ocr-overlay">
          <input
            type="checkbox"
            id="ocr-overlay"
            v-model="overlayChecked"
            :disabled="overlayDisabled"
            @change="onOverlayToggle"
          >
          <div class="uk-switch-slider"></div>
        </label>
      </div>
    </div>

    <div class="rx-info-content-value uk-margin-small-bottom uk-text-italic">
      Superimpose OCR text as a layer on top of the scanned volume image. We try our best to align the text to image but some may miss.
    </div>

    <div class="rx-info-content-label uk-flex-between rx-flex" style="align-items:center;">
      <span>Plain OCR Text</span>
      <div
        class="uk-label rx-label-copy"
        :class="{ 'uk-disabled': copyDisabled }"
        :aria-disabled="copyDisabled"
        role="button"
        tabindex="0"
        @click="!copyDisabled && copyText()"
        @keydown.enter.prevent="!copyDisabled && copyText()"
        @keydown.space.prevent="!copyDisabled && copyText()"
        style="user-select:none; cursor:pointer;"
      >
        <span uk-icon="icon: copy; ratio: 0.5"></span>
        Copy
      </div>
    </div>

    <div class="rx-info-content-value">
      <div v-if="isLoading" class="uk-flex uk-flex-middle" style="gap:.5rem;">
        <span uk-spinner="ratio: 0.6"></span>
        <span>Loading OCR…</span>
      </div>
      <div v-else-if="hasText" class="scrollable-container">{{ pagetext }}</div>
      <em v-else>OCR text unavailable</em>
    </div>
  </div>
  `,
  methods: {
    async copyText() {
      try {
        await navigator.clipboard.writeText(this.pagetext);
        if (window.UIkit?.notification) {
          UIkit.notification({ message: "Copied!", status: "success", timeout: 1200 });
        }
      } catch (err) { console.error("Copy failed:", err); }
    },

    onOverlayToggle() {
      this.applyOverlay(this.overlayChecked);
    },
    getOcrNodes() {
      return document.querySelectorAll("div.openseadragon-canvas div span");
    },
    addBlockHandlers(node) {
      if (this.nodeHandlers.has(node)) return;
      const handlers = {
        mouseup:   (e) => { e.stopPropagation(); e.preventDefault(); },
        mousemove: (e) => { e.stopPropagation(); e.preventDefault(); },
        mousedown: (e) => { e.stopPropagation(); e.preventDefault(); }
      };
      node.addEventListener("mouseup", handlers.mouseup);
      node.addEventListener("mousemove", handlers.mousemove);
      node.addEventListener("mousedown", handlers.mousedown);
      this.nodeHandlers.set(node, handlers);
    },
    removeBlockHandlers(node) {
      const h = this.nodeHandlers.get(node);
      if (!h) return;
      node.removeEventListener("mouseup", h.mouseup);
      node.removeEventListener("mousemove", h.mousemove);
      node.removeEventListener("mousedown", h.mousedown);
      this.nodeHandlers.delete(node);
    },
    applyOverlay(enabled) {
      const nodes = this.getOcrNodes();
      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i];
        if (enabled) {
          n.style.backgroundColor = "white";
          n.style.fontWeight = "bold";
          n.style.color = "rgb(149, 9, 83)";
          this.addBlockHandlers(n);
        } else {
          n.style.backgroundColor = "transparent";
          n.style.fontWeight = "";
          n.style.color = "transparent";
          this.removeBlockHandlers(n);
        }
      }
    },

    // ===== CANVAS SWITCH HANDLER =====
    async handleCanvasSwitch(detail) {
      const nextCanvas = detail?.canvas;

      this.isLoading = true;
      this.canvas = nextCanvas;

      // Prefer event-provided availability
      let availableFromEvent = typeof detail?.ocr !== "undefined" ? !!detail.ocr : null;

      try {
        if (nextCanvas && nextCanvas !== "all") {
          const { data } = await axios.get(`iiif/resource/${nextCanvas}`);
          this.pageresource = data.resource || null;
          this.pagetext = data.text || "";
        } else {
          this.pageresource = null;
          this.pagetext = "";
        }

        if (this.pagelink && nextCanvas) {
          this.localUrls = `${this.pagelink}/${nextCanvas}/full/full/0/default.jpg`;
          this.can = nextCanvas;
        }

        // Determine availability
        this.hasOcrAvailable = (availableFromEvent !== null) ? availableFromEvent : this.hasText;

        // ✅ If toggle cannot be used (no text or not available), force it off and clear styles
        const overlayPossible = this.hasOcrAvailable && this.hasText && !this.isLoading;
        if (!overlayPossible && this.overlayChecked) {
          this.overlayChecked = false;
          this.applyOverlay(false);
        }
        // If possible and already on, re-apply after DOM updates
        if (overlayPossible && this.overlayChecked) {
          this.$nextTick(() => this.applyOverlay(true));
        } else if (!overlayPossible) {
          this.applyOverlay(false);
        }

      } catch (err) {
        console.error("Failed to fetch page text:", err);
        this.pagetext = "";
        this.hasOcrAvailable = availableFromEvent !== null ? availableFromEvent : false;
        this.overlayChecked = false;
        this.applyOverlay(false);
      } finally {
        this.isLoading = false;
      }
    }
  },
  mounted() {
    this._onCanvasSwitch = (event) => {
      this.handleCanvasSwitch(event?.detail || {});
    };
    window.addEventListener("canvasswitch", this._onCanvasSwitch);
  },
  beforeDestroy() {
    window.removeEventListener("canvasswitch", this._onCanvasSwitch);
    const nodes = this.getOcrNodes();
    for (let i = 0; i < nodes.length; i++) this.removeBlockHandlers(nodes[i]);
  }
});

var readux = new Vue({
  el: "#v-readux",
  delimiters: ["[[", "]]"],
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