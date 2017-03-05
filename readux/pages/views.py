# feincms.views.cbv has been removed. Use feincms.urls and feincms.views directly instead.
# https://github.com/feincms/feincms/blob/776f569e53b6af445dd9194ce6cd05b14cf5a218/docs/releases/1.12.rst

from feincms.views import Handler


class SiteIndex(Handler):
    # extend default feincms view handler so it can be bound to the
    # index url and referenced as a named route

    def get_context_data(self, **kwargs):
        ctxt_data = super(SiteIndex, self).get_context_data()
        lead = self.object.content.lead
        # if lead content is present, pass in to the template
        # as a tagline or description for embedded metadata
        if lead:
            ctxt_data.update({
                'tagline': self.object.content.lead[0].render()
            })
        return ctxt_data
