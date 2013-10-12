from django.core.urlresolvers import reverse

def build_menu(request, menu):
    """Given a menu dict, return a menu list"""
    
    loggedin = request.user.is_authenticated()
    items = [menu[key] for key in sorted(menu.iterkeys())]

    best_match_url = ''
    new_menu = []
    for item in items:
        if item['pre_login_visible'] and item['post_login_visible']:
            pass # show whether or not the user is logged in
        elif item['post_login_visible'] and loggedin:
            pass # show only when user logs in
        elif item['pre_login_visible'] and not loggedin:
            pass # show only when user is not logged in
        else:
            continue # not to be shown at this time
        if item['superuser_required'] and not request.user.is_superuser:
            continue # not a superuser, don't show
        if item['staff_required'] and not request.user.is_staff:
            continue # not a staff, don't show
        try:
            item['url'] = reverse(item['reversible'])
        except:
            item['url'] = item['reversible']

        # record the based matched url on the requested path
        if len(item['url']) > 1 and item['url'] in request.path:
            if len(best_match_url) < len(item['url']):
                best_match_url = item['url']

        new_menu.append(item)

    # mark the best match url as selected
    matched_index = -1
    for item in new_menu:
        if best_match_url == item['url']:
            matched_index = new_menu.index(item)
            break
    if matched_index > -1:
        new_menu[matched_index]['selected'] = True
    
    return new_menu



