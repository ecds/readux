<template>
  <div class="rx-info-content">
    <div class="rx-info-content-label uk-flex-between rx-flex ">
      <span>{{ label }}</span>
      <div><span class="uk-label rx-label-copy" @click="copy">Copy</span></div>
    </div>
    <div class="rx-info-content-value">
      <a :href="localUrl" class="rx-anchor" target="_blank">{{ localUrl }}</a>
    </div>
  </div>
</template>

<script>
import { copyToClipboard } from "@/utils/clipboard";
export default {
  name: "InfoUrlExternal",
  props: {
    label: { type: String, default: "" },
    url: { type: String, required: true },
    volume: { type: String, required: true }
  },
  data() {
    return { localUrl: this.url };
  },
  methods: {
    copy() { copyToClipboard(this.localUrl); }
  },
  mounted() {
    this._onCanvasSwitch = (event) => {
      const detail = event?.detail;
      if (!detail) return;
      const protocol = window.location.protocol;
      const host = window.location.host;
      const canvas = detail.canvas;
      const url = `${protocol}//${host}${this.volume}/page/${canvas}`;
      this.localUrl = url;
    };
    window.addEventListener("canvasswitch", this._onCanvasSwitch);
  },
  beforeDestroy() {
    window.removeEventListener("canvasswitch", this._onCanvasSwitch);
  }
};
</script>