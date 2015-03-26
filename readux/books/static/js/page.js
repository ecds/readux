/**
jQuery plugin to adjust the width of a portion of text.  Expects a
block element, with the desired width set, and an inner span element
with the text that should be adjusted.  Uses CSS word-spacing and
letter-spacing to adjust the actual width to the desired width.
*/
(function($) {
    $.fn.textwidth = function() {
        // minimum allowed letterspacing
        var min_letterspace = 0.5;
        // actual vs desired size small enough to ignore
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
                ltrspc = (aw - dw) / (txt.text().length - 1);
                if (ltrspc < min_letterspace) { ltrspc = min_letterspace; }
                txt.css('letter-spacing', '-' + ltrspc + 'px');
                aw = txt.width(); // new actual
            }
            // console.log('text width: original=' + orig + ' desired= ' + dw + ' final=' + aw + ' (' + (dw-aw) + '), letter-spacing=' + ltrspc);
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

