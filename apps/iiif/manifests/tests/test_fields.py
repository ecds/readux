"""
Test class for SafeEDTFField.

Covers the storage round-trip (base64 text surviving a real varchar
column, unlike the raw pickle bytes the upstream EDTFField hands
psycopg2) and the defensive read behavior for corrupted/legacy values,
since the whole point of this field is to never crash a page render
over a garbled date.
"""

import base64
import pickle

from django.db import connection
from django.test import TestCase
from edtf import parse_edtf

from apps.iiif.manifests.fields import SafeEDTFField
from apps.iiif.manifests.models import Manifest
from apps.iiif.manifests.tests.factories import ManifestFactory


class SafeEDTFFieldStorageTest(TestCase):
    """Round-trip through an actual save/reload against the real DB column."""

    def test_round_trip_through_save_and_reload(self):
        manifest = ManifestFactory.create(published_date_edtf="1898")
        manifest.save()
        reloaded = Manifest.objects.get(pk=manifest.pk)
        assert reloaded.date_edtf is not None
        assert str(reloaded.date_edtf) == str(parse_edtf("1898"))

    def test_stored_value_is_base64_text_not_raw_bytes(self):
        """The actual column should hold plain ASCII base64 text -- this is
        the thing that broke under the upstream EDTFField, since handing
        psycopg2 raw pickle bytes for a varchar column gets silently
        mangled by Postgres's bytea->varchar cast."""
        manifest = ManifestFactory.create(published_date_edtf="1898")
        manifest.save()
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT date_edtf FROM manifests_manifest WHERE pid = %s",
                [manifest.pid],
            )
            raw_value = cursor.fetchone()[0]
        assert isinstance(raw_value, str)
        decoded = pickle.loads(
            base64.b64decode(raw_value.encode("ascii"), validate=True)
        )
        assert str(decoded) == str(parse_edtf("1898"))

    def test_self_heal_recovers_from_corrupted_legacy_value(self):
        """A manifest whose date_edtf column holds old-style corrupted text
        (the hex-text bytea rendering that caused the production incident
        this field was written to fix) must not crash on load, and should
        still show the correct date via the self-heal from
        published_date_edtf."""
        manifest = ManifestFactory.create(published_date_edtf="1898")
        manifest.save()
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE manifests_manifest SET date_edtf = %s WHERE pid = %s",
                ["\\x8004954f00000000000000008c1a656474662e", manifest.pid],
            )
        reloaded = Manifest.objects.get(pk=manifest.pk)  # must not raise
        assert str(reloaded.date_edtf) == str(parse_edtf("1898"))


class SafeEDTFFieldUnitTest(TestCase):
    """Exercises the field's methods directly, independent of a real save."""

    def setUp(self):
        self.field = SafeEDTFField()

    def test_from_db_value_returns_none_for_empty(self):
        assert self.field.from_db_value(None, None, None) is None
        assert self.field.from_db_value("", None, None) is None

    def test_from_db_value_returns_none_for_corrupted_legacy_text(self):
        assert (
            self.field.from_db_value(
                "\\x8004954f00000000000000008c1a656474662e", None, None
            )
            is None
        )

    def test_from_db_value_round_trips_base64_pickle(self):
        edtf_obj = parse_edtf("1898")
        encoded = base64.b64encode(pickle.dumps(edtf_obj)).decode("ascii")
        result = self.field.from_db_value(encoded, None, None)
        assert str(result) == str(edtf_obj)

    def test_from_db_value_handles_real_bytes_defensively(self):
        edtf_obj = parse_edtf("1898")
        raw_pickle = pickle.dumps(edtf_obj)
        result = self.field.from_db_value(raw_pickle, None, None)
        assert str(result) == str(edtf_obj)

    def test_from_db_value_returns_none_for_garbage_bytes(self):
        assert self.field.from_db_value(b"not a pickle", None, None) is None

    def test_get_db_prep_save_returns_base64_text_for_edtf_object(self):
        edtf_obj = parse_edtf("1898")
        prepped = self.field.get_db_prep_save(edtf_obj, connection)
        assert isinstance(prepped, str)
        decoded = pickle.loads(base64.b64decode(prepped.encode("ascii"), validate=True))
        assert str(decoded) == str(edtf_obj)

    def test_get_db_prep_save_passthrough_for_falsy_value(self):
        assert self.field.get_db_prep_save(None, connection) is None

    def test_get_prep_value_base64_encodes_edtf_object(self):
        edtf_obj = parse_edtf("1898")
        prepped = self.field.get_prep_value(edtf_obj)
        assert isinstance(prepped, str)
        decoded = pickle.loads(base64.b64decode(prepped.encode("ascii"), validate=True))
        assert str(decoded) == str(edtf_obj)

    def test_get_prep_value_passthrough_for_non_edtf_object(self):
        assert self.field.get_prep_value(None) is None
