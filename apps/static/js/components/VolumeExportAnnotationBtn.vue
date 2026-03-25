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

    this._onUserAnnotationsUpdate = (event) => {
      if (!event) return;
      const detail = event.detail || {};

      if (detail.annotationsOnPage) {
        if (detail.annotationAdded) this.localManifestCount++;
        if (detail.annotationDeleted) this.localManifestCount--;
        this.isExportVisible = this.localManifestCount >= 1;
      }

      if (detail.canvas && !location.pathname.includes(detail.canvas)) {
        history.pushState({}, "", detail.canvas);
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
/* Add any scoped styles here if needed */
</style>