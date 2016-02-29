function split(val) {
    return val.split(/,\s*/);
}
function extractLast(term) {
    return split(term).pop();
}


var related_pages = {

    getEditorExtension: function getEditorExtension(options) {
            // define a new editor function, with the configured
            // search url to find pages

            return function editorExtension(editor) {
            // The input element added to the Annotator.Editor wrapped in jQuery.
            // Cached to save having to recreate it everytime the editor is displayed.
            var field = null;
            var input = null;

            function updateField(field, annotation) {
                // convert list of related uris stored in the annnotation
                // into a comma-separated list for the form
                var value = '';
                if (annotation.related_pages) {
                    value = annotation.related_pages.join(', ') + ', ';
                }
                input.val(value);
            }

            function setRelatedPages(field, annotation) {
                // split comma-separated uris into an array,
                // removing any empty or duplicated values
                annotation.related_pages = split(input.val()).filter(function(el, index, arr){
                    return el !== '' && index === arr.indexOf(el);
                });
            }

            field = editor.addField({
                label: _t('Add related pages by permalink or search') + '\u2026',
                load: updateField,
                submit: setRelatedPages,
                type: 'textarea'
            });


            input = $(field).find(':input');
            input.addClass('related-pages');

            /* enable autocomplete on related pages input */
            $(".related-pages").relatedPageComplete({
                minLength: 2,
                source: function( request, response ) {
                    $.getJSON(options.search_url, {
                        keyword: extractLast( request.term )
                    }, response );
                },
                open: function(event, ui) {
                    /* annotator purposely sets the editor at a higher z-index
                    than anything else on the page; make sure the autocomplete
                    menu is still higher so it isn't obscured by annotator buttons */
                    $('.ui-autocomplete').zIndex($(event.target).zIndex() + 1);
                },
                select: function( event, ui ) {
                  /* multi-valued input */
                  var terms = split(this.value);
                  // remove the current input (seach term)
                  terms.pop();
                  // add the selected item
                  terms.push(ui.item.uri);
                  // add placeholder to get the comma-and-space at the end
                  terms.push("");
                  this.value = terms.join(", ");
                  return false;
                },
                focus: function() {
                    // prevent value inserted on focus
                    return false;
                },
                position: { my : "right top", at: "right bottom" }
            });


        }
    }
};


/* extend autocomplete for custom render item method */
$.widget("readux.relatedPageComplete", $.ui.autocomplete, {
    _renderItem: function(ul, item) {
         var li = $("<li>")
            .attr("data-value", item.uri)
            .append('<img class="pull-right" src="' + item.thumbnail + '"/>')
            .append('<h3>' + item.label + '</h3>');
        if (item.highlights && item.highlights.length > 0) {
            li.append('<p>...' + item.highlights[0] + '...</p>');
        }
        li.append('<p class="text-muted small">' + item.uri + '</p>');

        return li.appendTo(ul);
    },
});


