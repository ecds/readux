<template>
  <div class="rx-info-content">
    <div class="rx-info-content-label uk-flex-between rx-flex">
      <span v-if="localUrls !== undefined">{{ label }}</span>
      <div>
        <span
          class="uk-label rx-label-copy"
          @click="copyText"
          v-if="localUrls !== undefined"
        >
        <span uk-icon="icon: copy; ratio: 0.5"></span>
        Copy</span>
      </div>
    </div>
    <div class="rx-info-content-value">
      <a :href="pageresource" class="rx-anchor" target="_blank">{{ pageresource }}</a>
    </div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  name: "InfoUrlImageLink",
  props: {
    label: { type: String, required: true },
    pagelink: { type: String, required: true }
  },
  data() {
    return {
      localUrls: undefined,
      pageresource: undefined,
      canvas: null,
      can: null
    };
  },
  methods: {
    async copyText() {
      try {
        await navigator.clipboard.writeText(this.localUrls);
        if (window.UIkit?.notification) {
          UIkit.notification({ message: "Copied!", status: "success", timeout: 1200 });
        }
      } catch (err) {
        console.error("Copy failed:", err);
      }
    },
  },
  mounted() {
    window.addEventListener("canvasswitch", (event) => {
      if (event.detail && this.canvas !== event.detail.canvas) {
        this.canvas = event.detail.canvas;
        const localpagelink = this.pagelink;
        if (this.canvas !== 'all') {
          axios.get(`iiif/resource/${event.detail.canvas}`)
            .then(response => {
              this.pageresource = response.data.resource;
              this.pagetext = response.data.text;
            }).catch(error => {
              console.error(error);
            });
          this.localUrls = localpagelink + "/" + this.canvas + "/full/full/0/default.jpg";
          this.can = this.canvas;
        }
      }
    });
  }
}
</script>
