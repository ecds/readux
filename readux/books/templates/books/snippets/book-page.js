{% load static %}

<script type="text/javascript" charset="utf-8">
   $(document).ready(function () {
      // set up seadragon configuration (not loaded unless triggered by user)
      set_seadragon_opts({
          id: "zoom-page",
          prefixUrl: "{% static 'js/openseadragon/images/' %}",
          tileSources: "{% url 'deepzoom:dzi' page.pid %}",
          toolbar: 'deepzoom-controls',
          showNavigator: true,
          navigatorPosition: 'TOP_LEFT',
          zoomInButton: 'dz-zoom-in',
          zoomOutButton: 'dz-zoom-out',
          homeButton: 'dz-home',
          fullPageButton: 'dz-fs',
      });

      {# only enable annotation if tei is present for logged in users #}
      {% if page.tei.exists and user.is_authenticated %}
      var content = $('.content .inner').annotator();

      // Convert Markdown to HTML in the preview when the annotation is shown.
      // content.on("annotationViewerShown",function(){
      //   var $this = $(this).find('.annotator-viewer:not(.annotator-hide) .annotator-item>.annotator-controls+div'),
      //       markdown = $this.html(),
      //       html = Markdown(markdown);
      //   $this.html(html);
      // });

      var optionsStore = {
            // use local annotator storage
            prefix: '{% url "annotation-api-prefix" %}',
            annotationData: {
                // Attach the uri of the current page to all annotations to allow search.
                'uri': '{{ page.absolute_url }}',
               {% if page.ark_uri %},'ark': '{{ page.ark_uri }}'{% endif %}
            },
            loadFromSearch: {
                'uri': '{{ page.absolute_url }}'
            }
       };

      content.annotator('addPlugin', 'Store', optionsStore);

      var optionsMeltdown = {
        fullscreen: true,
        openPreview: false,
        sidebyside: false
      };

      content.annotator('addPlugin','MarginViewer');


      // Init markdown editor
      jQuery('textarea').meltdown(optionsMeltdown);
      {% endif %} {# end annotation config #}

   });
   {% if page.tei.exists %}
   // adjust ocr word & letter spacing on load & resize, with a timeout
   // to avoid adjusting too frequently as the browser is resized

      var resizeTimer; // Set resizeTimer to empty so it resets on page load
      function resizeFunction() {
          // adjust font sizes based on container to use viewport height
          $(".page img").relativeFontHeight({elements: $('.ocr-line')});
          // adjust ocr text on window load or resize
          $(".ocrtext").textwidth();
      };

      // On resize, run the function and reset the timeout with a 250ms delay
      $(window).resize(function() {
          clearTimeout(resizeTimer);
          resizeTimer = setTimeout(resizeFunction, 250);
      });

     $(window).load(function() {  // wait until load completes, so widths will be calculated
         resizeFunction();
     });
   {% endif %}
</script>
