Vue.component("v-volume-image", {
  props: ["imgSrc", "volumeLabel"],
  template: `
    <div class="uk-text-center rx-volume-na" v-cloak v-if="!hasImage">
      <span class="rx-item-na" uk-icon="icon: image; ratio: 2"></span>
      <p>Volume is being added or cover is not available.</p>
    </div>
    <img v-else="hasImage" :src="imgSrc" :alt="imgAlt">
  `,
  data: function() {
    return {
      hasImage: true, // visibility of image from src
    };
  },
  mounted() {
    var vm = this;
    var tester = new Image();
    tester.addEventListener("load", function() {
      vm.hasImage = true;
    });
    tester.addEventListener("error", function() {
      vm.hasImage = false;
    });
    tester.src = this.imgSrc;
  },
  computed: {
    imgAlt() {
      return `First page of ${this.volumeLabel}`; 
    },
  }
});

Vue.component("v-volume-annotations", {
  props: ["manifestCount", "pageCount"],
  template: `
  <ul class="uk-subnav uk-subnav-pill" uk-switcher v-cloak v-if="!hasImage">
    <li><a href="#" class="rx-btn-annotation"> {{manifestCount}} annotations in manifest</a></li>
    <li><a href="#" class="rx-btn-annotation"> {{pageCount}} annotations on page</a></li>
  </ul>
  `,
  data: function () {
    return {
      hasImage: false, // visibility of image from src
    };
  },
  mounted() {
    var vm = this;
    window.addEventListener("canvasswitch", function (event) {
      if (event.detail.annotationsOnPage) {
        vm.pageCount = event.detail.annotationsOnPage;
      }
    });
  },
  computed: {
    imgAlt() {
      return ``;
    },
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
  props: ["refName"],
  data: function() {
    return {
      url: "",
      label: ""
    };
  },
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
        <a v-bind:href="url" class="rx-anchor" v-bind:ref="refName"
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
  },
  mounted() {
    // this.currentSelection = this.$refs["v-attr-sort"].getAttribute("data-sort");
  }
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
  }
});

