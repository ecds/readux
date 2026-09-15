<template>
  <div class="rx-info-content">
    <ul uk-accordion class="rx-accordion-container">
      <li class="uk-open">
        <a class="uk-accordion-title uk-label rx-accordion-head" href>Annotation Counts</a>
        <div class="uk-accordion-content rx-accordion-content uk-margin-small-left uk-margin-small-top">
          <div class="rx-info-content-value rx-annotation-badge">{{ localManifestCount }} in manifest</div>
          <div v-if="!isAll && localPageCount > 0" class="rx-info-content-value rx-annotation-badge">{{ localPageCount }} on page</div>
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
    isAll: { type: Boolean, default: false },
    // Element whose textContent holds JSON { json_data: [...] }
    contextElId: { type: String, default: "context" }
  },
  data() {
    return {
      localPageCount: this.pageCount,
      annotationData: []
    };
  },
  computed: {
    // Manifest total is DERIVED from state — the sum of every page's current
    // count — never accumulated from deltas. This is the core fix: a transient,
    // duplicated, split, or out-of-order canvasswitch event can no longer
    // permanently corrupt the total (which is how it drifted, went negative,
    // and over-counted). The next authoritative event for a page overwrites its
    // entry and the sum simply recomputes.
    localManifestCount() {
      return this.annotationData.reduce(
        (sum, a) => sum + (a.canvas__position__count || 0),
        0
      );
    }
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

    // Counts come only from the annotator's "canvasswitch" events, which are
    // NOT a clean per-action stream:
    //   - a page's annotations load in two async steps (points, then text),
    //     so one page load emits two count events;
    //   - on navigation A->B the effect fires immediately with B's pid but A's
    //     still-loaded count (a transient), before the refetch resolves;
    //   - every point change also dispatches a synthetic reset
    //     {canvas: "all", annotationsOnPage: 0}.
    // The old code accumulated deltas across these events, so any transient or
    // out-of-order event corrupted the manifest total for good. Instead we
    // treat each event's annotationsOnPage as the AUTHORITATIVE current count
    // for that page and just record it; the manifest total is the sum (see the
    // localManifestCount computed). That is self-correcting: a wrong transient
    // value is overwritten by the next event for the same page, and a revisit
    // always restores the truth. No deltas, so no drift and no negatives.
    const RESET_CANVAS = "all";
    this._currentCanvas = null;

    this._onCanvasSwitch = (event) => {
      const detail = event && event.detail ? event.detail : {};
      const count =
        typeof detail.annotationsOnPage === "number"
          ? detail.annotationsOnPage
          : null;

      // Ignore the synthetic reset and any event without a real per-page count.
      if (!detail.canvas || detail.canvas === RESET_CANVAS || count === null) {
        return;
      }

      // Record this page's current count (authoritative SET, never a delta).
      const row = this.annotationData.find(
        (a) => a.canvas__pid === detail.canvas
      );
      if (row) {
        row.canvas__position__count = count;
      } else {
        const pidNum = (detail.canvas.match(/\d+/g) || []).pop();
        this.annotationData = this.annotationData.concat({
          canvas__manifest__label: this.annotationData[0]?.canvas__manifest__label,
          canvas__pid: detail.canvas,
          canvas__position: pidNum != null ? parseInt(pidNum, 10) : 0,
          canvas__position__count: count
        });
      }

      this.localPageCount = count;
      this._currentCanvas = detail.canvas;
    };

    window.addEventListener("canvasswitch", this._onCanvasSwitch);
  },
  beforeUnmount() {
    window.removeEventListener("canvasswitch", this._onCanvasSwitch);
  }
};
</script>

<style scoped>
/* Component-scoped overrides (optional) */
</style>