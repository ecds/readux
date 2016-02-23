/*** deprecated browser function ***/
(function() {
    var matched, browser;

    // Use of jQuery.browser is frowned upon.
    // More details: http://api.jquery.com/jQuery.browser
    // jQuery.uaMatch maintained for back-compat
    jQuery.uaMatch = function( ua ) {
        ua = ua.toLowerCase();

        var match = /(chrome)[ \/]([\w.]+)/.exec( ua ) ||
            /(webkit)[ \/]([\w.]+)/.exec( ua ) ||
            /(opera)(?:.*version|)[ \/]([\w.]+)/.exec( ua ) ||
            /(msie) ([\w.]+)/.exec( ua ) ||
            ua.indexOf("compatible") < 0 && /(mozilla)(?:.*? rv:([\w.]+)|)/.exec( ua ) ||
            [];

        return {
            browser: match[ 1 ] || "",
            version: match[ 2 ] || "0"
        };
    };

    matched = jQuery.uaMatch( navigator.userAgent );
    browser = {};

    if ( matched.browser ) {
        browser[ matched.browser ] = true;
        browser.version = matched.version;
    }

    // Chrome is Webkit, but Webkit is also Safari.
    if ( browser.chrome ) {
        browser.webkit = true;
    } else if ( browser.webkit ) {
        browser.safari = true;
    }

    jQuery.browser = browser;
})();

$(document).ready(function() {
    // collection browse cover view
    var $container = $('#cover-list');
    // init
    var item_width = 220;
    if($('.cover-view.landscape').length>0){
      item_width = 370;
    }
    $container.isotope({
      // options
      itemSelector: 'li',
      masonry: {
        columnWidth: item_width,
        isFitWidth: true
      },
      transitionDuration:'0.4s'
    });

    $bannerInfo = $('.collection-image-info');

    $bannerInfo.on('click',function(){
        $(this).toggleClass('collasped');
    });


    $(".page-header .expand").on('click',function(evt){
        evt.preventDefault();
        $(this).toggle().siblings('.continued').toggle();
    });

    $('.page-header .continued').on('click',function(evt){
        evt.preventDefault();
        $(this).toggle().siblings('.expand').toggle();
    });

    $(".page-search .trigger").on('click',function(evt){
      evt.preventDefault();
      $(this).toggleClass('active');
      $(".page-search .row").stop().slideToggle();
    });

    $('img.page-image').on('error', function(evt) {
        $('.page').addClass('image-error');
        $(this).attr('src', error_images.single_page);
    });
    $('img.cover-mini-thumb').on('error', function(evt) {
        $(this).attr('src', error_images.cover_mini_thumb);
    });

    function export_generating(cookie_id) {
        // show the "generating" spinner
        $('#export-generating').removeClass('hidden');
        // check for the cookie by requested id and hide the spinner
        var check_complete = window.setInterval(check_cookie, 500);
        function check_cookie() {
          if (Cookies.get(cookie_id) == 'complete') {
              $('#export-generating').addClass('hidden');
              Cookies.remove(cookie_id);
              clearInterval(check_complete);
          }
        }
    }

    // volume export indicator for long-running downloads
    $("a.volume-export").on('click', function(evt) {
        export_generating(this.id);
    });
    $("form.volume-webexport").on('submit', function(evt) {
        export_generating($(this).find("input[name='completion-cookie']").attr('value'));
    });

    // turn on bootstrap tooltips
    $(function () {
      $('[data-toggle="tooltip"]').tooltip();
    })
});
