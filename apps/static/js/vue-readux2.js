import Vue from 'vue';                 // will resolve to vue/dist/vue.esm.js via alias
import App from './App.vue';           // your SFC
window.Vue = Vue; // TEMP: for legacy scripts that expect global Vue
console.log('[boot] Vue version =', Vue.version);

new Vue({
  delimiters: ['[[', ']]'],   // 👈 custom delimiters
  render: h => h(App),
}).$mount('#v-readux');                // matches HTML <div id="v-readux">