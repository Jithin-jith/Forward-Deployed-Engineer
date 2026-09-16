"""
Module 01 - Step 1: Data Validation & Configuration with Pydantic v2.

This lab demonstrates production-grade type enforcement, custom field validators,
settings management via `pydantic-settings`, and sensitive credential masking.

Why Pydantic v2 for Forward Deployed Engineers?
----------------------------------------------
In production AI and enterprise data pipelines, unstructured data from external APIs,
LLM JSON outputs, or user inputs can be corrupted, missing fields, or improperly typed.
Pydantic v2 (compiled in Rust via `pydantic-core`) validates input schemas at high speed,
casts types when safe, and provides strict error feedback when data breaks constraints.

Key Concepts Demonstrated:
1. `BaseModel`: Defining typed data contracts.
2. `Field`: Declaring constraints (min/max lengths, default factories, descriptions).
3. `@field_validator`: Normalizing and validating specific fields (e.g. lowecasing document IDs).
4. `@model_validator`: Cross-field validation logic (checking combinations of attributes).
5. `SecretStr`: Masking API keys and passwords in logs.
6. `BaseSettings`: Auto-loading configuration from environment variables or `.env` files.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class LogLevel(str, Enum):
    """
    Supported logging levels.
    Inheriting from `str` ensures seamless JSON serialization without custom json_encoders.
    """
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class ClientConfig(BaseSettings):
    """
    Application & Client configuration management.
    Automatically resolves values from environment variables or `.env` file.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    app_name: str = Field(default="FDE-Platform", description="Identifier for deployed app")
    environment: str = Field(default="development", description="Execution mode: development, staging, prod")
    api_key: SecretStr = Field(default="secret_dev_key_12345", description="Sensitive Gemini/LLM API Key")
    max_concurrent_requests: int = Field(default=10, ge=1, le=100, description="Rate limit max concurrency threshold")


class DocumentPayload(BaseModel):
    """
    Enterprise Document Schema representing raw documents targeted for ingestion and embedding.
    """
    doc_id: str = Field(..., min_length=3, description="Unique Document Identifier")
    title: str = Field(..., min_length=1, max_length=255, description="Document Title")
    content: str = Field(..., min_length=10, description="Full body text of the document")
    tags: List[str] = Field(default_factory=list, description="Categorization labels")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary Key-Value metadata")
    author_email: Optional[str] = Field(default=None, description="Author contact email")

    @field_validator("doc_id")
    @classmethod
    def validate_and_normalize_doc_id(cls, v: str) -> str:
        """
        Validates that doc_id contains only alphanumeric characters, underscores, or hyphens,
        and normalizes the result to lowercase.
        """
        clean_v = v.strip()
        if not all(c.isalnum() or c in ("_", "-") for c in clean_v):
            raise ValueError("doc_id must contain only alphanumeric characters, underscores, or hyphens.")
        return clean_v.lower()

    @model_validator(mode="after")
    def check_metadata_and_tags(self) -> "DocumentPayload":
        """
        Cross-field validator ensuring metadata contains 'source' if tags include 'external'.
        """
        if "external" in self.tags and "source" not in self.metadata:
            self.metadata["source"] = "unknown_external"
        return self

    def get_token_estimate(self) -> int:
        """
        Provides a rough token estimate based on character length (~4 characters per token).
        """
        return len(self.content) // 4


def run_demo():
    print("=" * 60)
    print("STEP 1: PYDANTIC V2 VALIDATION & SETTINGS DEMO")
    print("=" * 60)

    # 1. Settings Loading
    config = ClientConfig()
    print(f"Loaded Config App: {config.app_name}")
    print(f"Environment:       {config.environment}")
    print(f"Max Concurrency:   {config.max_concurrent_requests}")
    # SecretStr hides plaintext when printed:
    print(f"API Key (Masked):  {config.api_key}")
    print(f"API Key (Secret):  {config.api_key.get_secret_value()}")

    print("\n--- Validating DocumentPayload ---")
    doc = DocumentPayload(
        doc_id="DOC_FDE_999",
        title="Forward Deployed Architecture Guide",
        content="Forward Deployed Engineers work directly with customers to build AI data pipelines.",
        tags=["external", "architecture"],
        metadata={"author": "FDE Team"}
    )
    print(f"Original doc_id: 'DOC_FDE_999' -> Normalized: '{doc.doc_id}'")
    print(f"Auto-injected metadata: {doc.metadata}")
    print(f"Estimated Tokens: {doc.get_token_estimate()}")

    print("\n--- Testing Validation Errors ---")
    try:
        DocumentPayload(
            doc_id="INVALID ID!",
            title="Short",
            content="Too short"  # Min length 10 required
        )
    except ValueError as e:
        print(f"Caught expected validation errors:\n{e}")


if __name__ == "__main__":
    run_demo()
