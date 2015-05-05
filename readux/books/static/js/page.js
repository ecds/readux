/**
jQuery plugin to adjust the width of a portion of text.  Expects a
block element, with the desired width set, and an inner span element
with the text that should be adjusted.  Uses CSS word-spacing and
letter-spacing to adjust the actual width to the desired width.
*/
(function($) {
    $.fn.textwidth = function() {
        // minimum allowed letterspacing
        var min_letterspace = -0.5;
        // actual vs desired size discrepancy small enough to ignore
        var allowable_discrepancy = 2;

        return this.each(function(){
            var ltrspc;
            var txt = $(this).find('span');
            var aw = txt.width(); // actual text width
            var orig = aw;  // store original actual
            var dw = $(this).width(); // desired text width

            // if the difference is small enough, don't bother adjusting anything
            if (Math.abs(dw - aw) <= allowable_discrepancy) {
                return;
            }

            if (aw < dw) { // if actual width is less than desired
                // add 1px word-spacing first, if there is room
                if ((dw - aw) >= (txt.text().wordcount() - 1)) {
                    txt.css('word-spacing', '1px');
                    aw = txt.width(); // get new actual width
                }
                // if actual is still less than desired, adjust letter-spacing
                if (aw < dw) {
                    // difference in width divided by number of spaces between letters
                    ltrspc = (dw - aw) / (txt.text().length - 1);
                    txt.css('letter-spacing', ltrspc + 'px');
                    aw = txt.width(); // get new actual
                    // scale back if we overshot on the size
                    while (aw > dw) {
                        ltrspc -= 0.25;
                        txt.css('letter-spacing', ltrspc + 'px');
                        aw = txt.width(); // get new actual
                    }
                }

            } else {
                // decrease letter spacing
                // FIXME: this calculation seems way off, especially for short blocks
                ltrspc = - ((aw - dw) / (txt.text().length - 1));
                // don't go lower than the minimum letter-spacing threshold
                if (ltrspc < min_letterspace) { ltrspc = min_letterspace; }
                txt.css('letter-spacing', ltrspc + 'px');
                aw = txt.width(); // new actual
            }
            // console.log('text width: original=' + orig + ' desired= ' + dw + ' final=' + aw + ' (' + (dw-aw) + '), letter-spacing=' + ltrspc);
        });
    };
})(jQuery);

/**
jQuery plugin to allow for container relative font size, by scaling according
to the difference in the container and the viewport.

Main element is the container that font sizes should be relative to, and will
be used to adjust to viewport height.  Elements to be adjusted should be specified
in the plugin options (or use vhfont-resize class), and should have a
data-vhfontsize with the desired font size relative to the specified element.

Example use:

 $(".page img").relativeFontHeight({elements: $('.ocr-line')});

Set debug option to true to see output about what is being done.

*/
(function($) {
    // should it take the elements and then
    $.fn.relativeFontHeight = function(options) {
        var container = $(this);
        var settings = $.extend({
            // defaults
            elements: $(".vhfont-resize"),
            debug: false
        }, options);

        var scale = container.height() / $(window).height();
        // if window has resized but scale is unaffected, nothing to do
        if (scale == container.data('vhscale')) {
            if (settings.debug) {
                console.log('relative font size scale (' + scale +') is unchanged.');
            }
            return;
        }
        // store current scale to check against on next resize
        container.data('vhscale', scale);

        // update relative font size for configured elements
        settings.elements.each(function() {
            var el = $(this);
            // get % of container from data and scale based on parent / window
            if (settings.debug) {
                console.log('setting font size to ' + el.data('vhfontsize') * scale + 'vh');
            }
            el.css('font-size', el.data('vhFontSize') * scale + 'vh');
        });

    };
})(jQuery);


/* extend String with a few utility methods */
String.prototype.wordcount = function() {
    // count the number of words in a string by splitting on plain whitespace
    return this.split(' ').length;
};
// thanks to http://stackoverflow.com/questions/280634/endswith-in-javascript
String.prototype.endswith = function(str) {
    return this.length >= str.length && this.lastIndexOf(str) + str.length == this.length;
};
String.prototype.startswith = function(str) {
    return this.length >= str.length && this.lastIndexOf(str) === 0;
};


/** Django CSRF token handling for ajax put/post/delete requests.
Based on https://docs.djangoproject.com/en/1.7/ref/contrib/csrf/#ajax
*/
// NOTE: could use jquery cookie plugin instead of this method
// http://plugins.jquery.com/cookie/
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
// var csrftoken = getCookie('csrftoken');
var csrftoken = 'notrealcsrftoken';

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
function sameOrigin(url) {
    // test that a given url is a same-origin URL
    // url could be relative or scheme relative or absolute
    var host = document.location.host; // host + port
    var protocol = document.location.protocol;
    var sr_origin = '//' + host;
    var origin = protocol + sr_origin;
    // Allow absolute or scheme relative URLs to same origin
    return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
        (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
        // or any other URL that isn't scheme relative or absolute i.e relative.
        !(/^(\/\/|http:|https:).*/.test(url));
}
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
            // Send the token to same-origin, relative URLs only.
            // Send the token only if the method warrants CSRF protection
            // Using the CSRFToken value acquired earlier
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

