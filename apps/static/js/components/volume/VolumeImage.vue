<template>
  <div>
    <div class="uk-text-center" v-cloak v-if="!hasImage">
      <span class="rx-item-na" uk-icon="icon: image; ratio: 2"></span>
      <p>Volume is being added or cover is not available.</p>
    </div>
    <img v-else class="rx-title-image" :src="imgSrc" :alt="imgAlt" />
  </div>
</template>

<script>
export default {
  name: "VolumeImage",
  props: {
    imgSrc: { type: String, required: true },
    volumeLabel: { type: String, default: "" }
  },
  data() {
    return { hasImage: true };
  },
  computed: {
    imgAlt() { return `First page of ${this.volumeLabel}`; }
  },
  mounted() {
    const tester = new Image();
    tester.addEventListener("load", () => { this.hasImage = true; });
    tester.addEventListener("error", () => { this.hasImage = false; });
    tester.src = this.imgSrc;
  }
};
</script>