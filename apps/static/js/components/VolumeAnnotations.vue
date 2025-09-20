<template>
  <div class="rx-info-content">
    <ul uk-accordion class="rx-accordion-container">
      <li class="uk-open">
        <a class="uk-accordion-title uk-label rx-accordion-head" href>Annotation Counts</a>
        <div class="uk-accordion-content rx-accordion-content uk-margin-small-left uk-margin-small-top">
          <div class="rx-info-content-value rx-annotation-badge">{{ localManifestCount }} in manifest</div>
          <div class="rx-info-content-value rx-annotation-badge">{{ localPageCount }} on page</div>
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
            <li v-for="annotation in annotationData" :key="annotation.canvas__pid">
              <div v-if="annotation.canvas__position__count">
                <a :href="annotation.canvas__pid">
                  <span class="uk-label rx-label-copy">Page {{ annotation.canvas__position }}</span>
                </a>
                ‧ {{ annotation.canvas__position__count }} annotations
              </div>
            </li>
          </ul>
        </div>
      </li>
    </ul>
  </div>
</template>

<script>
export default {
  name: "VolumeAnnotations",
  props: {
    manifestCount: { type: Number, default: 0 },
    pageCount: { type: Number, default: 0 },
    // Element whose textContent holds JSON { json_data: [...] }
    contextElId: { type: String, default: "context" }
  },
  data() {
    return {
      localManifestCount: this.manifestCount,
      localPageCount: this.pageCount,
      annotationData: []
    };
  },
  mounted() {
    // Initialize from embedded JSON
    const el = document.getElementById(this.contextElId);
    if (el && el.textContent) {
      try {
        const parsed = JSON.parse(el.textContent);
        this.annotationData = parsed?.json_data || [];
      } catch (e) {
        console.error("[VolumeAnnotations] Failed to parse context JSON:", e);
      }
    }

    // Listen for canvas switch / annotation changes
    this._onUserAnnotationsUpdate = (event) => {
      const detail = event && event.detail ? event.detail : {};

      if (detail.annotationAdded) {
        let createNewPage = true;
        for (let i = 0; i < this.annotationData.length; i++) {
          if (this.annotationData[i].canvas__pid === detail.canvas) {
            this.annotationData[i].canvas__position__count++;
            createNewPage = false;
            break;
          }
        }
        if (createNewPage) {
          const canvasPidNum = (detail.canvas?.match(/\d+$/) || []).pop();
          this.annotationData = this.annotationData.concat({
            canvas__manifest__label: this.annotationData[0]?.canvas__manifest__label,
            canvas__pid: detail.canvas,
            canvas__position: parseInt(canvasPidNum, 10) + 1,
            canvas__position__count: detail.annotationsOnPage
          });
        }
        this.localManifestCount++;
      }

      if (detail.annotationDeleted) {
        for (let i = 0; i < this.annotationData.length; i++) {
          if (this.annotationData[i].canvas__pid === detail.canvas) {
            this.annotationData[i].canvas__position__count--;
            break;
          }
        }
        this.localManifestCount--;
      }

      if (typeof detail.annotationsOnPage === "number") {
        this.localPageCount = detail.annotationsOnPage;
      }
    };

    window.addEventListener("userAnnotationsUpdate", this._onUserAnnotationsUpdate);
  },
  beforeDestroy() {
    window.removeEventListener("userAnnotationsUpdate", this._onUserAnnotationsUpdate);
  }
};
</script>

<style scoped>
/* Component-scoped overrides (optional) */
</style>