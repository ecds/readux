/* Marginalia  - margin annotation viewer for annotator */

function annotatorMarginalia(options) {

  var _t = annotator.util.gettext;
  var _app;

  options = options || {};
  // Sets the renderer function for the annotations.
  // Defaults to statard formatting.
  if(options.viewer && typeof options.viewer === 'function'){
    options.viewer = options.viewer;
  }
  else{
    options.viewer = function(annotation){
      if (annotation.text) {
        return annotator.util.escapeHtml(annotation.text);
      } else {
        return "<i>" + _t('No comment') + "</i>";
      }
    };
  }

  options.element = options.element || '.content';
  options.margin_class = options.margin_class || 'margin-container';

  // Container element for annotator
  var $container = $(options.element);

  // Define marginalia annotation container
  var $margin_container = $('<aside/>').attr({
        class:options.margin_class
      });

  // Marginalia variables
  var marginalia_item_class = 'marginalia-item',
      toggle_id = 'toggle-annotations',
      annotations_list_class = 'annotation-list';

// Easing Function for scroll
// from jQuery Easing Plugin (version 1.3)
// http://gsgd.co.uk/sandbox/jquery/easing/
  jQuery.extend( jQuery.easing,{
    easeInOutExpo: function (x, t, b, c, d) {
      if (t==0) return b;
      if (t==d) return b+c;
      if ((t/=d/2) < 1) return c/2 * Math.pow(2, 10 * (t - 1)) + b;
      return c/2 * (-Math.pow(2, -10 * --t) + 2) + b;
    }
  });


  // Object for Marginalia
  // Defined as a object for namespacing references (i.e. marginalia.render)
  var marginalia = {
      start: function (app) {
        _app = app;
        var toggle_html ='<span class="fa fa-file-text-o"></span>',
            toggle_attrs = {
              class:'btn btn-green',
              id: toggle_id,
              alt: 'Toggle Annotations'
            },
            $toggle = $('<a/>')
              .attr(toggle_attrs) // add attributes to the toggle object
              .hide() // hide the toggle object for now, will show when annotations are loaded
              .html(toggle_html); //add the html to the toggle object

        $container.prepend($toggle, $margin_container);

        // get the rendered margin container
        $margin_container = $('.'+options.margin_class);
      },

      render: function(annotation){
        return options.viewer(annotation);
      },

      // Returns the annotion in the marginalia list format
      renderAnnotation: function(annotation){
        var text = $('<div/>').attr({
            class:'text'
            }).html(marginalia.render(annotation)),
            controls = '<nav class="controls"><a class="btn btn-default btn-edit">Edit</a><a class="btn btn-danger btn-delete">Delete</a></nav>',
            $marginalia_item = $('<li/>').attr({
              class:marginalia_item_class,
              'data-annotation-id': annotation.id
            }).append(controls).append(text);

        $marginalia_item.on('click.marginalia','.btn-edit',function(event){
          event.preventDefault();
          var offset = $(this).parent().siblings(".text").offset();

          _app.annotations.update(annotation);
          $(".annotator-editor").css({
            top: offset.top,
            left: offset.left
          });
        })
        .on('click.marginalia','.btn-delete',function(event){
          event.preventDefault();
          _app.annotations['delete'](annotation);
        });

        return $marginalia_item;
      },

      // Add annotations to the sidebar when loaded
      annotationsLoaded: function(annotations){
        //show toggle object once annotations are loaded
        $("#"+toggle_id).show();

        var $annotaton_list = $('<ul/>').attr({
              class:annotations_list_class
            });

        // Display annotations in the marginalia container
        $.each(annotations,function(i){
          var annotation = annotations[i],
          $marginalia_item = marginalia.renderAnnotation(annotation);

          $annotaton_list.append($marginalia_item);
        });

        $margin_container.html($annotaton_list);

        // Add class to container to hide marginalia aside
        $container.addClass('margin-container-hide');

        // Initalize on click.marginalia event for annotation highlights
        $('.annotator-hl').on('click.marginalia',function(event){
          marginalia.annotationSelected(event);
        });

        // Initalize on click.marginalia event for Marginalia items
        $('.'+marginalia_item_class).find('.text').on('click.marginalia',function(event){
          marginalia.itemSelected(event);
        });

        // Initalize toggle control for marginalia container
        $('#'+toggle_id).on('click.marginalia',function(event){
          event.preventDefault();
          var $this = $(this);

          if($this.hasClass('active')){
            marginalia.toggle.hide();
          }
          else{
            marginalia.toggle.show();
          }
        });

      },

      // Add marginalia when annotations are created
      annotationCreated: function(annotation){
        var $marginalia_item = marginalia.renderAnnotation(annotation);
        // Append to annotations list...
        $('.'+annotations_list_class).append($marginalia_item);
        // highlight created...
        marginalia.onSelected(annotation.id);
        // and show marginalia container.
        marginalia.toggle.show();
      },

      // Remove marginalia when annotations are removed
      beforeAnnotationDeleted: function(annotation){
        var $marginalia_item = $('.'+marginalia_item_class+'[data-annotation-id='+annotation.id+']');
        $marginalia_item.remove();
      },

      // Update marginalia when annotations are updated
      annotationUpdated: function(annotation){
        var $marginalia_item = $('.'+marginalia_item_class+'[data-annotation-id='+annotation.id+']'),
            updated_text = marginalia.render(annotation);

        $marginalia_item.find(".text").html(updated_text);
      },

      // Toggle functions for the margin container
      toggle: {

        show: function(){
          $container.addClass('margin-container-show');
          $container.removeClass('margin-container-hide');

          $('#'+toggle_id).addClass('active');

          if(options.toggle.show){
            options.toggle.show();
          }
        },

        hide: function(){
          $container.addClass('margin-container-hide');
          $container.removeClass('margin-container-show');

          $('#'+toggle_id).removeClass('active');

          if(options.toggle.hide){
            options.toggle.hide();
          }
        }
      },

      // Custom event for when an annotation is selected
      // Highlight the marginalia item associated with the annotation
      annotationSelected: function(event) {
        event.stopPropagation();

        var $annotation_highlight = $(event.target),
            annotation_id = $annotation_highlight.data('annotation-id');

        marginalia.onSelected(annotation_id);
      },

      // On Marginalia item select event
      // Highlight the annotation highlight associated with the item
      itemSelected: function(event){
        event.stopPropagation();

        var $marginalia_item = $(event.target).parents('.' + marginalia_item_class),
            annotation_id = $marginalia_item.data('annotation-id');
        marginalia.onSelected(annotation_id);
      },

      clearHighlights: function(){
        $('.marginalia-item-selected').removeClass('marginalia-item-selected');
        $('.marginalia-annotation-selected').removeClass('marginalia-annotation-selected');
      },

      applyHighlights: function($annotation, $item){
        marginalia.clearHighlights();

        $annotation.addClass('marginalia-annotation-selected');
        $item.addClass('marginalia-item-selected');
      },

      onSelected: function(annotation_id){
        var id = annotation_id,
            $annotation = $('.annotator-hl'+'[data-annotation-id='+id+']'),
            $item = $('.' + marginalia_item_class + '[data-annotation-id=' + id + ']' );

        // Return false if the id is undefined
        if(id === undefined){
          return false;
        }

        // Return false if the item is already selected to prevent
        // jumping to the top when highlighting text.
        if ($item.hasClass("marginalia-item-selected")){
            return false;
        }

        $margin_container = $('.'+options.margin_class);

        // Scroll to the position of the item
          var cTop = $('.margin-container').offset().top,
              cScrollTop = $('.margin-container').scrollTop(),
              top = $item.position().top,
              top2 = $annotation.parents('.ocr-line').position().top;

          $margin_container.stop().animate({'scrollTop':top-top2+30},500,'easeInOutExpo');


        // Highlight selected parts
        marginalia.applyHighlights($annotation, $item);

        // Show marginalia container
        marginalia.toggle.show();

      }
  };
  // return marginalia object
  return marginalia;
}
