from collections import OrderedDict
from django.template import Library

register = Library()


@register.filter
def has_inner_hits(volume):
    """Template filter to determine if there are any inner hits across the volume"""
    inner_hits = volume.meta.inner_hits
    for key in inner_hits.to_dict().keys():
        if inner_hits[key].hits.total.value:
            return True
    return False


@register.filter
def group_by_canvas(inner_hits):
    """Template filter to group inner hits by canvas #, then flatten into list"""
    hits_dict = inner_hits.to_dict()
    # dict keyed on canvas
    canvases = {}
    for key in hits_dict.keys():
        for canvas in hits_dict[key]:
            if not canvas.position in canvases:
                # only need to get some info once per canvas (position, pid)
                canvases[canvas.position] = {
                    "pid": canvas.pid,
                    "position": canvas.position,
                    "highlights": [],
                    "search_terms": [key],
                }
            else:
                # keep track of search term for exact match queries
                canvases[canvas.position]["search_terms"] += [key]
            # collect highlights per canvas
            if canvas.meta and canvas.meta.highlight:
                for result in canvas.meta.highlight["canvas_set.result"]:
                    canvases[canvas.position]["highlights"].append(result)

    # flatten values into list for display
    grouped = []
    for canvas in canvases.values():
        # result should generally be of length 3 or less, but if there are multiple exact queries
        # in this search, ensure at least one highlighted page per exact query (i.e. if none of the
        # search terms matched on this page are matched on any of the pages we've selected for
        # display, ensure this page gets displayed too)
        if len(grouped) < 3 or not any(
            [
                set(c["search_terms"]).intersection(canvas["search_terms"])
                for c in grouped
            ]
        ):
            grouped.append(canvas)
    return grouped
