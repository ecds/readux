<template>
  <div class="rx-info-content">

    <div class="ocr-notification uk-margin-small-bottom" v-if="!isLoading && !hasText">
      This page does not have any usable OCR.
    </div>

    <div class="rx-info-content-label uk-flex-between rx-flex" style="align-items:center;">
      <span>Overlay OCR on Page</span>
      <div>
        <label class="uk-switch" for="ocr-overlay">
          <input
            type="checkbox"
            id="ocr-overlay"
            v-model="overlayChecked"
            :disabled="overlayDisabled"
            @change="onOverlayToggle"
          >
          <div class="uk-switch-slider"></div>
        </label>
      </div>
    </div>

    <div class="rx-info-content-value uk-margin-small-bottom uk-text-italic">
      Superimpose OCR text as a layer on top of the scanned volume image. We try our best to align the text to image but some may miss.
    </div>

    <div class="rx-info-content-label uk-flex-between rx-flex" style="align-items:center;">
      <span>Plain OCR Text</span>
      <div
        class="uk-label rx-label-copy"
        :class="{ 'uk-disabled': copyDisabled }"
        :aria-disabled="copyDisabled"
        role="button"
        tabindex="0"
        @click="!copyDisabled && copyText()"
        @keydown.enter.prevent="!copyDisabled && copyText()"
        @keydown.space.prevent="!copyDisabled && copyText()"
        style="user-select:none; cursor:pointer;"
      >
        <span uk-icon="icon: copy; ratio: 0.5"></span>
        Copy
      </div>
    </div>

    <div class="rx-info-content-value">
      <div v-if="isLoading" class="uk-flex uk-flex-middle" style="gap:.5rem;">
        <span uk-spinner="ratio: 0.6"></span>
        <span>Loading OCR…</span>
      </div>
      <div v-else-if="hasText" class="scrollable-container">{{ pagetext }}</div>
      <em v-else>OCR text unavailable</em>
    </div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  name: "OcrInspector",
  props: {
    pagelink: { type: String, default: "" }
  },
  data() {
    return {
      pagetext: "",
      isLoading: false,
      canvas: null,
      pageresource: null,
      localUrls: "",
      can: null,
      overlayChecked: false,
      hasOcrAvailable: false,
      nodeHandlers: new WeakMap()
    };
  },
  computed: {
    hasText() {
      return !!(this.pagetext && this.pagetext.trim().length);
    },
    copyDisabled() {
      return this.isLoading || !this.hasText;
    },
    overlayDisabled() {
      return this.isLoading || !this.hasOcrAvailable || !this.hasText;
    }
  },
  methods: {
    async copyText() {
      try {
        await navigator.clipboard.writeText(this.pagetext);
        if (window.UIkit?.notification) {
          UIkit.notification({ message: "Copied!", status: "success", timeout: 1200 });
        }
      } catch (err) {
        console.error("Copy failed:", err);
      }
    },

    onOverlayToggle() {
      this.applyOverlay(this.overlayChecked);
    },
    getOcrNodes() {
      return document.querySelectorAll("div.openseadragon-canvas div span");
    },
    addBlockHandlers(node) {
      if (this.nodeHandlers.has(node)) return;
      const handlers = {
        mouseup: (e) => { e.stopPropagation(); e.preventDefault(); },
        mousemove: (e) => { e.stopPropagation(); e.preventDefault(); },
        mousedown: (e) => { e.stopPropagation(); e.preventDefault(); }
      };
      node.addEventListener("mouseup", handlers.mouseup);
      node.addEventListener("mousemove", handlers.mousemove);
      node.addEventListener("mousedown", handlers.mousedown);
      this.nodeHandlers.set(node, handlers);
    },
    removeBlockHandlers(node) {
      const h = this.nodeHandlers.get(node);
      if (!h) return;
      node.removeEventListener("mouseup", h.mouseup);
      node.removeEventListener("mousemove", h.mousemove);
      node.removeEventListener("mousedown", h.mousedown);
      this.nodeHandlers.delete(node);
    },
    applyOverlay(enabled) {
      const nodes = this.getOcrNodes();
      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i];
        if (enabled) {
          n.style.backgroundColor = "white";
          n.style.fontWeight = "bold";
          n.style.color = "rgb(149, 9, 83)";
          this.addBlockHandlers(n);
        } else {
          n.style.backgroundColor = "transparent";
          n.style.fontWeight = "";
          n.style.color = "transparent";
          this.removeBlockHandlers(n);
        }
      }
    },

    async handleCanvasSwitch(detail) {
      const nextCanvas = detail?.canvas;

      this.isLoading = true;
      this.canvas = nextCanvas;

      const availableFromEvent = typeof detail?.ocr !== "undefined" ? !!detail.ocr : null;

      try {
        if (nextCanvas && nextCanvas !== "all") {
          const { data } = await axios.get(`iiif/resource/${nextCanvas}`);
          this.pageresource = data.resource || null;
          this.pagetext = data.text || "";
        } else {
          this.pageresource = null;
          this.pagetext = "";
        }

        if (this.pagelink && nextCanvas) {
          this.localUrls = `${this.pagelink}/${nextCanvas}/full/full/0/default.jpg`;
          this.can = nextCanvas;
        }

        this.hasOcrAvailable = (availableFromEvent !== null) ? availableFromEvent : this.hasText;

        const overlayPossible = this.hasOcrAvailable && this.hasText && !this.isLoading;
        if (!overlayPossible && this.overlayChecked) {
          this.overlayChecked = false;
          this.applyOverlay(false);
        }
        if (overlayPossible && this.overlayChecked) {
          this.$nextTick(() => this.applyOverlay(true));
        } else if (!overlayPossible) {
          this.applyOverlay(false);
        }

      } catch (err) {
        console.error("Failed to fetch page text:", err);
        this.pagetext = "";
        this.hasOcrAvailable = availableFromEvent !== null ? availableFromEvent : false;
        this.overlayChecked = false;
        this.applyOverlay(false);
      } finally {
        this.isLoading = false;
      }
    }
  },
  mounted() {
    this._onCanvasSwitch = (event) => {
      this.handleCanvasSwitch(event?.detail || {});
    };
    window.addEventListener("canvasswitch", this._onCanvasSwitch);
  },
  beforeDestroy() {
    window.removeEventListener("canvasswitch", this._onCanvasSwitch);
    const nodes = this.getOcrNodes();
    for (let i = 0; i < nodes.length; i++) this.removeBlockHandlers(nodes[i]);
  }
};
</script>

<style scoped>
/* optional: local styles */
.scrollable-container {
  max-height: 200px;
  overflow-y: auto;
}
</style>