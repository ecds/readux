from feincms.module.page.models import Page

def default_page(request):
    # always include a default feincms page, so we can retrieve
    # top-level navigation
    return {
        'feincms_page': Page.objects.in_navigation().first()
    }
