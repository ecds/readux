$(document).ready(function() {
    // collection browse cover view
    var $container = $('#cover-list');
    // init
    $container.isotope({
      // options
      itemSelector: '.cover',
      masonry: {
        columnWidth: 220,
        isFitWidth: true
      }
    });

    // collection browse toggle view modes
    $('#view-toggle a').click(function() {
        $('#view-toggle a').removeClass('disabled');
        var show_filter = '.coverlist-toggle > .item-' + $(this).attr('id');
        $('.coverlist-toggle > div[class^="item-"]').hide().removeClass('hidden');
        $(show_filter).show();
        $(this).addClass('disabled');
    });


});