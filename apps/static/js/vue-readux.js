import { createApp } from 'vue'
import VolumeSearch from './components/VolumeSearch.vue'
import VolumeAnnotations from './components/VolumeAnnotations.vue'
import OcrInspector from './components/OcrInspector.vue'
import InfoUrlUnit from './components/InfoUrlUnit.vue'
import InfoUrlSingle from './components/InfoUrlSingle.vue'
import InfoUrlMultiple from './components/InfoUrlMultiple.vue'
import InfoExport from './components/InfoExport.vue'
import InfoUrlExternal from './components/InfoUrlExternal.vue'
import VolumeExportAnnotationBtn from './components/VolumeExportAnnotationBtn.vue'

const app = createApp({
  components: {
    VolumeSearch,
    VolumeAnnotations,
    OcrInspector,
    InfoUrlUnit,
    InfoUrlSingle,
    InfoUrlMultiple,
    InfoExport,
    InfoUrlExternal,
    VolumeExportAnnotationBtn,
  },
  data() {
    return {
      options: ["title", "author", "date published", "date added"],
      searchPrefix: "?sort=",
      currentSelection: null,
      itemNotFound: false,
      showMoreInfo: false,
      manifestCount: 0,
    }
  },
  methods: {
    sortBy(selection) {
      const value = this.searchPrefix + selection
      if (window.location !== value) {
        window.location = value
      }
    },
    toggleMoreInfo() {
      this.showMoreInfo = !this.showMoreInfo
    },
  },
  mounted() {
    if (this.$refs["v-attr-sort"]) {
      this.currentSelection = this.$refs["v-attr-sort"].getAttribute("data-sort")
    }
    if (window.location.href.includes("?q=")) {
      this.showMoreInfo = true
    }
  },
})

// Custom delimiters so Vue expressions don't clash with Django template tags.
// Must be set before mount().
app.config.compilerOptions.delimiters = ['[[', ']]']

app.mount('#v-readux')
