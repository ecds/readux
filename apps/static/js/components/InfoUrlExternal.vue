<template>
  <div class="rx-info-content">
    <div class="rx-info-content-label uk-flex-between rx-flex">
      <span>{{ label }}</span>
      <div>
        <span class="uk-label rx-label-copy" @click="copyText">
          <span uk-icon="icon: copy; ratio: 0.5"></span>
          Copy
        </span>
      </div>
    </div>
    <div class="rx-info-content-value">
      <a :href="localUrl" class="rx-anchor" target="_blank">{{ localUrl }}</a>
    </div>
  </div>
</template>

<script>
export default {
  name: "InfoUrlExternal",
  props: {
    label: { type: String, required: true },
    pagelink: { type: String, required: true },
    volume: { type: String, required: true }
  },
  data() {
    return { localUrl: this.url };
  },
  methods: {
    async copyText() {
      try {
        await navigator.clipboard.writeText(this.localUrl);
        if (window.UIkit?.notification) {
          UIkit.notification({ message: "Copied!", status: "success", timeout: 1200 });
        }
      } catch (err) {
        console.error("Copy failed:", err);
      }
    },
  },
  mounted() {
    window.addEventListener("canvasUpdate", (event) => {
      if (event.detail) {
        const protocol = window.location.protocol;
        const host = window.location.host;
        const canvas = event.detail;
        const url = protocol + "//" + host + this.volume + "/page/" + canvas;
        this.localUrl = url;
      }
    });
  }
}
</script>
