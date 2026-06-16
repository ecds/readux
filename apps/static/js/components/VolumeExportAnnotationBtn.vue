<template>
  <div class="rx-info-content" v-if="isExportVisible">
    <slot></slot>
  </div>
</template>

<script>
export default {
  name: "VolumeExportAnnotationBtn",
  props: {
    manifestCount: { type: Number, default: 0 }
  },
  data() {
    return {
      localManifestCount: this.manifestCount,
      isExportVisible: true
    };
  },
  mounted() {
    this.isExportVisible = this.localManifestCount >= 1;

    // "canvasswitch" carries canvas + annotationAdded/annotationDeleted;
    // the flags are only trustworthy while staying on the same canvas (on
    // page navigation they compare counts of two different pages).
    this._currentCanvas = null;
    this._prevPageCount = null;
    this._onCanvasSwitch = (event) => {
      if (!event) return;
      const detail = event.detail || {};
      const sameCanvas = detail.canvas && detail.canvas === this._currentCanvas;
      const newPageCount = typeof detail.annotationsOnPage === "number" ? detail.annotationsOnPage : null;

      if (sameCanvas && newPageCount !== null && this._prevPageCount !== null) {
        const delta = newPageCount - this._prevPageCount;
        if (delta !== 0) {
          this.localManifestCount += delta;
          this.isExportVisible = this.localManifestCount >= 1;
        }
      }

      if (newPageCount !== null && sameCanvas) {
        this._prevPageCount = newPageCount;
      }

      if (detail.canvas) {
        if (!location.pathname.includes(detail.canvas)) {
          history.pushState({}, "", detail.canvas);
        }
        if (detail.canvas !== this._currentCanvas) {
          this._prevPageCount = newPageCount;
        }
        this._currentCanvas = detail.canvas;
      }
    };

    window.addEventListener("canvasswitch", this._onCanvasSwitch);
  },
  beforeUnmount() {
    window.removeEventListener("canvasswitch", this._onCanvasSwitch);
  }
};
</script>

<style scoped>
/* Add any scoped styles here if needed */
</style>