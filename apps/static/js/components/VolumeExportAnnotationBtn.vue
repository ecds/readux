<template>
  <div class="rx-info-content" v-if="isExportVisible">
    <slot></slot>
  </div>
</template>

<script>
export default {
  name: "VolumeExportAnnotationBtn",
  props: {
    manifestCount: { type: Number, default: 0 },
    // Element whose textContent holds JSON { json_data: [...] }
    contextElId: { type: String, default: "context" }
  },
  data() {
    // Seed the per-page counts from the server-rendered JSON up front so the
    // export button's initial visibility is correct on first render (no flash).
    let annotationData = [];
    try {
      const el = document.getElementById(this.contextElId);
      if (el && el.textContent) {
        annotationData = JSON.parse(el.textContent)?.json_data || [];
      }
    } catch (e) {
      console.error("[VolumeExportAnnotationBtn] Failed to parse context JSON:", e);
    }
    return { annotationData };
  },
  computed: {
    // Derived from state — sum of every page's current count — never
    // accumulated from deltas, so transient/out-of-order canvasswitch events
    // can't corrupt it (see VolumeAnnotations for the full rationale).
    localManifestCount() {
      return this.annotationData.reduce(
        (sum, a) => sum + (a.canvas__position__count || 0),
        0
      );
    },
    isExportVisible() {
      return this.localManifestCount >= 1;
    }
  },
  mounted() {
    this._onCanvasSwitch = (event) => {
      if (!event) return;
      const detail = event.detail || {};
      const count =
        typeof detail.annotationsOnPage === "number"
          ? detail.annotationsOnPage
          : null;

      // Record this page's authoritative count. Ignore the synthetic
      // {canvas: "all"} reset the annotator dispatches on every point change.
      if (detail.canvas && detail.canvas !== "all" && count !== null) {
        const row = this.annotationData.find(
          (a) => a.canvas__pid === detail.canvas
        );
        if (row) {
          row.canvas__position__count = count;
        } else {
          const pidNum = (detail.canvas.match(/\d+/g) || []).pop();
          this.annotationData = this.annotationData.concat({
            canvas__pid: detail.canvas,
            canvas__position: pidNum != null ? parseInt(pidNum, 10) : 0,
            canvas__position__count: count
          });
        }

        // Keep the URL in sync with the current canvas. Guarded against the
        // "all" reset so a point add/delete can't rewrite the URL to /all.
        if (!location.pathname.includes(detail.canvas)) {
          history.pushState({}, "", detail.canvas);
        }
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
