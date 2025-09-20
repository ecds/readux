<template>
  <div class="rx-info-content">
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

export default {
  name: "InfoExport",
  props: {
    label:    { type: String, required: true },
    btnlabel: { type: String, required: true },
    icon:    { type: String, required: true },
    pagelink: { type: String, required: true }, // base IIIF image server
    fullurl: { type: String, required: false } // if a fullurl is provided, use that
  },
  data() {
    return {
      localUrls: undefined,
      canvas: null,
      can: null
    };
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
        return;
      }

      this.localUrls = `${this.pagelink}/${canvasId}/full/full/0/default.jpg`;
      this.canvas = this.can = canvasId;
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
  },
  beforeDestroy() {
    window.removeEventListener("canvasUpdate", this._onCanvasUpdate);
  }
};
</script>