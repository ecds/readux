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

            // create serach input
            var input = $(document.createElement('input'))
                .attr('type', 'text')
                .attr('placeholder', options.placeholder_text);
            options.element.append(input);

            /* enable autocomplete on search input */
            $(input).autocomplete({
                minLength: 2,
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
                    // if annotation is for another page, go there
                    // TODO: can we use a hash to select annotation?
                    if (window.location.href != ui.item.uri) {
                        window.location.assign(ui.item.uri);
                    }
                    // otherwise, select the annotation on this page
                    // TODO: make select action configurable
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