import re
from html import unescape
from django.template import Library

register = Library()


@register.filter
def dict_item(dictionary, key):
    """'Template filter to allow accessing dictionary value by variable key.
    Example use::

        {{ mydict|dict_item:keyvar }}
    """
    # adapted from Princeton-CDH/geniza project https://github.com/Princeton-CDH/geniza/
    try:
        return dictionary[key]
    except AttributeError:
        # fail silently if something other than a dict is passed
        return None


@register.filter
def attr(obj, attr_name):
    """Safely access an attribute on an object without raising if missing."""
    try:
        return getattr(obj, attr_name)
    except AttributeError:
        return None


@register.filter
def manifest_year(volume):
    """Return a 4-digit published year from a manifest or hit object."""
    # try standard published_date first
    published = getattr(volume, "published_date", None)
    if published:
        # handle datetime/date objects with a year attribute
        year = getattr(published, "year", None)
        if year:
            return f"{int(year):04d}"
        # fall back to parsing string content
        match = re.search(r"\d{4}", str(published))
        if match:
            return match.group(0)
        return str(published)[:4]

    # fall back to elasticsearch stored string (may be missing on some hits)
    edtf = getattr(volume, "published_date_edtf", None)
    if edtf:
        match = re.search(r"\d{4}", str(edtf))
        if match:
            return match.group(0)
        return str(edtf)[:4]

    return ""


@register.filter
def has_inner_hits(volume):
    """Template filter to determine if there are any inner hits across the volume"""
    try:
        inner_hits = volume.meta.inner_hits
        for key in inner_hits.to_dict().keys():
            if inner_hits[key].hits.total.value:
                return True
    except AttributeError:
        pass
    return False


@register.filter
def group_by_canvas(inner_hits, limit=3):
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
        # result should generally be of length "limit" or less, but if there are multiple exact
        # queries in this search, ensure at least one highlighted page per exact query (i.e. if
        # none of the search terms matched on this page are matched on any of the pages we've
        # selected for display, ensure this page gets displayed too)
        if len(grouped) < limit or not any(
            [
                set(c["search_terms"]).intersection(canvas["search_terms"])
                for c in grouped
            ]
        ):
            grouped.append(canvas)
    return grouped


@register.filter
def get_headers(block_list):
    # filter to get just the headers in a wagtail page, in order to render a table of contents
    return list(filter(lambda b: b.value and b.block_type == "heading_block", block_list))


@register.filter
def vimeo_embed_url(vimeo_url):
    # get the embed url from a vimeo link
    # i.e. https://vimeo.com/76979871 --> https://player.vimeo.com/video/76979871
    return re.sub(r"vimeo\.com\/(\d+)", r"player.vimeo.com/video/\1", vimeo_url)


@register.filter
def spaced_semicolons(value):
    """Ensure a single space follows each semicolon in a metadata string."""
    try:
        return re.sub(r";\s*", "; ", str(value))
    except TypeError:
        return value


@register.filter
def unescape_html(value):
    """Decode HTML entities to their corresponding characters."""
    try:
        return unescape(str(value))
    except Exception:
        return value


@register.filter
def metadata_items(value):
    """Normalize collection metadata for template display."""
    if not value:
        return []

    if isinstance(value, list):
        items = []
        for entry in value:
            if isinstance(entry, dict):
                label = entry.get("label", "")
                content = entry.get("value", "")
                items.append((label, content))
        return items

    if isinstance(value, dict):
        return list(value.items())

    return []


@register.filter
def strip_trailing_commas(value):
    """Remove any trailing commas and surrounding whitespace."""
    try:
        return re.sub(r",\s*$", "", str(value))
    except TypeError:
        return value
