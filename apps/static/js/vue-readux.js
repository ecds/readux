new Vue({
  el: "#v-readux",
  delimiters: ["[[", "]]"],
  data: {
    options: ["title", "author", "date published", "date added"],
    searchPrefix: "?sort=",
    currentSelection: null
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

