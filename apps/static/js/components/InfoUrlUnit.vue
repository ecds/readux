<template>
  <div class="rx-info-content-value uk-flex-between rx-flex">
    <a :href="url" class="rx-anchor" target="_blank">{{ url }}</a>
    <div>
      <span class="uk-label rx-label-copy" @click="copyToClipboard">Copy</span>
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
    copyToClipboard() {
      if (navigator.clipboard) {
        navigator.clipboard.writeText(this.url)
          .then(() => alert(`You have copied: ${this.url}`))
          .catch(() => alert("Something went wrong with copy."));
      } else {
        alert("Clipboard API not supported in this browser.");
      }
    }
  }
}
</script>
