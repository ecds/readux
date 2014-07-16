$(document).ready(function() {
    // collection browse cover view
    var $container = $('#collection-covers');
    // init
    $container.isotope({
      // options
      itemSelector: '.collection',
      masonry: {
        columnWidth: 220,
        isFitWidth: true
      }
    });

    // collection browse toggle view modes

    $('#view-toggle a').click(function() {
        console.log(this);
        console.log($(this).attr('id'));
        $('#view-toggle a').removeClass('active');
        var show_id = '#collection-' + $(this).attr('id');
        console.log('show id = ' + show_id);
        $('div[id^="collection-"]').hide().removeClass('hidden');
        $(show_id).show();
        $(this).addClass('active');

    });


});