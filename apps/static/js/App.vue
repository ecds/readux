<template>
  <div id="v-readux">
    <!-- Example usage & parity with your original root instance -->
    <div class="uk-margin">
      <VolumeImage :img-src="volumeImgSrc" :volume-label="volumeLabel" />
    </div>

    <VolumeSearch :pid="pid" />

    <VolumeExportAnnotationBtn :manifest-count="manifestCount">
      <!-- Whatever content to show inside the button region when visible -->
      <button class="uk-button uk-button-default">Export Annotations</button>
    </VolumeExportAnnotationBtn>

    <VolumeAnnotations :manifest-count="manifestCount" :page-count="pageCount" />

    <OcrInspector :pagelink="pageLinkBase" />

    <!-- Info URL components -->
    <InfoUrlSingle label="Volume URL" :url="volumeUrl" />
    <InfoUrlMultiple label="Related URLs">
      <InfoUrlUnit :url="related1" />
      <InfoUrlUnit :url="related2" />
    </InfoUrlMultiple>
    <InfoUrlExternal label="Shareable Page URL" :url="shareUrl" :volume="volumeBase" />
    <InfoUrlImageLink label="Page Image" :pagelink="pageLinkBase" />

    <!-- Sort + More Info mirrors original root behavior -->
    <div class="uk-margin">
      <select ref="v-attr-sort" class="uk-select" :data-sort="currentSelection" v-model="currentSelection" @change="sortBy(currentSelection)">
        <option disabled value="">Sort by…</option>
        <option v-for="opt in options" :key="opt" :value="opt">{{ opt }}</option>
      </select>
    </div>

    <div class="uk-margin-small">
      <a class="uk-link" @click.prevent="toggleMoreInfo">{{ showMoreInfo ? 'Hide' : 'Show' }} Info</a>
      <div v-if="showMoreInfo" class="uk-alert-primary uk-alert">More information shown because of a query (?q=)</div>
    </div>
  </div>
</template>

<script>
import VolumeImage from "@/components/volume/VolumeImage.vue";
import VolumeSearch from "@/components/volume/VolumeSearch.vue";
import VolumeExportAnnotationBtn from "@/components/volume/VolumeExportAnnotationBtn.vue";
import VolumeAnnotations from "@/components/volume/VolumeAnnotations.vue";
import OcrInspector from "@/components/volume/OcrInspector.vue";
import InfoUrlSingle from "@/components/info/InfoUrlSingle.vue";
import InfoUrlUnit from "@/components/info/InfoUrlUnit.vue";
import InfoUrlMultiple from "@/components/info/InfoUrlMultiple.vue";
import InfoUrlExternal from "@/components/info/InfoUrlExternal.vue";
import InfoUrlImageLink from "@/components/info/InfoUrlImageLink.vue";

export default {
  name: "App",
  components: {
    VolumeImage,
    VolumeSearch,
    VolumeExportAnnotationBtn,
    VolumeAnnotations,
    OcrInspector,
    InfoUrlSingle,
    InfoUrlUnit,
    InfoUrlMultiple,
    InfoUrlExternal,
    InfoUrlImageLink
  },
  data() {
    return {
      // parity with original root instance
      options: ["title", "author", "date published", "date added"],
      searchPrefix: "?sort=",
      currentSelection: "",
      itemNotFound: false,
      showMoreInfo: false,

      // demo/placeholder state you can wire to real data
      volumeImgSrc: "",
      volumeLabel: "",
      pid: "",
      manifestCount: 0,
      pageCount: 0,
      volumeUrl: "",
      related1: "",
      related2: "",
      shareUrl: "",
      volumeBase: "/volume/123", // e.g. "/volume/123"
      pageLinkBase: "/iiif/identifier" // e.g. base IIIF path
    };
  },
  methods: {
    sortBy(selection) {
      const value = `${this.searchPrefix}${selection}`;
      if (window.location !== value) window.location = value;
    },
    toggleMoreInfo() { this.showMoreInfo = !this.showMoreInfo; }
  },
  mounted() {
    if (this.$refs["v-attr-sort"]) {
      this.currentSelection = this.$refs["v-attr-sort"].getAttribute("data-sort") || this.currentSelection;
    }
    if (window.location.href.includes("?q=")) {
      this.showMoreInfo = true;
    }
  }
};
</script>