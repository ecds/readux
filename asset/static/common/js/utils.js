// __author__ = 'Val Neekman [neekware.com]'


$(document).ready(function(){

    jQuery.fn.hasAttr = function(name) {  
       return this.attr(name) !== undefined;
    };

    String.prototype.contains = function(sub_str) {
        return this.indexOf(sub_str) != -1; 
    };

    // checkbox simulation
    ///////////////////////////////////////
    $(".checkbox.toggle").on('hover', function(){
        if($(this).hasClass('disabled')){
            return
        }
        if($(this).children('i').hasClass('icon-check')){
            $(this).children('i').removeClass('icon-check').addClass('icon-check-empty');
        }
        else if($(this).children('i').hasClass('icon-check-empty')){
            $(this).children('i').removeClass('icon-check-empty').addClass('icon-check');
        }
    });

    // background flasher
    ///////////////////////////////////////
    jQuery.fn.backgroundFlashFade = function(timeout, flash_color, orig_color) {
        if (!is_valid(orig_color)) {
            var orig_color = this.css('backgroundColor');
        }
        if (!is_valid(flash_color)) {
            var flash_color = 'yellow';
        }
        if (!is_valid(timeout)) {
            var timeout = 500;
        }
        return this.css({
            'backgroundColor': flash_color
        }).animate({
            'backgroundColor': orig_color
        }, timeout);
    };

    // text flasher
    //////////////////////////////////////
    jQuery.fn.textFlashFade = function(timeout, flash_color, orig_color) {
        if (!is_valid(orig_color)) {
            var orig_color = this.css('color');
        }
        if (!is_valid(flash_color)) {
            var flash_color = 'yellow';
        }
        if (!is_valid(timeout)) {
            var timeout = 700;
        }
        return this.css({
            'color': flash_color
        }).animate({
            'color': orig_color
        }, timeout);
    };

});

// Trac toggler
///////////////////////////////////////
function trac_document_load(){
    $(document).ready(function(){
        var me = $('.trac_initial_load');
        if (me.attr('trac-state') == 'TICK_INIT'){
            me.trigger('click');
        }
    });
}
function trac_document_bind(){
    $(document).on('click', 'a', function () {
        var me = $(this);
        if (!me.hasAttr('trac-type')){ return; }
        trac_elment_toggler(me);
        return false;
    });
}
function trac_update_fields(element, parent_li, data, result){
    element.attr('trac-state', result['state']);
    if (result['state'] == 'TICK_OFF'){
        element.find('i').removeClass('icon-check').addClass('icon-check-empty');
    }else if (result['state'] == 'TICK_ON'){
        element.find('i').removeClass('icon-check-empty').addClass('icon-check');
    }
    var me = null;
    if (result['trac_stats_tracked_obj']){
        stats = result['trac_stats_tracked_obj'];
        for (trac_type in stats){
            if (stats[trac_type] != '-1'){
                me = $('#trac li .tracked#'+trac_type);
                if (me && me.html() != stats[trac_type]){
                    me.html(stats[trac_type]).textFlashFade(timeout=500, flash_color='brown');
                }
            }
        }
    }
    if (result['trac_stats_tracker_obj']){
        stats = result['trac_stats_tracker_obj'];
        for (trac_type in stats){
            if (stats[trac_type] != '-1'){
                me = $('#trac li .tracker#'+trac_type);
                if (me && me.html() != stats[trac_type]){
                    me.html(stats[trac_type]).textFlashFade(timeout=500, flash_color='brown');
                }
            }
        }
    }
    show_empty_list_message(parent_li);
}
function trac_elment_toggler(element){
    if (!element.hasAttr('trac-type')){ return; }
    var url = element.attr('href');
    var postdata = {
        'trac-oid': element.attr('trac-oid'),
        'trac-app': element.attr('trac-app'),
        'trac-type': element.attr('trac-type'),
        'trac-class': element.attr('trac-class'),
        'trac-state': element.attr('trac-state'),
        'csrfmiddlewaretoken': $('form#csrf_post_form input').val(),
    }
    var parent_li = element.closest("li");
    parent_li.find('.status_ajax_loader').show();
    $.ajax({
        url: url,
        type: 'POST',
        timeout: 5000,
        data: postdata,
        dataType: 'json',
        success: function(result) {
            trac_update_fields(element, parent_li, postdata, result);
        },
        error: function(result) {
            // alert_message('warning', 'Operation Failed.');
        },
        complete: function(result) {
        }
    });
}

