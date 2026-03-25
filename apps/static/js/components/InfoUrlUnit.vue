<template>
  <div class="rx-info-content-value uk-flex-between rx-flex">
    <a :href="url" class="rx-anchor" target="_blank">{{ url }}</a>
    <div>
      <span class="uk-label rx-label-copy" @click="copyText">
        <span uk-icon="icon: copy; ratio: 0.5"></span>
        Copy
      </span>
    </div>
  </div>
</template>

<script>
export default {
  name: "InfoUrlUnit",
  props: {
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
