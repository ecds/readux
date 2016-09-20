from feincms.views.cbv.views import Handler


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
