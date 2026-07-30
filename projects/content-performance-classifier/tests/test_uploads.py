from __future__ import annotations

import pytest

from content_performance_classifier import InputValidationError, read_content_csv


def test_upload_reader_accepts_bounded_utf8_csv() -> None:
    payload = (
        b"content_id,topic_family,content_type,word_count,readability_score,"
        b"age_days,internal_link_count,entity_count,query_coverage,"
        b"update_cadence,high_engagement\n"
        b"example,technical,guide,900,60,90,8,14,0.7,4,1\n"
    )

    frame = read_content_csv(payload)

    assert frame["content_id"].tolist() == ["example"]


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (b"", "empty"),
        (b"\xff\xfe", "UTF-8"),
        (b"content_id\n", "data rows"),
    ],
)
def test_upload_reader_rejects_malformed_input(payload: bytes, message: str) -> None:
    with pytest.raises(InputValidationError, match=message):
        read_content_csv(payload)


def test_upload_reader_enforces_byte_and_row_caps() -> None:
    with pytest.raises(InputValidationError, match="5 MB"):
        read_content_csv(b"x" * (5_000_001))

    payload = b"content_id\n" + b"\n".join(f"content-{index}".encode() for index in range(5_001))
    with pytest.raises(InputValidationError, match="5,000"):
        read_content_csv(payload)
