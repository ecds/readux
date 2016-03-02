/**
Annotator plugin for related pages.

- editor extension adds a multi-value autocomplete field to search for
  pages in the same volume and add them to the annotation record
  by ARK URI (requires a search url option)
- marginalia render extension to display related pages
- uses jquery-ui autocomplete for editor input field

*/
var related_pages = {

    split: function (val) {
        return val.split(/,\s*/);
    },
    extractLast: function (term) {
        return related_pages.split(term).pop();
    },

    renderExtension: function(annotation, item) {
        // replace existing related pages block with updated version
        var rel_pages = related_pages.renderRelatedPages(annotation);
        item.find('.annotator-related-pages').remove();
        // insert related pages (if any) before tags or footer, whichever comes first
        if (rel_pages != '') {
            rel_pages.insertBefore(item.find('.annotator-tags,.annotation-footer').first());
        }
        return item;
    },

    arkNoid: function(ark_uri) {
        // return the noid portion of an ark uri for short-hand display
        // (assumes unqualified ark)
        return ark_uri.split('/').pop();
    },

    renderRelatedPages: function(annotation) {
        var rel_pages = '';
        if (annotation.related_pages && $.isArray(annotation.related_pages) &&
                                  annotation.related_pages.length) {
          rel_pages = $('<div/>').addClass('annotator-related-pages').html(function () {
            return 'Related pages: ' + $.map(annotation.related_pages, function (related_page) {
              return '<a href="' + related_page + '">' +
                     related_pages.arkNoid(related_page) + '</a>';
              }).join(', ');
          });
        }
        return rel_pages;
      },

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
                annotation.related_pages = related_pages.split(input.val()).filter(function(el, index, arr){
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
                        keyword: related_pages.extractLast( request.term )
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
                  var terms = related_pages.split(this.value);
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


