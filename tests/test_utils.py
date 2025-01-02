#!/usr/bin/env python

"""Tests for `access_ipy_telemetry` package."""

from access_ipy_telemetry.api import SessionID, ApiHandler
from access_ipy_telemetry.registry import TelemetryRegister
from pydantic import ValidationError
import pytest


def test_session_id_singleton():
    """
    Check that the SessionID class is a lazily evaluated singleton.
    """
    id1 = SessionID()
    id2 = SessionID()

    assert id1 is id2

    assert type(id1) is str

    assert len(id1) == 64

    assert id1 != SessionID.create_session_id()


def test_api_handler():
    """
    Check that the APIHandler class is a singleton.
    """
    session1 = ApiHandler()
    session2 = ApiHandler()

    assert session1 is session2

    DEFAULT_URL = "https://tracking-services-d6c2fd311c12.herokuapp.com"
    LOCALHOST = "http://localhost:8000"

    # Check defaults haven't changed unintentionally
    assert session1.server_url == DEFAULT_URL

    # Change the server url
    session1.server_url = LOCALHOST
    assert session2.server_url == LOCALHOST

    # Change the extra fields - first
    with pytest.raises(ValidationError):
        session1.extra_fields = {"catalog_version": "1.0"}

    session1.extra_fields = {"catalog": {"version": "1.0"}}

    assert session2.extra_fields == {"catalog": {"version": "1.0"}}

    with pytest.raises(KeyError) as excinfo:
        session1.add_extra_field("catalogue", {"version": "2.0"})
        assert str(excinfo.value) == "Endpoint catalogue not found"

    # Make sure that adding a new sesson doesn't overwrite the old one
    session3 = ApiHandler()
    assert session3 is session1
    assert session1.server_url == LOCALHOST
    assert session3.server_url == LOCALHOST


def test_telemetry_register():
    """
    Check that the TelemetryRegister class is a singleton & that we can register
    and deregister functions as we would expect.
    """
    session1 = TelemetryRegister("catalog")
    session2 = TelemetryRegister("catalog")

    # assert session1 is session2

    assert set(session1) == {
        "esm_datastore.search",
        "DfFileCatalog.search",
        "DfFileCatalog.__getitem__",
    }

    session1.register("test_function")

    assert set(session2) == {
        "esm_datastore.search",
        "DfFileCatalog.search",
        "DfFileCatalog.__getitem__",
        "test_function",
    }

    session1.deregister("test_function", "DfFileCatalog.__getitem__")

    assert set(session2) == {
        "esm_datastore.search",
        "DfFileCatalog.search",
    }

    with pytest.raises(ValidationError):
        session1.register(1.0)

    with pytest.raises(ValidationError):
        session1.deregister(1.0, 2.0, [3.0])

    session3 = TelemetryRegister("catalog")

    assert set(session3) == {
        "esm_datastore.search",
        "DfFileCatalog.search",
    }
