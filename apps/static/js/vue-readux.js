Vue.component("v-volume-image", {
  props: ["srcFirst", "srcLast", "isStartingPage", "isLastItem", "volumeLabel"],
  template: `
    <div class="rx-card-image-container uk-text-center rx-volume-na" v-cloak v-if="!hasImage">
      <span class="rx-item-na" uk-icon="icon: image; ratio: 3"></span>
      <p>Volume is being added or cover is not available.</p>
    </div>
    <img v-else="hasImage" :src="imgSrc" :alt="imgAlt">
  `,
  data: function() {
    return {
      hasImage: true, // visibility of image from src
      imgSrc: ""
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

    if (this.isStartingPage == 1) {
      tester.src = this.srcFirst;
      this.imgSrc = this.srcFirst;
    } else if (this.isLastItem == "yes") {
      tester.src = this.srcLast;
      this.imgSrc = this.srcLast;
    } else {
      this.hasImage = false;
    }
  },
  computed: {
    imgAlt() {
      return `First page of ${this.volumeLabel}`; 
    },
    isFirst() {
      return this.isStartingPage == 1;
    },
    isLast() {
      return (this.isLastItem == "yes")
    }
  }
});

new Vue({
  el: "#v-readux",
  delimiters: ["[[", "]]"],
  data: {
    options: ["title", "author", "date published", "date added"],
    searchPrefix: "?sort=",
    currentSelection: null,
    itemNotFound: false,
  },
  methods: {
    sortBy: function(selection) {
      var value = this.searchPrefix + selection;
      if (window.location !== value) {
        window.location = value;
      }
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
    this.currentSelection = this.$refs["v-attr-sort"].getAttribute("data-sort");
  }
});