// Popover Hide on Click
///////////////////////////////////////
function enable_popover_view(){
    // use [rel*=popover] instead of [rel=popover] so linkes with nofollow work
    $('[rel*=popover]').popover({'html': true}).click(function(e) {
        $(this).popover('hide');
    });
}

// Modal Ajax
///////////////////////////////////////
function enable_modal_view(){
    $("a[data-toggle=modal]").on('click', function() {
        var me = $(this);
        var url = me.attr('href');
        csrf = $('form#csrf_post_form input').val();
        var postdata = {csrfmiddlewaretoken: csrf };
        $.ajax({
            url: url,
            type: 'POST',
            timeout: 5000,
            data: postdata,
            dataType: 'json',
            success: function(result) {
                $('#empty_modal_box').html(result['modal']);
                $('#empty_modal_box').addClass('fade in').modal('show');
            },
            error: function(result) {
                alert_message('warning', 'Operation Failed.')
            },
            complete: function(result) {
            }
        });
        return false;
    });
}

// Infinite Scroll -- Member Search List
/////////////////////////////////////////
function enable_infinite_scroll(){
    if (!_member_search_list_ajax_url){
        _infinite_scroll = false;
    } else {
        _infinite_scroll = true;
    }
}
function push_state_sync(result){
    window.history.pushState('', '', result['curr_url']);
}
function append_members_info(result){
    $(_member_list_ul).append(result['result']);
    $(_member_list_prev_next).html(result['prev_next']);
    _member_search_list_ajax_url = result['next_url'];
    $(_infinite_scroll_ajax_loader).hide();
    push_state_sync(result);
}
function get_member_list_view_next_page() {
    var url = _member_search_list_ajax_url;
    var postdata = $(_element_id_list_search_form).serialize();
    $.ajax({
        url: url,
        type: 'POST',
        timeout: 5000,
        data: postdata,
        dataType: 'json',
        success: function(result) {
            append_members_info(result);
        },
        error: function(result) {
            alert_message('warning', 'Operation Failed.');
        },
        complete: function(result) {
            $(_infinite_scroll_ajax_loader).hide();
            window.setTimeout(function() { enable_infinite_scroll() }, 500);
        }
    });
    return false;
}
function infinite_list_view_scroll(){
    $(document).ready(function(){
        $(window).scroll(function(e) {
            if (_infinite_scroll){
                var wintop = $(window).scrollTop();
                var docheight = $(document).height();
                var winheight = $(window).height();
                var scrolltrigger = 0.60;
                if  ((wintop/(docheight-winheight)) > scrolltrigger) {
                    _infinite_scroll = false;
                    $(_infinite_scroll_ajax_loader).show('fast');
                    get_member_list_view_next_page();
                }
            }
        });
    });
}

// highlights needle in haystack
/////////////////////////////////////////
function highlighter(needle, haystack, highlightKlass) {
    pattern = new RegExp('(.*?)(' + needle + ')(.*?)','ig');
    if (highlightKlass) {
        replaceWith = '$1<span class="' + highlightKlass + '">$2</span>$3';
    } else {
        replaceWith = '$1<strong>$2</strong>$3';
    }
    highlighted = haystack.replace(pattern, replaceWith);
    return highlighted;
}

// geo, compares  strings
/////////////////////////////////////////
function geo_compare_fuction(a,b) {
    a = (a.name + (a.adminName1 ? ", " + a.adminName1 : "") + ", " + a.countryName).toLowerCase();
    b = (b.name + (b.adminName1 ? ", " + b.adminName1 : "") + ", " + b.countryName).toLowerCase();
    return a == b ? 0 : (a < b ? -1 : 1);
}

// remove duplicate elements in an array
/////////////////////////////////////////
function unique_array(a, compFunc){
    var isCompFunc = false;
    if(typeof compFunc !== "undefined"){
        isCompFunc = true;
        a.sort( compFunc );
    }
    for(var i = 1; i < a.length; ){
        if( (isCompFunc && compFunc(a[i-1], a[i]) === 0) || a[i-1] == a[i]){
            a.splice(i, 1);
        } else {
            i++;
        }
    }
    return a;
}

// if variable is set
/////////////////////////////////////////
function is_valid(value){
    return (value && (typeof value !== 'undefined') && 
            value != '' && value != 'None'&&
            value.toString() != '0.0' && value.toString() != '0');
}
