/* Project specific Javascript goes here. */
    $bannerInfo = $('.collection-image-info');

    $bannerInfo.on('click',function(){
        $(this).toggleClass('collasped');
    });