$(document).ready(function() {
	var $container = $('.collection-list');
	// init
	$container.isotope({
	  // options
	  itemSelector: '.collection',
	  masonry: {
      columnWidth: 220,
      isFitWidth: true
    }
	});
})