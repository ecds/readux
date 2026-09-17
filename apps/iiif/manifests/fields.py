"""Local patch for python-edtf's EDTFField.

EDTFField (from the third-party `edtf` package) pickles EDTFObject
instances to raw bytes for storage, but it's built on top of
models.CharField -- a varchar column, not bytea. Handing psycopg2 raw
Python bytes for a varchar column triggers an implicit bytea->varchar
cast in Postgres, which renders the bytes through bytea_output (hex by
default) instead of storing them as-is. What actually lands in the
column is the *text* representation of the bytes (e.g. "\\x8004..."),
which can never be unpickled back (a varchar column always returns
str, and pickle.loads requires a real bytes-like object), and letting
EDTFField's text-parsing fallback run against that garbage can hang
for pathological input (see the production incidents this patch is
responding to).

SafeEDTFField base64-encodes the pickled value before writing, so
what's stored is plain ASCII text that survives an ordinary varchar
round-trip intact, and from_db_value never lets a parse failure
propagate or fall through to the slow natural-language parser fallback
on garbage input.
"""

import base64
import pickle

from edtf import EDTFObject
from edtf.fields import EDTFField


class SafeEDTFField(EDTFField):
    """EDTFField that stores its pickled value as base64 text."""

    def from_db_value(self, value, expression, connection):
        if not value:
            return None

        if isinstance(value, (bytes, memoryview)):
            # Defensive: only ever expected for pre-patch rows if the
            # column type is ever changed to real bytea.
            try:
                return pickle.loads(bytes(value))
            except Exception:  # pylint: disable=broad-except
                return None

        try:
            raw = base64.b64decode(value.encode("ascii"), validate=True)
            return pickle.loads(raw)
        except Exception:  # pylint: disable=broad-except
            # Not one of our base64-encoded values -- most likely a
            # leftover pre-patch row (corrupted hex-text) or a value
            # written directly via SQL. Don't try the natural-language
            # parser here: on some malformed input it can pathologically
            # backtrack and hang the request instead of failing fast.
            # EDTFFieldDescriptor's update_values() will re-derive the
            # correct value from published_date_edtf on load anyway.
            return None

    def get_db_prep_save(self, value, connection):
        if value:
            return base64.b64encode(pickle.dumps(value)).decode("ascii")
        return super().get_db_prep_save(value, connection)

    def get_prep_value(self, value):
        if isinstance(value, EDTFObject):
            return base64.b64encode(pickle.dumps(value)).decode("ascii")
        return super().get_prep_value(value)
