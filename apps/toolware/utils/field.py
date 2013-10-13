from django.db import models



class EmailFieldLowerCase(models.EmailField):
    """Case-Insensitive Email (lower case)"""

    def get_prep_value(self, value):
        prep_value = super(EmailFieldLowerCase, self).get_prep_value(value)
        if prep_value:
            prep_value = prep_value.lower()
        return prep_value