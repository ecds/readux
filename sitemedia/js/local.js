$(document).ready(function() {
    // collection browse cover view
    var $container = $('#cover-list');
    // init
    $container.isotope({
      // options
      itemSelector: 'li',
      masonry: {
        columnWidth: 220,
        isFitWidth: true
      },
      transitionDuration:'0.4s'
    });

    // collection browse toggle view modes
    $('#view-toggle a').click(function() {
        $('#view-toggle a').removeClass('active');
        var show_filter = '.coverlist-toggle > .item-' + $(this).attr('id');
        $('.coverlist-toggle > div[class^="item-"]').hide().removeClass('hidden');
        $(show_filter).show();
        $(this).addClass('active');
        var href= $(this).attr('href') ||'';
        window.location.hash = href;
    });

    var hash = window.location.hash; 

    if(hash){
      if(hash.indexOf('list-view')>0){
        $("a#list").click();
      }
      else if(hash.indexOf('covers-view')>0){
        $("a#covers").click();
      }
    }
});