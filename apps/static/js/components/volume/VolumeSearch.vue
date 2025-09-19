<template>
  <div class="rx-volume-search">
    <div class="uk-search uk-search-default rx-page-search-container">
      <span uk-search-icon></span>
      <input
        class="uk-search-input"
        type="search"
        id="volume-search"
        placeholder="Search in volume text or annotations"
        name="q"
        v-model.trim="keyword"
        @keypress.enter="getSearchResults"
      />
    </div>
    <div class="uk-text-small uk-margin-small-top uk-margin-small-left">Use "" to match whole words.</div>

    <div v-if="hasResults">
      <ul class="uk-text-bold uk-text-large uk-tab" data-uk-tab="{connect:'#rx-search-panel'}">
        <li><a href>Text ({{ inText }})</a></li>
        <li><a href>Annotation ({{ inAnnotations }})</a></li>
      </ul>
      <ul id="rx-search-panel" class="uk-switcher uk-panel-scrollable uk-resize-vertical" uk-height-viewport="offset-bottom: 100">
        <li>
          <div v-if="inText === 0" class="rx-padding-extra-small uk-text-small">No matches in text.</div>
          <div v-else v-for="(match, index) in textData" :key="`t-${index}`" class="rx-padding-extra-small">
            <div class="uk-text-small">
              <a :href="`/volume/${pid}/page/${match.canvas_pid}`"><div class="uk-label rx-label-copy">Page {{ match.canvas_index }}</div></a>
              <div class="uk-inline-block" style="vertical-align: middle"> · {{ match.canvas_match_count }} match<span v-if="match.canvas_match_count > 1">es</span></div>
            </div>
            <ul class="uk-text-small rx-line-height-sm uk-margin-small-bottom uk-list uk-list-bullet">
              <li v-for="(context, i) in match.context" :key="`tc-${i}`" v-html="context" class="uk-margin-small-top"></li>
            </ul>
          </div>
        </li>
        <li>
          <div v-if="inAnnotations === 0" class="rx-padding-extra-small uk-text-small">No matches in annotations.</div>
          <div v-else v-for="(match, index) in annotationData" :key="`a-${index}`" class="rx-padding-extra-small">
            <div class="uk-text-small">
              <a :href="`/volume/${pid}/page/${match.canvas_pid}`"><div class="uk-label rx-label-copy">Page {{ match.canvas_index }}</div></a>
              <div class="uk-inline-block" style="vertical-align: middle"> · {{ match.canvas_match_count }} match<span v-if="match.canvas_match_count > 1">es</span></div>
            </div>
            <ul class="uk-text-small rx-line-height-sm uk-margin-small-bottom uk-list uk-list-bullet">
              <li v-for="(context, i) in match.context" :key="`ac-${i}`" v-html="context" class="uk-margin-small-top"></li>
            </ul>
          </div>
        </li>
      </ul>
    </div>

    <div v-else>
      <div v-if="emptyMessage" class="uk-alert uk-margin-small-top uk-margin-remove-bottom">{{ emptyMessage }}</div>
    </div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  name: "VolumeSearch",
  props: { pid: { type: [String, Number], required: true } },
  data() {
    return {
      searchResults: {},
      annotationData: [],
      textData: [],
      keyword: "",
      inAnnotations: 0,
      inText: 0,
      emptyMessage: ""
    };
  },
  computed: {
    hasResults() { return (this.inAnnotations + this.inText) > 0; }
  },
  methods: {
    async getSearchResults() {
      try {
        if (!this.keyword) {
          this.emptyMessage = "Type a keyword to search";
          this.inAnnotations = 0; this.inText = 0; this.annotationData = []; this.textData = [];
          return;
        }
        this.emptyMessage = "";
        const { data } = await axios.get(`/search/volume/pages`, {
          params: { keyword: this.keyword, volume_id: this.pid }
        });
        this.searchResults = data || {};
        if (this.searchResults && this.searchResults.hasOwnProperty("matches_in_annotations")) {
          const ann = this.searchResults.matches_in_annotations || {};
          const txt = this.searchResults.matches_in_text || {};
          this.inAnnotations = ann.total_matches_in_volume || 0;
          this.inText = txt.total_matches_in_volume || 0;
          this.annotationData = ann.volume_matches || [];
          this.textData = txt.volume_matches || [];
        }
        if (!this.hasResults) this.emptyMessage = "No matches in either annotations or text.";
      } catch (error) {
        console.error("Error fetching volume search data via API call to ElasticSearch:", error);
        this.emptyMessage = "Search failed. Please try again.";
      }
    }
  }
};
</script>