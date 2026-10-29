<template>
  <div class="rx-info-content">
    <div v-if="label" class="rx-info-content-label">{{ label }}</div>
    <div class="rx-info-content-value">
      <!-- Full content is rendered until mounted() measures it; if it's over the
           limit we capture its HTML, drop it, and show the preview + link. -->
      <div v-if="!collapsed" ref="content"><slot /></div>
      <template v-else>
        <span>{{ preview }}&#8230; </span>
        <a href="#" class="rx-info-read-more" @click.prevent="showModal = true"
          >Show more</a
        >
      </template>
    </div>

    <teleport to="body">
      <div
        v-if="showModal"
        class="rx-meta-modal-overlay"
        @click.self="showModal = false"
      >
        <div class="rx-meta-modal-dialog" role="dialog" aria-modal="true">
          <button
            type="button"
            class="rx-meta-modal-close"
            aria-label="Close"
            @click="showModal = false"
          >
            &times;
          </button>
          <div v-if="label" class="rx-info-content-label">{{ label }}</div>
          <div class="rx-info-content-value rx-meta-modal-body" v-html="fullHtml"></div>
        </div>
      </div>
    </teleport>
  </div>
</template>

<script>
export default {
  name: "MetadataField",
  props: {
    label: { type: String, default: "" },
    // Character limit above which the value collapses behind "Show more".
    limit: { type: Number, default: 750 },
  },
  data() {
    return { collapsed: false, preview: "", fullHtml: "", showModal: false };
  },
  mounted() {
    const el = this.$refs.content;
    if (!el) return;
    const text = (el.textContent || "").replace(/\s+/g, " ").trim();
    if (text.length > this.limit) {
      // Capture the full (possibly HTML) content for the modal before collapsing.
      this.fullHtml = el.innerHTML;
      // Plain-text preview, trimmed back to a word boundary.
      this.preview = text.slice(0, this.limit).replace(/\s+\S*$/, "");
      this.collapsed = true;
    }
    this._onKeydown = (e) => {
      if (e.key === "Escape") this.showModal = false;
    };
    document.addEventListener("keydown", this._onKeydown);
  },
  beforeUnmount() {
    document.removeEventListener("keydown", this._onKeydown);
    document.body.classList.remove("rx-meta-modal-open");
  },
  watch: {
    showModal(open) {
      // Prevent the page behind the modal from scrolling.
      document.body.classList.toggle("rx-meta-modal-open", open);
    },
  },
};
</script>
