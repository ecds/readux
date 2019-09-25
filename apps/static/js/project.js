/* Project specific Javascript goes here. */
    $bannerInfo = $('.collection-image-info');

    $bannerInfo.on('click',function(){
        $(this).toggleClass('collasped');
    });


    // Iterate through menu items and highlight the current page if it matches the URL
    $.each($(".rx-nav-item"), function(index, navItem) {
        var activePage = window.location.pathname.replace(
          /^\/([^\/]*).*$/,
          "$1"
        );
        if (navItem.href.includes(activePage)) {
            navItem.classList.add("uk-active");
        }
    });