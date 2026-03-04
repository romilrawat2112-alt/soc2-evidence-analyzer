"""Tests for evidence file parsers."""

import csv
from pathlib import Path

import pytest

from soc2_analyzer.parsers import UnsupportedFileTypeError, parse_evidence


@pytest.fixture
def sample_dir():
    """Return the sample_evidence directory path."""
    return Path(__file__).parent.parent / "sample_evidence"


def test_parse_text_file(sample_dir):
    """Test parsing a plain text file."""
    result = parse_evidence(sample_dir / "change_mgmt_policy.txt")
    assert result.filename == "change_mgmt_policy.txt"
    assert result.file_type == "txt"
    assert "CHANGE MANAGEMENT POLICY" in result.extracted_text
    assert result.image_bytes is None


def test_parse_json_file(sample_dir):
    """Test parsing a JSON config file."""
    result = parse_evidence(sample_dir / "aws_iam_policy.json")
    assert result.filename == "aws_iam_policy.json"
    assert result.file_type == "json"
    assert "MFARequired" in result.extracted_text


def test_parse_csv_file(sample_dir):
    """Test parsing a CSV file."""
    result = parse_evidence(sample_dir / "access_review_log.csv")
    assert result.filename == "access_review_log.csv"
    assert result.file_type == "csv"
    assert "user_id" in result.extracted_text
    assert "Alice Chen" in result.extracted_text


def test_unsupported_file_type(tmp_path):
    """Test that unsupported file types raise an error."""
    unsupported = tmp_path / "test.docx"
    unsupported.write_text("test")
    with pytest.raises(UnsupportedFileTypeError):
        parse_evidence(unsupported)


def test_parse_evidence_returns_timestamp(sample_dir):
    """Test that parsed evidence includes a timestamp."""
    result = parse_evidence(sample_dir / "firewall_rules.txt")
    assert result.parse_timestamp is not None
