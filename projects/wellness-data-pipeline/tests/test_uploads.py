import pandas as pd
import pytest

from wellness_data_pipeline import UploadError, read_csv_upload


def test_read_csv_upload_accepts_bounded_utf8_csv() -> None:
    result = read_csv_upload(b"name,value\nalpha,1\nbeta,2\n")

    pd.testing.assert_frame_equal(
        result,
        pd.DataFrame({"name": ["alpha", "beta"], "value": [1, 2]}),
    )


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (b"", "empty"),
        (b"\xff\xfe\x00", "UTF-8"),
        (b"name\n", "no data rows"),
    ],
)
def test_read_csv_upload_rejects_invalid_content_without_echoing_payload(
    payload: bytes,
    message: str,
) -> None:
    with pytest.raises(UploadError, match=message) as error:
        read_csv_upload(payload)

    assert repr(payload) not in str(error.value)


def test_read_csv_upload_enforces_byte_limit_before_parsing() -> None:
    payload = b"x" * 101

    with pytest.raises(UploadError, match="100 bytes"):
        read_csv_upload(payload, max_bytes=100)


def test_read_csv_upload_enforces_row_limit() -> None:
    payload = b"name\none\ntwo\nthree\n"

    with pytest.raises(UploadError, match="2 rows"):
        read_csv_upload(payload, max_rows=2)
