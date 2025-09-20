<template>
  <div class="rx-info-content">
    <div class="rx-info-content-label uk-flex-between rx-flex">
      <span>{{ label }}</span>
      <div>
        <span class="uk-label rx-label-copy" @click="copyToClipboard">Copy</span>
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
    url: { type: String, required: true },
    volume: { type: String, required: true }
  },
  data() {
    return { localUrl: this.url };
  },
  methods: {
    copyToClipboard() {
      if (navigator.clipboard) {
        navigator.clipboard.writeText(this.localUrl)
          .then(() => alert(`You have copied: ${this.localUrl}`))
          .catch(() => alert("Something went wrong with copy."));
      } else {
        alert("Clipboard API not supported in this browser.");
      }
    }
  },
  mounted() {
    window.addEventListener("canvasswitch", (event) => {
      if (event.detail) {
        const protocol = window.location.protocol;
        const host = window.location.host;
        const canvas = event.detail.canvas;
        const url = protocol + "//" + host + this.volume + "/page/" + canvas;
        this.localUrl = url;
      }
    });
  }
}
</script>
