from django.views.decorators.vary import vary_on_cookie

class VaryOnCookieMixin(object):
    @classmethod
    def as_view(cls, **initkwargs):
        view = super(VaryOnCookieMixin, cls).as_view(**initkwargs)
        return vary_on_cookie(view)
