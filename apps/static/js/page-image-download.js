console.log('[readux] page-image-download.js loaded');

(function () {
  var DEBUG = true; // set to false to silence logs
  function log(){ if (DEBUG) try { console.log.apply(console, arguments); } catch(_){} }

  // --- helpers ------------------------------------------------------------
  function stripInfoJson(u) {
    if (!u) return null;
    try { return u.replace(/\/?info\.json$/i, ''); } catch(_) { return u; }
  }
  function absoluteUrl(u) {
    try { return new URL(u, document.baseURI).toString(); } catch(_) { return null; }
  }
  function buildIiifFullJpg(base) {
    var abs = absoluteUrl(stripInfoJson(base));
    if (!abs) return null;
    return abs.replace(/\/$/, '') + '/full/full/0/default.jpg';
  }

  function getLink() { return document.getElementById('rx-download-img'); }
  function getTemplate(el) { return el && el.getAttribute('data-href-template'); }

  // Try to discover the active IIIF image service from the viewer stack
  function svcFromOSD() {
    try {
      var osd = window.osdViewer || window.viewer || window.osd || window.openSeadragonViewer;
      if (!osd || !osd.world || typeof osd.world.getItemAt !== 'function') return null;
      var item = osd.world.getItemAt(0);
      if (!item) return null;
      var ts = item.source || item.tileSource || (item.getTileSource && item.getTileSource());
      var id = ts && (ts['@id'] || ts['id'] || ts['url'] || ts['tileSource']);
      return id ? stripInfoJson(id) : null;
    } catch(_) { return null; }
  }
  function svcFromMirador() {
    try {
      if (window.Mirador && Mirador.viewer && Mirador.viewer.store && Mirador.viewer.store.getState) {
        var st = Mirador.viewer.store.getState();
        var winIds = st && st.windows && Object.keys(st.windows);
        if (!winIds || !winIds.length) return null;
        var win = st.windows[winIds[0]];
        var canvasId = win && win.canvasId;
        return canvasId ? stripInfoJson(canvasId) : null;
      }
    } catch(_) {}
    return null;
  }
  function svcFromNetwork() {
    try {
      var entries = (performance.getEntriesByType && performance.getEntriesByType('resource')) || [];
      for (var i = entries.length - 1; i >= 0; i--) {
        var name = entries[i] && entries[i].name;
        if (!name || /^chrome-extension:/.test(name)) continue;
        if (/\/(full|pct:|\d+,\d+,\d+,\d+)\//.test(name) && /(jpg|jpeg|png|tif|tiff)(\?|$)/i.test(name)) {
          try {
            var url = new URL(name, document.baseURI);
            var parts = url.pathname.split('/').filter(Boolean);
            // IIIF image path ends with 4 trailing segments:
            //   /{region}/{size}/{rotation}/{quality}.{format}
            if (parts.length >= 4) {
              var baseParts = parts.slice(0, parts.length - 4); // remove 4 trailing segments
              var basePath = '/' + baseParts.join('/');
              return url.origin + basePath;
            }
          } catch(_) {}
        }
        if (/\/info\.json(\?|$)/.test(name)) {
          try {
            var url2 = new URL(name, document.baseURI);
            return url2.origin + url2.pathname.replace(/\/info\.json(\?|$).*/, '');
          } catch(_) {}
        }
      }
    } catch(_) {}
    return null;
  }

  function pidFromAnnotator() {
    try {
      if (window.annotator && annotator.currentPage && annotator.currentPage.pid) return annotator.currentPage.pid;
      if (window.readux && readux.state && readux.state.page && readux.state.page.pid) return readux.state.page.pid;
      if (window.Rx && Rx.store && Rx.store.state && Rx.store.state.page && Rx.store.state.page.pid) return Rx.store.state.page.pid;
    } catch (_) {}
    // OpenSeadragon tileSource id often ends with PID; use as a weak fallback
    try {
      var osd = window.osdViewer || window.viewer || window.osd || window.openSeadragonViewer;
      if (osd && osd.world && typeof osd.world.getItemAt === 'function') {
        var item = osd.world.getItemAt(0);
        var ts = item && (item.source || item.tileSource || (item.getTileSource && item.getTileSource()));
        var id = ts && (ts['@id'] || ts['id'] || ts['url']);
        if (id) {
          var parts = id.split('/').filter(Boolean);
          return parts[parts.length - 1];
        }
      }
    } catch(_) {}
    return null;
  }
  function pidFromDom() {
    var el = document.querySelector('[data-page-pid]');
    if (el) return el.getAttribute('data-page-pid');
    var el2 = document.querySelector('.rx-page[data-pid]');
    if (el2) return el2.getAttribute('data-pid');
    return null;
  }

  function currentPid() {
    return (
      pidFromAnnotator() ||
      pidFromDom() ||
      pidFromServiceBase(lastSvc) ||
      pidFromLinkHref() ||
      lastPid
    );
  }
  function pidFromServiceBase(svc) {
    if (!svc) return null;
    try {
      var u = new URL(svc, document.baseURI);
      var parts = u.pathname.split('/').filter(Boolean);
      return parts.length ? parts[parts.length - 1] : null;
    } catch(_) { return null; }
  }

  function pidFromLinkHref() {
    try {
      var el = getLink();
      if (!el || !el.href) return null;
      var u = new URL(el.href, document.baseURI);
      var parts = u.pathname.split('/').filter(Boolean);
      // Remove the 4 trailing IIIF segments if present
      if (parts.length >= 4) {
        var baseParts = parts.slice(0, parts.length - 4);
        if (baseParts.length) return baseParts[baseParts.length - 1] || null;
      }
      return parts.length ? parts[parts.length - 1] : null;
    } catch(_) { return null; }
  }

  var lastPid = null;
  var lastSvc = null;

  function updateLink(el) {
    if (!el) el = getLink();
    if (!el) return;
    // Try service-first for accuracy
    var svc = svcFromNetwork() || svcFromOSD() || svcFromMirador() || lastSvc;
    if (svc) {
      var url = buildIiifFullJpg(svc);
      if (url && el.href !== url) {
        el.href = url;
        lastSvc = svc;
        lastPid = pidFromServiceBase(svc) || lastPid;
        log('[readux] href (svc) ->', url);
        return;
      }
    }
    // Fallback: use template + pid
    var template = getTemplate(el);
    var pid = pidFromAnnotator() || pidFromDom() || lastPid;
    if (template && pid) {
      var u = template.replace('__PID__', encodeURIComponent(pid));
      if (el.href !== u) {
        el.href = u;
        lastPid = pid;
        log('[readux] href (pid) ->', u);
      }
    }
  }

  function ensureWired() {
    var el = getLink();
    if (!el) return;

    // Click-time resolution (always correct at click)
    try {
      el.addEventListener('click', function (e) {
        try { e.preventDefault(); } catch(_) {}
        updateLink(el);
        try { window.open(el.href, '_blank'); } catch(_) {
          try { location.href = el.href; } catch(_) {}
        }
      }, true);
    } catch(_) {}

    // React to common custom events
    ['ecds:page-changed', 'readux:page-changed', 'page-changed'].forEach(function (evt) {
      window.addEventListener(evt, function () { setTimeout(function(){ updateLink(el); }, 0); });
    });

    // OSD events
    try {
      var osd = window.osdViewer || window.viewer || window.osd || window.openSeadragonViewer;
      if (osd && typeof osd.addHandler === 'function') {
        ['open','page','tile-loaded','add-item','remove-item','item-index-change','animation-finish']
          .forEach(function (evt) { osd.addHandler(evt, function(){ setTimeout(function(){ updateLink(el); }, 0); }); });
      }
    } catch(_) {}

    // PerformanceObserver for network tile loads
    try {
      if (window.PerformanceObserver) {
        var po = new PerformanceObserver(function(){ updateLink(el); });
        po.observe({ entryTypes: ['resource'] });
      }
    } catch(_) {}

    // DOM & URL changes
    try {
      var mo = new MutationObserver(function(){ updateLink(el); });
      mo.observe(document.body, { childList:true, subtree:true, attributes:true });
    } catch(_) {}
    window.addEventListener('hashchange', function(){ updateLink(el); });
    window.addEventListener('load', function(){ updateLink(el); });
    document.addEventListener('DOMContentLoaded', function(){ updateLink(el); });

    // Expose manual hook
    window.readuxSetCurrentPid = function (pid) { lastPid = pid; updateLink(el); };

    // initial
    updateLink(el);
  }

  // Wait until the link exists (in case template renders it late)
  if (!getLink()) {
    var wait = setInterval(function(){
      if (getLink()) { clearInterval(wait); ensureWired(); }
    }, 100);
    setTimeout(function(){ try { clearInterval(wait); ensureWired(); } catch(_){} }, 10000);
  } else {
    ensureWired();
  }
})();