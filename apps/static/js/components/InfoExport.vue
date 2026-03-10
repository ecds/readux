<template>
  <div v-if="shouldRender" class="rx-info-content">
    <div class="rx-info-content-label uk-flex-between rx-flex">
      <span>{{ label }}</span>

      <a v-if="fullurl"
          :href="fullurl"
          target="_blank"
          rel="noopener"> 
        <span
          class="uk-label rx-label-copy"
          role="button"
          tabindex="0"
        >
          <span :uk-icon="`icon: ${icon}; ratio: 0.6`"></span>
          {{btnlabel}}
        </span>
      </a>

      <a v-else-if="!!localUrls"
          :href="localUrls"
          target="_blank"
          rel="noopener"> 
        <span
          class="uk-label rx-label-copy"
          role="button"
          tabindex="0"
        >
          <span :uk-icon="`icon: ${icon}; ratio: 0.6`"></span>
          {{btnlabel}}
        </span>
      </a>
    </div>

    <div class="rx-info-content-value">
      <a
        v-if="fullurl"
        :href="fullurl"
        class="rx-anchor"
        target="_blank"
        rel="noopener"
      >{{ fullurl }}</a>
      <a
        v-else-if="!!localUrls"
        :href="localUrls"
        class="rx-anchor"
        target="_blank"
        rel="noopener"
      >{{ localUrls }}</a>
    </div>
  </div>
</template>

<script>

const shouldShowForPath = (path) => {
  if (!path) return true;
  const segments = path.split("/").filter(Boolean);
  const pageIndex = segments.indexOf("page");
  if (pageIndex === -1) return true;
  const nextSegment = segments[pageIndex + 1];
  if (!nextSegment) return true;
  return nextSegment !== "all";
};

export default {
  name: "InfoExport",
  props: {
    label:    { type: String, required: true },
    btnlabel: { type: String, required: true },
    icon:    { type: String, required: true },
    pagelink: { type: String, required: true }, // base IIIF image server
    fullurl: { type: String, required: false }, // if a fullurl is provided, use that
    pageonly: { type: Boolean, default: false } // apply visibility rules only on page views
  },
  data() {
    const path = typeof window !== "undefined" ? window.location.pathname : "";
    return {
      localUrls: undefined,
      canvas: null,
      can: null,
      shouldRender: this.pageonly ? shouldShowForPath(path) : true
    };
  },
  watch: {
    pageonly(next) {
      if (!next) {
        this.shouldRender = true;
        return;
      }
      this._updateVisibility(this.canvas);
    }
  },
  methods: {
    // Normalize whatever canvasUpdate sends (string or {canvas})
    _resolveCanvasFromEvent(event) {
      const d = event?.detail;
      if (!d) return null;
      if (typeof d === "string") return d;
      if (typeof d === "object" && d.canvas) return d.canvas;
      return null;
    },

    async _updateForCanvas(canvasId) {
      if (!canvasId || canvasId === "all") {
        this.canvas = this.can = null;
        this.localUrls = undefined;
        this._updateVisibility(canvasId);
        return;
      }

      this.localUrls = `${this.pagelink}/${canvasId}/full/full/0/default.jpg`;
      this.canvas = this.can = canvasId;
      this._updateVisibility(canvasId);
    },
    _updateVisibility(canvasId) {
      if (!this.pageonly) {
        this.shouldRender = true;
        return;
      }
      if (canvasId === "all") {
        this.shouldRender = false;
        return;
      }
      if (canvasId) {
        this.shouldRender = true;
        return;
      }
      const path = typeof window !== "undefined" ? window.location.pathname : "";
      this.shouldRender = shouldShowForPath(path);
    }
  },
  mounted() {
    this._onCanvasUpdate = (event) => {
      const next = this._resolveCanvasFromEvent(event);
      if (next && next !== this.canvas) {
        this._updateForCanvas(next);
      }
    };
    window.addEventListener("canvasUpdate", this._onCanvasUpdate);
    this._onHistoryChange = () => {
      this._updateVisibility(this.canvas);
    };
    window.addEventListener("popstate", this._onHistoryChange);
    this._updateVisibility(this.canvas);
  },
  beforeDestroy() {
    window.removeEventListener("canvasUpdate", this._onCanvasUpdate);
    if (this._onHistoryChange) {
      window.removeEventListener("popstate", this._onHistoryChange);
    }
  }
};
</script>
