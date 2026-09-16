"""
Unit tests for Step 1: Pydantic v2 Models & Settings.
"""

import pytest
from pydantic import ValidationError
# pyrefly: ignore [missing-import]
from lab.models import DocumentPayload, ClientConfig


def test_document_payload_normalization():
    doc = DocumentPayload(
        doc_id="  UPPER_CASE_DOC_123  ",
        title="Test Title",
        content="This is a test document with minimum required length.",
        tags=["external"]
    )
    assert doc.doc_id == "upper_case_doc_123"
    assert doc.get_token_estimate() > 0
    assert doc.metadata.get("source") == "unknown_external"


def test_invalid_doc_id_characters():
    with pytest.raises(ValidationError):
        DocumentPayload(
            doc_id="invalid@doc#name",
            title="Title",
            content="Valid content string that meets minimum length criteria."
        )


def test_client_config_defaults():
    config = ClientConfig()
    assert config.app_name == "FDE-Platform"
    assert config.max_concurrent_requests >= 1
    assert config.api_key.get_secret_value() != ""
