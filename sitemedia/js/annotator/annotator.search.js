/* search for annotations */

function annotatorSearch(user_options) {

    var _app, storage;

    // default options
    var options = {
      // element where search input should be added
      element: $('.annotation-search'),
      // annotation render method
      render: null,
      // optional search filter
      filter: {},
      // input placeholder text
      placeholder_text: 'Search annotations'
    };
    $.extend(options, user_options || {});

    // Object for search
    // Defined as a object for namespacing references
    var annotatorSearch = {
        start: function (app) {
            _app = app;
            storage = _app.registry.getUtility('storage');

            // find search input element
            var input = options.element.find('input').first();
            /* enable autocomplete on search input */
            $(input).autocomplete({
                minLength: 2,
                // include the autocomplete on the element, to simplify
                // styling and placement issues
                appendTo: options.element,
                source: function( request, response ) {
                    // use annotator storage query as the source
                    var search_opts = {keyword: request.term}
                    $.extend(search_opts, options.filter);
                    storage.query(search_opts)
                        .then(function(results, meta) {
                            response(results.results);
                    })
                },
                select: function( event, ui ) {
                    // if annotation is for another page, load it
                    // add annotation id as hash, so it can be selected
                    // if a trigger for that is supported
                    if (window.location.href != ui.item.uri) {
                        window.location.assign(ui.item.uri + '#' + ui.item.id);
                    }
                    // otherwise, select the annotation on this page
                    // by triggering the corresponding highlight change
                    $annotation = $('.annotator-hl[data-annotation-id='+ui.item.id+']');
                    $annotation.trigger('click');
                }
            })
            .autocomplete( "instance" )._renderItem = function( ul, item ) {
              return $("<li>")
                .addClass('annotation-search-result')
                .attr('id', item.uri)
                .append(options.render(item))
                .appendTo(ul);
            };
        },
     };
  // return annotatorSearch object
  return annotatorSearch;
}