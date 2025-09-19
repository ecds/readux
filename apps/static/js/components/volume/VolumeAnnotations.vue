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
          <div v-if="annotationData.length === 0"><span>No annotations to show</span></div>
          <ul v-else>
            <li v-for="annotation in annotationData" :key="annotation.canvas__pid">
              <div v-if="annotation.canvas__position__count">
                <a :href="annotation.canvas__pid"><span class="uk-label rx-label-copy">Page {{ annotation.canvas__position }}</span></a>
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
    const el = document.getElementById(this.contextElId);
    if (el?.textContent) {
      try { this.annotationData = JSON.parse(el.textContent).json_data || []; }
      catch(e) { console.error("Failed to parse annotation context:", e); }
    }

    this._onCanvasSwitch = (event) => {
      const detail = event?.detail || {};
      if (detail.annotationAdded) {
        let createNewPage = true;
        for (let i = 0; i < this.annotationData.length; i++) {
          if (this.annotationData[i].canvas__pid === detail.canvas) {
            this.annotationData[i].canvas__position__count++;
            createNewPage = false;
          }
        }
        if (createNewPage) {
          const canvas_pid_num = (detail.canvas?.match(/\d+$/) || []).pop();
          this.annotationData = this.annotationData.concat({
            canvas__manifest__label: this.annotationData[0]?.canvas__manifest__label || "",
            canvas__pid: detail.canvas,
            canvas__position: parseInt(canvas_pid_num, 10) + 1,
            canvas__position__count: detail.annotationsOnPage
          });
        }
        this.localManifestCount++;
      }
      if (detail.annotationDeleted) {
        for (let i = 0; i < this.annotationData.length; i++) {
          if (this.annotationData[i].canvas__pid === detail.canvas) {
            this.annotationData[i].canvas__position__count--;
          }
        }
        this.localManifestCount--;
      }
      if (typeof detail.annotationsOnPage === "number") {
        this.localPageCount = detail.annotationsOnPage;
      }
    };

    window.addEventListener("canvasswitch", this._onCanvasSwitch);
  },
  beforeDestroy() {
    window.removeEventListener("canvasswitch", this._onCanvasSwitch);
  }
};
</script>