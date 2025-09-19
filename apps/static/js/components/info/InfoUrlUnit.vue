<template>
  <div class="rx-info-content-value uk-flex-between rx-flex">
    <a :href="url" class="rx-anchor" target="_blank">{{ url }}</a>
    <div><span class="uk-label rx-label-copy" @click="copy">Copy</span></div>
  </div>
</template>

<script>
import { copyToClipboard } from "@/utils/clipboard";
export default {
  name: "InfoUrlUnit",
  props: { url: { type: String, required: true } },
  methods: { copy() { copyToClipboard(this.url); } }
};
</script>