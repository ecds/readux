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
      isExportVisible: false,
    };
  },
  mounted() {
    var vm = this;
    window.addEventListener("canvasswitch", function (event) {
      if (event.detail.annotationsOnPage) {
        if (event.detail.annotationAdded) {
          vm.localManifestCount++;
        }
        if (event.detail.annotationDeleted) {
          vm.localManifestCount--;
        }
        vm.isExportVisible = vm.localManifestCount >= 1 ? true : false;
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
              <a :href="annotation.canvas__pid"><span class="uk-label rx-label-copy rx-fixed-width-100">Canvas {{ annotation.canvas__position }}</span></a> ‧ {{annotation.canvas__position__count}} annotations
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
      <div class="rx-info-content-label uk-flex-between rx-flex ">
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
  props: ["label", "url"],
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
        var volume = event.detail.volume;
        var url =
          protocol + "//" + host + "/volume/" + volume + "/page/" + canvas;
        vm.localUrl = url;
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
    sortBy: function(selection) {
      var value = this.searchPrefix + selection;
      if (window.location !== value) {
        window.location = value;
      }
    },

    toggleMoreInfo: function(){
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

  mounted: function() {
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

