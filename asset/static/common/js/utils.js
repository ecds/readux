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

    // get to post converter
    ///////////////////////////////////////
    $(document).on('click', 'a', function () {
        var me = $(this);
        if (!me.hasClass('get2post')){
            return;
        }
        var parent_li = me.closest("li");
        parent_li.find('.status_ajax_loader').show();
        var url = me.attr('href');
        if (me.hasClass('confirm')){
            if(!window.confirm("Are you sure?")){
                parent_li.find('.status_ajax_loader').hide();
                return false;
            }
        }
        if (me.hasClass('deletion')){
            csrf = $('form#csrf_post_form input').val();
            var postdata = {csrfmiddlewaretoken: csrf };
            $.ajax({
                url: url,
                type: 'POST',
                timeout: 5000,
                data: postdata,
                dataType: 'json',
                success: function(result) {
                    show_empty_list_message(parent_li);
                },
                error: function(result) {
                    alert_message('warning', 'Operation Failed.');
                },
                complete: function(result) {
                }
            });
            return false;
        }
        
        $('form#csrf_post_form').attr('action', url).submit();
        return false;
    });

    // Alert Warning
    //////////////////////////////////////////
    $("#message_box .alert_success").delay(2).fadeTo(9000, 0)
    $("#message_box .alert_warning").delay(2).fadeTo(18000, 0)
    $("#message_box .alert_error").delay(2).fadeTo(28000, 0)

    // Page title inserter for contact form
    /////////////////////////////////////////
    $('a.send_page_title').click(function () {
        var current_title = $(document).attr('title');
        var link = $(this).attr("href") + "?page_title=" + encodeURI(current_title);
        document.location = link;
        return false;
    });

    // Popover related
    /////////////////////////////////////////
    function enable_popover_elements(){
        // use [rel*=popover] instead of [rel=popover] so linkes with nofollow work
        $('[rel*=popover]').popover({ html : true });
    }
    enable_popover_elements();

    // Status related
    //////////////////////////////////////////
    // $("a").click(function(){
    //     $('i.icon-cog').addClass('icon-spin');
    // });

    // Tooltip related
    /////////////////////////////////////////
    function enable_tooltip_elements(){
        // use [rel*=tooltip] instead of [rel=tooltip] so linkes with nofollow work
        $('body').tooltip({
            selector: '[rel*=tooltip]'
        });
    }
    enable_tooltip_elements();

    // Tooltip related
    /////////////////////////////////////////
    $('a.login_required_or_signup').click(function () {
        $(this).hide();
        $(this).html('please login to use this feature');
        $(this).fadeIn(2000);
        $(this).unbind('click');
        $(this).removeClass('login_required_or_signup');
        return false;
    });

    // trac utils
    trac_document_bind();
    trac_document_load();

    align_checkbox();
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

