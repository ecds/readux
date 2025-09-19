<template>
  <div class="rx-info-content">
    <div class="rx-info-content-label uk-flex-between rx-flex ">
      <span v-if="localUrls">{{ label }}</span>
      <div><span class="uk-label rx-label-copy" v-if="localUrls" @click="copy">Copy</span></div>
    </div>
    <div class="rx-info-content-value">
      <a :href="pageresource" class="rx-anchor" target="_blank">{{ pageresource }}</a>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import { copyToClipboard } from "@/utils/clipboard";
export default {
  name: "InfoUrlImageLink",
  props: { label: { type: String, default: "" }, pagelink: { type: String, required: true } },
  data() {
    return { localUrls: "", pageresource: "", canvas: null };
  },
  methods: { copy() { copyToClipboard(this.localUrls); } },
  mounted() {
    this._onCanvasSwitch = async (event) => {
      const detail = event?.detail || {};
      if (!detail.canvas || this.canvas === detail.canvas) return;
      this.canvas = detail.canvas;
      if (this.canvas !== "all") {
        try {
          const { data } = await axios.get(`iiif/resource/${this.canvas}`);
          this.pageresource = data.resource;
          // If you also want raw text, you could expose data.text here
        } catch (e) { console.error(e); }
        this.localUrls = `${this.pagelink}/${this.canvas}/full/full/0/default.jpg`;
      }
    };
    window.addEventListener("canvasswitch", this._onCanvasSwitch);
  },
  beforeDestroy() { window.removeEventListener("canvasswitch", this._onCanvasSwitch); }
};
</script>