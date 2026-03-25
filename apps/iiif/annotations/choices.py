 # pylint: disable=invalid-name
from django.db.models import TextChoices

class AnnotationSelector(TextChoices):
    FragmentSelector = 'FR'
    CssSelector = 'CS'
    XPathSelector = 'XP'
    TextQuoteSelector = 'TQ'
    TextPositionSelector = 'TP'
    DataPositionSelector = 'DP'
    SvgSelector = 'SV'
    RangeSelector = 'RG'

class AnnotationPurpose(TextChoices):
    assessing = 'AS'
    bookmarking = 'BM'
    classifying = 'CL'
    commenting = 'CM'
    describing = 'DS'
    editing = 'ED'
    highlighting = 'HL'
    identifying = 'ID'
    linking = 'LK'
    moderating = 'MO'
    painting = 'PT'
    questioning = 'QT'
    replying = 'RE'
    supplementing = 'SP'
    tagging = 'TG'
