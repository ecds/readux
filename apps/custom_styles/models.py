"""Model manage custom style."""
from django.db import models

class Style(models.Model):
    """Model to hold style values for customization."""
    primary_color = models.CharField(
        max_length=50,
        blank=False,
        null=False,
        help_text="Bold color to be used for links and navigation."
    )
    active = models.BooleanField(default=False)

    @property
    def css(self):
        """Represent style as CSS

        :return: Style tag
        :rtype: str
        """
        tag = """:root {{
                .primary-color: {p};
              }}"""

        return tag.format(
            p=self.primary_color
        ).replace('\n', '').replace(' ', '')

    def save(self, *args, **kwargs):
        """
        Override save to ensure only one objects is the active one.
        """
        if self.active:
            active_style = Style.objects.get(active=True)
            if self != active_style:
                active_style.active = False
                active_style.save()
        if Style.objects.all().count() == 0:
            self.active = True

        super(Style, self).save(*args, **kwargs)

    def __str__(self):
        return 'Style - {id}'.format(id=self.pk)
