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


    // sort items displayed by appending/updating search params in URL
    function ascaddURL(element) {
      $(element).attr("href", function() {
        if (window.location.search.length == 0) {
          this.href = this.href + "?sort=title&order=asc";
          return this.href;
        } else if (window.location.search.match(/[?&]order=asc/gi)) {
          this.href = this.href.replace("order=asc", "order=asc");
          return this.href;
        } else if (window.location.search.match(/[?&]order=desc/gi)) {
          this.href = this.href.replace("order=desc", "order=asc");
          return this.href;
        } else {
          this.href = this.href + "&order=asc";
          return this.href;
        }
      });
    }

    // sort items displayed by appending/updating search params in URL
    function descaddURL(element) {
      $(element).attr("href", function() {
        if (window.location.search.length == 0) {
          this.href = this.href + "?sort=title&order=desc";
          return this.href;
        } else if (window.location.search.match(/[?&]order=asc/gi)) {
          this.href = this.href.replace("order=asc", "order=desc");
          return this.href;
        } else if (window.location.search.match(/[?&]order=desc/gi)) {
          this.href = this.href.replace("order=desc", "order=desc");
          return this.href;
        } else {
          this.href = this.href + "&order=desc";
          return this.href;
        }
      });
    }


    // use an a element to log out
    function rxSignout() {
      debugger;
      $("#rx-sign-out-form").submit();
    }