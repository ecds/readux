<template>
  <div class="rx-info-content">
    <ul uk-accordion class="rx-accordion-container">
      <li class="uk-open">
        <a class="uk-accordion-title uk-label rx-accordion-head" href>Annotation Counts</a>
        <div class="uk-accordion-content rx-accordion-content uk-margin-small-left uk-margin-small-top">
          <div class="rx-info-content-value rx-annotation-badge">{{ localManifestCount }} in manifest</div>
          <div v-if="localPageCount > 0" class="rx-info-content-value rx-annotation-badge">{{ localPageCount }} on page</div>
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
              <div v-if="annotation.canvas__position__count" class="rx-annotation-index-row">
                <a :href="annotation.canvas__pid">
                  <span class="uk-label rx-label-copy">Page {{ annotation.canvas__position }}</span>
                </a>
                <span>‧ {{ annotation.canvas__position__count }} annotations</span>
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

    // The "userAnnotationsUpdated" event only carries a reliable
    // annotationsOnPage (its added/deleted flags are computed after the
    // comparison ref has already been updated, so they are always false).
    // "canvasswitch" carries the full detail (canvas, annotationAdded,
    // annotationDeleted, annotationsOnPage) — but it also fires on page
    // navigation, where added/deleted can be spuriously true because the
    // counts of two different pages get compared. Track the current canvas
    // and only treat add/delete as real when the canvas hasn't changed.
    //
    // "canvasswitch" can also fire more than once in quick succession for
    // the SAME canvas while its annotation list is still loading — e.g. a
    // transient "0 on page" read before the async fetch resolves, followed
    // by the real count moments later. Diffing against a running
    // _prevPageCount on every event mistakes that settle-in transition for
    // a real add/delete and double-counts it against localManifestCount
    // (which already reflects the server-rendered total as of page load).
    // Debounce: only diff once the count for the current canvas has stopped
    // changing for SETTLE_MS, so we always compare against a stable reading.
    const SETTLE_MS = 250;
    this._currentCanvas = null;
    this._prevPageCount = null;
    this._settleTimer = null;

    this._commitSettledCount = (canvas, newPageCount) => {
      if (this._prevPageCount !== null) {
        const delta = newPageCount - this._prevPageCount;
        if (delta > 0) {
          // annotation(s) added
          let createNewPage = true;
          for (let i = 0; i < this.annotationData.length; i++) {
            if (this.annotationData[i].canvas__pid === canvas) {
              this.annotationData[i].canvas__position__count = newPageCount;
              createNewPage = false;
              break;
            }
          }
          if (createNewPage) {
            const canvasPidNum = (canvas.match(/\d+/g) || []).pop();
            this.annotationData = this.annotationData.concat({
              canvas__manifest__label: this.annotationData[0]?.canvas__manifest__label,
              canvas__pid: canvas,
              canvas__position: parseInt(canvasPidNum, 10) + 1,
              canvas__position__count: newPageCount
            });
          }
          this.localManifestCount += delta;
        } else if (delta < 0) {
          // annotation(s) deleted
          for (let i = 0; i < this.annotationData.length; i++) {
            if (this.annotationData[i].canvas__pid === canvas) {
              this.annotationData[i].canvas__position__count = newPageCount;
              break;
            }
          }
          this.localManifestCount += delta;
        }
      }
      this._prevPageCount = newPageCount;
    };

    this._onCanvasSwitch = (event) => {
      const detail = event && event.detail ? event.detail : {};
      const newPageCount = typeof detail.annotationsOnPage === "number" ? detail.annotationsOnPage : null;

      if (newPageCount !== null) {
        this.localPageCount = newPageCount;
      }

      if (!detail.canvas) {
        return;
      }

      if (detail.canvas !== this._currentCanvas) {
        // Navigated to a different canvas: reset the baseline so we never
        // diff this canvas's count against the previous canvas's count.
        this._currentCanvas = detail.canvas;
        this._prevPageCount = null;
        if (this._settleTimer) {
          clearTimeout(this._settleTimer);
          this._settleTimer = null;
        }
      }

      if (newPageCount === null) {
        return;
      }

      const canvas = detail.canvas;
      if (this._settleTimer) {
        clearTimeout(this._settleTimer);
      }
      this._settleTimer = setTimeout(() => {
        this._settleTimer = null;
        this._commitSettledCount(canvas, newPageCount);
      }, SETTLE_MS);
    };

    window.addEventListener("canvasswitch", this._onCanvasSwitch);
  },
  beforeDestroy() {
    window.removeEventListener("canvasswitch", this._onCanvasSwitch);
    if (this._settleTimer) {
      clearTimeout(this._settleTimer);
    }
  }
};
</script>

<style scoped>
/* Component-scoped overrides (optional) */
</style>