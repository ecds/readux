<template>
  <div class="rx-info-content" v-if="isExportVisible">
    <slot />
  </div>
</template>

<script>
export default {
  name: "VolumeExportAnnotationBtn",
  props: { manifestCount: { type: Number, default: 0 } },
  data() {
    return { localManifestCount: this.manifestCount, isExportVisible: true };
  },
  mounted() {
    this.isExportVisible = this.localManifestCount >= 1;
    this._onCanvasSwitch = (event) => {
      const detail = event?.detail || {};
      if (detail.annotationsOnPage) {
        if (detail.annotationAdded) this.localManifestCount++;
        if (detail.annotationDeleted) this.localManifestCount--;
        this.isExportVisible = this.localManifestCount >= 1;
      }
      if (detail.canvas && !location.pathname.includes(detail.canvas)) {
        history.pushState({}, "", detail.canvas);
      }
    };
    window.addEventListener("canvasswitch", this._onCanvasSwitch);
  },
  beforeDestroy() {
    window.removeEventListener("canvasswitch", this._onCanvasSwitch);
  }
};
</script>