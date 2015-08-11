/* ImageSelect - image selection and annotation for annotator

Requires imgAreaSelect.js.
http://odyniec.net/projects/imgareaselect/

Specify the image(s) to be selected when including the module, e.g.

    .include(annotatorImageSelect, {
        element: $('.content img'),
    })


*/

function annotatorImageSelect(options) {
  var _t = annotator.util.gettext,
    global = this;  // equivalent to previously used annotator.util.getGlobal()

  options = options || {};

  // Object to hold local state
  var s = {
    interactionPoint: null,
    ias: null
  };

  // utility methods to support image annotation
  var imgselect_utils = {
    // image area inital setup
    selectionSetup:function(){
      $(document)
        .on('click.imgselection','.imgareaselect-outer, .annotator-cancel',function(evt){
          var $active = $(".active-img-selection");
          $active.removeClass('active-img-selection');
        });
      return true;
    },

    // image area selection start event
    selectionStart: function(img, selection) {
      // hide editor if visible
      var $visible_editor = $(".annotator-editor:not(.annotator-hide)");
      if ($visible_editor.length>0){
        $visible_editor.addClass('annotator-hide');
      }
      // hide the adder whenever a new selection is started
      s.adder.hide();
      // unselect any selected text to avoid confusion
      // between text/image selection & annotation
      global.getSelection().removeAllRanges();
    },

    // image area selection change event
    selectionChange: function(img, selection) {
      // hide the adder whenever a new selection is started
      s.adder.hide();
      // hide the text selection adder.
      var $visible_editor = $(".annotator-editor:not(.annotator-hide)");
      if ($visible_editor.length>0){
        $visible_editor.addClass('annotator-hide');
      }
      // TODO: hide text selection adder if possible

    },

    // image area selection end event
    selectionEnd: function(img, selection) {
      // only display adder once selection gets above a certain
      // minimum size
      // TODO: make min size configurable (?)
      if (selection.width < 25 || selection.height < 25) {
        return;
      }
      // create a preliminary annotation object.
      // based on makeAnnotation from annotator.ui.main
      var annotation =  {
        quote: '',   // image selection = no text quotation
        // NOTE: normal highlights include xpath dom ranges
        // we don't have anything like that, but annotator
        // seems happy enough with an empty list.
        ranges: [],
        // image selection details
        image_selection: imgselect_utils.imageSelection(img, selection)
      };
      $(".annotator-adder+div").addClass('active-img-selection');
      // calculate "interaction point" - using top right of selection box
      s.interactionPoint = imgselect_utils.selectionPosition(img, selection);
      // show the annotation adder button
      s.adder.load(annotation, s.interactionPoint);

      // set editor window is not positioned relative to the adder element
      var offset = $(s.adder.element[0]).offset();
      if(offset){
        $(".annotator-editor").css({
          top: offset.top + 50,
          left: offset.left - (selection.width/2)
        });
      }
    },

    // draw a highlight element for an image annotation
    drawImageHighlight: function(annotation) {
      // if annotation is not an image selection annotation,
      // or does not provide needed attributes, skip
      if (! annotation.image_selection || ! annotation.image_selection.src) {
        return;
      }
      var imgselection = annotation.image_selection;
      var img = $('img[src$="' + imgselection.src + '"]').first();
      if (img.length === 0) {
        // if the highlighted image is not found, skip
        return;
      }
      // create a highlight element
      var hl = $(document.createElement('span'));
      hl.addClass('annotator-hl');
      // set position, width, height, annotation id
      hl.css({
        width: imgselection.w,
        height: imgselection.h,
        left: imgselection.x,
        top: imgselection.y,
        position: 'absolute',
        display: 'block'
      });
      // Add a data attribute for annotation id if the annotation has one
      if (typeof annotation.id !== 'undefined' && annotation.id !== null) {
       hl.attr('data-annotation-id', annotation.id);
     }
     // Save the annotation data on each highlighter element.
     hl.data('annotation', annotation);

     // add highlight to img parent element
     // NOTE: this relies on readux style/layout for correct placement
     img.parent().append(hl);

      return true;
    },

    // get position from image + selection
    selectionPosition: function(img, selection) {
      // based on annotator.util.mousePosition
      // body offset logic borrowed from annotator.util
      var body = global.document.body;

      var offset = {top: 0, left: 0};
      if ($(body).css('position') !== "static") {
        offset = $(body).offset();
      }
      // get position based on image offset + selection position
      var img_offset = $(img).offset();
      // setting adder to top right corner of selection for now
      return {
        top: img_offset.top + selection.y1 - offset.top,
        left: img_offset.left + selection.x2 - offset.left
      };
    },

    percent: function(val) {
      // convert image position/size number into percentage
      // for storing in the annotation and displaying highlight
      return Number(val*100).toFixed(2) + '%';
    },

    imageSelection: function(img, selection) {
      // image selection information to be
      // stored with the annotation, so that we can load
      // and display highlighted region

      var percent = imgselect_utils.percent;

      // storing all dimensions as percentages so it can
      // be scaled for different sizes if necessary
      var w = (selection.x2 - selection.x1) / img.width,
         h = (selection.y2 - selection.y1) / img.height;
      return {
        // full uri to the image
        uri: img.src,
        // store src as it appears in the document, so we can find it again
        src: $(img).attr('src'),
        x: percent(selection.x1 / img.width),
        y: percent(selection.y1 / img.height),
        w: percent(w),
        h: percent(h)
      };
    },

  };

  // export annotator module hooks
  return {

    // when annotator starts, load & configure image selection
      start: function (app) {
          if (!jQuery.imgAreaSelect || typeof jQuery.imgAreaSelect !== 'function') {
              console.warn(_t("To use the ImageSelect annotator module, you must " +
                  "include imgAreaSelect in the page."));
              return;
          }
          // NOTE: might be possible to set fallback logic to identify
          // annotable image content, but this is probably good enough for now.
          if (! options.element) {
              console.warn(_t("To use the ImageSelect annotator module, you must " +
                  "configure elements for image selection."));
              return;
          }

          // enable image selection on configured annotatable image
          s.ias = options.element.imgAreaSelect({
              instance: true,  // return an instance for later interaction
              handles: true,
              onInit: imgselect_utils.selectionSetup,
              onSelectStart: imgselect_utils.selectionStart,
              onSelectChange: imgselect_utils.selectionChange,
              onSelectEnd: imgselect_utils.selectionEnd,
              keys: true
           });

          // Customize the mouse cursor to indicate when configured image
          // can be selected for annotation.
          options.element.css({'cursor': 'crosshair'});

          // create annotation adder
          // borrowed from annotator.ui.main
          s.adder = new annotator.ui.adder.Adder({
            onCreate: function (ann) {
                app.annotations.create(ann);
            }
          });
          s.adder.attach();

          return true;
      },

      beforeAnnotationCreated: function(annotation) {
        // hide the image selection tool
        s.adder.hide();
        // cancel image selection box if there is one
        // (mirrors annotator logic for unselecting text)
        if (s.ias !== null) {
          s.ias.cancelSelection();
        }
        return true;
      },

      annotationCreated: function(annotation) {
        // hide highlight
        $(".active-img-selection").removeClass('active-img-selection');
        // show image highlight div for new image annotation
        imgselect_utils.drawImageHighlight(annotation);
        return true;
      },

      // nothing to do for annotationUpdated
      // (image selection not currently editable)

      beforeAnnotationDeleted: function(annotation) {
        // remove highlight element for deleted image annotation
        if (annotation.id && annotation.image_selection) {
            $('.annotator-hl[data-annotation-id='+ annotation.id +']').remove();
        }
        return true;
      },

      annotationsLoaded: function(annotations) {
        // look for any annotations with an image-selection
        // and create positioned div based on the selection coordinates
        // using the same styles as text annotations.
        $.each(annotations, function(i){
          imgselect_utils.drawImageHighlight(annotations[i]);
        });
        // return true so annotator will draw text highlights normally
        return true;
      },

  };
}
