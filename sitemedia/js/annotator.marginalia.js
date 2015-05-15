/* Marginalia  - margin annotation viewer for annotator */

function annotatorMarginalia(options) {

  var _t = annotator.util.gettext;

  options = options || {};
  options.element = options.element || '.content';
  options.margin_class = options.margin_class || 'margin-container';

  // Container element for annotator
  var $container = $(options.element);

  // Define marginalia annotation container
  var $margin_container = $("<aside/>").attr({
        class:options.margin_class
      });

  // Marginalia variables
  var marginalia_item_class = "marginalia-item",
      toggle_id = "toggle-annotations";

  // Object for Marginalia
  // Defined as a object for namespacing references (i.e. marginalia.render)
  var marginalia = {
      start: function (app) {
        var toggle_html ='<span class="fa fa-file-text-o"></span>',
            toggle_attrs = {
              class:"btn btn-green",
              id: toggle_id,
              alt: "Toggle Annotations"
            },
            $toggle = $("<a/>").attr(toggle_attrs).html(toggle_html);

        $container.prepend($toggle, $margin_container);
        $margin_container = $("."+options.margin_class);
      },

      render: function(annotation){
        return annotator.ui.markdown.render(annotation);
      },

      // Add annotations to the sidebar when loaded
      annotationsLoaded: function(annotations){

        var $annotaton_list = $("<ul/>").attr({
              class:"annotation-list"
            });

        // Display annotations in the marginalia container
        $.each(annotations,function(i){
          var annotation = annotations[i],
              text = marginalia.render(annotation),
              $annotation = $("<li/>").attr({
                class:marginalia_item_class,
                "data-annotation-id": annotation.id
              }).append(text);

            $annotaton_list.append($annotation);
        });

        $margin_container.html($annotaton_list);

        // Add class to container to hide marignalia aside
        $container.addClass("margin-container-hide");

        // Initalize on click event for annotation highlights
        $(".annotator-hl").on("click",function(event){
          marginalia.annotationSelected(event);
        });

        // Initalize on click event for Marginalia items
        $("."+marginalia_item_class).on("click",function(event){
          marginalia.itemSelected(event);
        });

        // Initalize toggle control for marginalia container
        $("#"+toggle_id).on('click',function(event){
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

      // Toggle functions for the margin container
      toggle: {

        show: function(){
          $container.addClass('margin-container-show');
          $container.removeClass('margin-container-hide');

          $("#"+toggle_id).addClass('active');

          if(options.toggle.show){
            options.toggle.show();
          }
        },

        hide: function(){
          $container.addClass('margin-container-hide');
          $container.removeClass('margin-container-show');

          $("#"+toggle_id).removeClass('active');

          if(options.toggle.hide){
            options.toggle.hide();
          }
        }
      },

      // Update marginalia when annotations are updated
      annotationUpdated: function(annotation){
        var $marginalia_item = $("."+marginalia_item_class+"[data-annotation-id="+annotation.id+"]"),
            updated_text = marginalia.render(annotation);

        $marginalia_item.html(updated_text);
      },

      // On Annotation selected event
      // Highlight the marginalia item associated with the annotation
      annotationSelected: function(event) {
        event.stopPropagation();

        var $annotation_highlight = $(event.target),
            annotation_id = $annotation_highlight.data("annotation-id");

        marginalia.onSelected(annotation_id);
      },

      // On Marginalia item select event
      // Highlight the annotation highlight associated with the item
      itemSelected: function(event){
        event.stopPropagation();

        var $marginalia_item = $(event.target).parents("." + marginalia_item_class),
            annotation_id = $marginalia_item.data("annotation-id");
        marginalia.onSelected(annotation_id);
      },

      clearHighlights: function(){
        $(".marginalia-item-selected").removeClass("marginalia-item-selected");
        $(".marginalia-annotation-selected").removeClass("marginalia-annotation-selected");
      },

      applyHighlights: function($annotation, $item){
        marginalia.clearHighlights();

        $annotation.addClass("marginalia-annotation-selected");
        $item.addClass("marginalia-item-selected");
      },

      onSelected: function(annotation_id){
        var id = annotation_id,
            $annotation = $(".annotator-hl"+"[data-annotation-id="+id+"]"),
            $item = $("." + marginalia_item_class + "[data-annotation-id=" + id + "]" );

        // Highlight selected parts
        marginalia.applyHighlights($annotation, $item);

        // Show marginalia container
        marginalia.toggle.show();

      }
  };
  // return marginalia object
  return marginalia;
}
