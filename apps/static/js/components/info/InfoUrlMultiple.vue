<template>
  <div class="rx-info-content">
    <div class="rx-info-content-label"><span>{{ label }}</span></div>
    <div><slot /></div>
  </div>
</template>

<script>
export default { name: "InfoUrlMultiple", props: { label: { type: String, default: "" } } };
</script>