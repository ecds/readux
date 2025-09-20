import Vue from 'vue'
import VolumeSearch from './components/VolumeSearch.vue'
import VolumeAnnotations from './components/VolumeAnnotations.vue'
import OcrInspector from './components/OcrInspector.vue'
import InfoUrlUnit from './components/InfoUrlUnit.vue'
import InfoUrlSingle from './components/InfoUrlSingle.vue'
import InfoUrlMultiple from './components/InfoUrlMultiple.vue'
import InfoUrlImageLink from './components/InfoUrlImageLink.vue'
import InfoUrlExternal from './components/InfoUrlExternal.vue'
import VolumeExportAnnotationBtn from './components/VolumeExportAnnotationBtn.vue'

var readux = new Vue({
  el: "#v-readux",
  delimiters: ["[[", "]]"],
  components: { 
    VolumeSearch, VolumeAnnotations, OcrInspector, InfoUrlUnit, InfoUrlSingle, InfoUrlMultiple, InfoUrlImageLink, InfoUrlExternal, VolumeExportAnnotationBtn
  },
  data: {
    options: ["title", "author", "date published", "date added"],
    searchPrefix: "?sort=",
    currentSelection: null,
    itemNotFound: false,
    showMoreInfo: false,
    manifestCount: 0,
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