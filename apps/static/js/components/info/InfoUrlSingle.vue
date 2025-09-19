<template>
  <div class="rx-info-content">
    <div class="rx-info-content-label uk-flex-between rx-flex">
      <span>{{ label }}</span>
      <div><span class="uk-label rx-label-copy" @click="copy">Copy</span></div>
    </div>
    <div class="rx-info-content-value">
      <a :href="url" class="rx-anchor" target="_blank">{{ url }}</a>
    </div>
  </div>
</template>

<script>
import { copyToClipboard } from "@/utils/clipboard";
export default {
  name: "InfoUrlSingle",
  props: { label: { type: String, default: "" }, url: { type: String, required: true } },
  methods: { copy() { copyToClipboard(this.url); } }
};
</script>