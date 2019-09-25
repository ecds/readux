/* Project specific Javascript goes here. */
    $bannerInfo = $('.collection-image-info');

    $bannerInfo.on('click',function(){
        $(this).toggleClass('collasped');
    });


    // Iterate through menu items and highlight the current page if it matches the URL
    $.each($(".rx-nav-item"), function(index, navItem) {
        var segmentsInURL = (location.pathname.split('/').length - 1) - (location.pathname[location.pathname.length - 1] == '/' ? 1 : 0);
        var atModuleRoot = (segmentsInURL > 1) ? false:true;
        var activePage = window.location.pathname.replace(
          /^\/([^\/]*).*$/,
          "$1"
        );
        if (navItem.href.includes(activePage) && (activePage != "") && atModuleRoot) {
          navItem.classList.add("uk-active");
        }
    });