<template>
  <div class="rx-info-content">
    <div class="rx-info-content-label uk-flex-between rx-flex">
      <span>{{ label }}</span>
      <div>
        <span class="uk-label rx-label-copy" @click="copyText">
          <span uk-icon="icon: copy; ratio: 0.5"></span>
          Copy</span>
      </div>
    </div>
    <div class="rx-info-content-value">
      <a :href="url" class="rx-anchor" target="_blank">{{ url }}</a>
    </div>
  </div>
</template>

<script>
export default {
  name: "InfoUrlSingle",
  props: {
    label: { type: String, required: true },
    url: { type: String, required: true }
  },
  methods: {
    async copyText() {
      try {
        await navigator.clipboard.writeText(this.url);
        if (window.UIkit?.notification) {
          UIkit.notification({ message: "Copied!", status: "success", timeout: 1200 });
        }
      } catch (err) {
        console.error("Copy failed:", err);
      }
    },
  }
}
</script>