// show empty message when last element of
// a is removed
/////////////////////////////////////////
function show_empty_list_message(li_element){
    var parent_ul = li_element.closest("ul");
    if (!parent_ul.hasAttr('writable-ul')){
        return
    }
    var fixed_li_num = parent_ul.attr('fixed-li-num');
    if (!fixed_li_num) fixed_li_num = 1;
    li_element.hide('slow', function () {
        $(this).remove();
    });
    if (li_element.siblings().length == fixed_li_num){
        li_element.siblings('.information_list_element')
                 .hide()
                 .removeClass('hidden_element')
                 .show('slow');
    }
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

function alert_message(type, msg_text){
    msg_text = typeof msg_text !== 'undefined' ? msg_text : 'Operation Failed.';
    var msg_box = $('#message_box');
    msg_html = '<div class="alert_'+type+'">'+
          '<button type="button" class="close" data-dismiss="alert">×</button>'+
          '» '+msg_text+' « </div>'
    msg_box.html(msg_html).show('slow');
}

// expert list view stuff
/////////////////////////////////////////
function list_view_utils(){
    $('.errorlist').hide();

    var ccode = $("#id_country option:selected").val();
    if (!(ccode && (typeof ccode !== 'undefined') && ccode != '')){
        $("#id_country").val('{{request|geo_country_code}}');
    }

    $("#id_country").attr('data-placeholder', "Choose a country");
    $("#id_country").chosen();
    var code = $("#id_country option:selected").val()
    var image = "url('" + common_asset_base_url + 'images/flags/' + code.toLowerCase() + "_16.png') no-repeat 0px center";
    $('#id_country_chzn a.chzn-single span').css('background', image);
    $('#id_country_chzn a.chzn-single span').css('padding-left', "20px");
    // console.log($('#id_country_chzn a.chzn-single span').text());

    // $('#id_country_chzn li#id_country_chzn_o_0').remove();
    $('#id_country_chzn ul li.active-result').each(function(){
        var name = $(this).text();
        var code = $('#id_country option:contains(' + name + ')').val();
        if (name.indexOf('---') < 0){
            var image = "url('" + common_asset_base_url + 'images/flags/' + code.toLowerCase() + "_16.png') no-repeat 4px center";
            $(this).css('background', image);
            $(this).css('padding-left', "24px");
        }
    });

    $(document).on("click", '#id_country_chzn ul li.active-result', function(){
        var name = $('#id_country_chzn a.chzn-single span').text();
        var code = $('#id_country option:contains(' + name + ')').val();
        if (name.indexOf('---') < 0){
            var image = "url('" + common_asset_base_url + 'images/flags/' + code.toLowerCase() + "_16.png') no-repeat 0 center";
            $('#id_country_chzn a.chzn-single span').css('background', image);
            $('#id_country_chzn a.chzn-single span').css('padding-left', "20px");
            $('#id_country').closest("form").submit();
            // console.log($('#id_country_chzn a.chzn-single span').text());
        }
    });

    function change_chzn_single_image(){
        var name = $('#id_country_chzn a.chzn-single span').text();
        var code = $('#id_country option:contains(' + name + ')').val();
        if (name.indexOf('---') < 0){
            var image = "url('" + common_asset_base_url + 'images/flags/' + code.toLowerCase() + "_16.png') no-repeat 0 center";
            $('#id_country_chzn a.chzn-single span').css('background', image);
            $('#id_country_chzn a.chzn-single span').css('padding-left', "20px");
            $('#id_country').closest("form").submit();
            // console.log($('#id_country_chzn a.chzn-single span').text());
        }
    }

    $(document).on("keydown", 'div.chzn-search input', function(e){
        var keyCode = e.keyCode || e.which;
        if (keyCode == 9 || keyCode == 13) {
            window.setTimeout(function() {
                change_chzn_single_image();
            }, 85);
        }
    });

    $(document).on("click", '#id_map_view_button', function(e){
        $('#id_map_view_ajax_wheel').show();
    });

    $(document).on("click", '#search_reset_link', function(e){
        $('#submit_button_ajax_loader').show();
    });

    $(document).on("click", '#form_search_list input[type=submit]', function(e){
        $('#submit_button_ajax_loader').show();
    });

    $(document).on("click", '.clickable_tags a', function(e){
        $('#submit_button_ajax_loader').show();
        var me = $(this);
        var tag = me.attr('tag-data');
        if (tag.contains(' ')){
            tag = '"'+tag+'"'
        }
        var keyword_field = $('#form_search_list input[id=id_keywords]');
        keyword_field.val(tag);
        $('#form_search_list').submit();
    });

    $('#id_country_chzn').width(199);
    $('#id_country_chzn .chzn-drop').width(197);
    $('#id_country_chzn .chzn-search input').width(163);
    
    // sort by
    $("#id_sort_by").chosen();
    $("#id_sort_by_chzn .chzn-search").hide();
    $('#id_sort_by_chzn').width(199);
    $('#id_sort_by_chzn .chzn-drop').width(197);
    $(document).on("click", '#id_sort_by_chzn ul li.active-result', function(){
        $('#id_sort_by').closest("form").submit();
    });
}

// Social Profiles
////////////////////////////////////////
function social_profile_utils(){
    $("#id_provider").attr('data-placeholder', "Choose a social network");
    var selected = $("#id_provider option:selected").val()
    if (!selected) {
        $("#id_provider option:selected").attr('selected', false).text('');
        $("#id_provider").chosen();
    } else {
        $("#id_provider").chosen();
        var name = $("#id_provider option:selected").text()
        var image = "url('" + common_asset_base_url + 'images/social/' + name.toLowerCase() + "_16.png') no-repeat 4px center";
        $('#id_provider_chzn a.chzn-single span').css('background', image);
        $('#id_provider_chzn a.chzn-single span').css('padding-left', "24px");
        // console.log($('#id_provider_chzn a.chzn-single span').text());
    }

    $('#id_provider_chzn li#id_provider_chzn_o_0').remove();
    $('#id_provider_chzn ul li.active-result').each(function(){
        var name = $(this).text();
        if (name.indexOf('---') < 0){
            var image = "url('" + common_asset_base_url + 'images/social/' + name.toLowerCase() + "_16.png') no-repeat 4px center";
            $(this).css('background', image);
            $(this).css('padding-left', "24px");
        }
    });

    $(document).on("click", '#id_provider_chzn ul li.active-result', function(){
        var name = $('#id_provider_chzn a.chzn-single span').text();
        if (name.indexOf('---') < 0){
            var image = "url('" + common_asset_base_url + 'images/social/' + name.toLowerCase() + "_16.png') no-repeat 0 center";
            $('#id_provider_chzn a.chzn-single span').css('background', image);
            $('#id_provider_chzn a.chzn-single span').css('padding-left', "20px");
            // console.log($('#id_provider_chzn a.chzn-single span').text());
        }
    });

    function change_chzn_single_image(){
        var name = $('#id_provider_chzn a.chzn-single span').text();
        if (name.indexOf('---') < 0){
            var image = "url('" + common_asset_base_url + 'images/social/' + name.toLowerCase() + "_16.png') no-repeat 0 center";
            $('#id_provider_chzn a.chzn-single span').css('background', image);
            $('#id_provider_chzn a.chzn-single span').css('padding-left', "20px");
            // console.log($('#id_provider_chzn a.chzn-single span').text());
        }
    }

    $(document).on("keydown", 'div.chzn-search input', function(e){
        var keyCode = e.keyCode || e.which;
        if (keyCode == 9 || keyCode == 13) {
            window.setTimeout(function() {
                change_chzn_single_image();
            }, 85);
        }
    });
}

// Body (css rework)
////////////////////////////////////////
function set_main_page_css(){
    $('body').css('background', '#f8f8f8');
    $('body').css('font-family', 'Georgia,Hoefler,"Hoefler Text",Times,"Times New Roman",serif;');
    $('#bd_container_box').css('background', '#f8f8f8');
    $('#bd_container_box').css('font-family', 'Georgia,Hoefler,"Hoefler Text",Times,"Times New Roman",serif;');
}

// Checkbox (css rework)
////////////////////////////////////////
function align_checkbox(){
    $('[type=checkbox]').each(function(){
        var me = $(this);
        me.addClass('raw_checkbox');
        var parent = me.parents('p')
        var label = parent.find('label');
        label.addClass('pull-left');
    });
}

// Sign up page
////////////////////////////////////////
function signup_status(){
    $(document).on("click", '#singup_view_ajax_wheel', function(e){
        $('.status_ajax_loader').show();
    });
}



