from __future__ import annotations

import hashlib
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]

CERTIFICATES = {
    "datacamp-data-scientist.jpg": {
        "sha256": "41b1e4b20344bc75ff0debb054db594213707ca7a413272cd65316fac2c7a748",
        "credential_id": "DS0020270967326",
        "verification_url": (
            "https://careerhub-api.datacamp.com/certificates/DS0020270967326/pdf"
        ),
        "date_patterns": (r"2026-04-30", r"April 30, 2026"),
    },
    "datacamp-data-engineer.jpg": {
        "sha256": "a980ae6b80f08b294b57e6f5074f308544571ba4eaf68b7fff8fee500319f3ad",
        "credential_id": "DE0013887181066",
        "verification_url": (
            "https://careerhub-api.datacamp.com/certificates/DE0013887181066/pdf"
        ),
        "date_patterns": (r"2026-04-01", r"April 1, 2026"),
    },
}
IGNORED_LOCAL_DIRECTORIES = {
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__marimo__",
    "__pycache__",
    "build",
    "dist",
}
DEFAULT_FIXTURE_SHA256 = {
    "airline": "d8a745bbc8c53e973328fe0e83b2fcc9fc36b45cd70fbc0f6ee9f87ce157d6fb",
    "cohort": "5aa30097da9a8f47c9c2cb17e73c4bcd0d6938640de7e81d154d72e7cd83fdbc",
    "restaurant": "7e8ef86c9729ccc136698165234afbcf18ce5172077f2c0615642a02d6fe7e9e",
    "streaming": "223f9931a90bb95e1e65425c6f8998c345a723a01740609ce36ba5c292f18228",
    "sports": "4713eb2e3d93a9ecf7a2215cffcc7b665fa1c56d5d18d3cf3e7282b99db87977",
}


def test_learning_lab_provenance_records_clean_room_reimplementation() -> None:
    provenance = (PROJECT_ROOT / "PROVENANCE.md").read_text(encoding="utf-8")
    normalized = provenance.casefold()

    for private_source in (
        "airline.ipynb",
        "cancer-patient-dataset.ipynb",
        "mcdonalds.ipynb",
        "notebook.ipynb",
        "winning-medal-in-judo.ipynb",
    ):
        assert private_source in provenance

    assert "clean-room" in normalized
    assert "deterministic synthetic" in normalized
    assert "code" in normalized
    assert "prose" in normalized
    assert "dataset" in normalized
    assert "output" in normalized
    assert "not migrated" in normalized or "not copied" in normalized


def test_learning_lab_provenance_pins_default_fixture_identity() -> None:
    provenance = (PROJECT_ROOT / "PROVENANCE.md").read_text(encoding="utf-8")

    assert "analytics-learning-labs/1.0" in provenance
    assert "2026-07-30" in provenance
    assert "seed `2026`" in provenance
    assert all(digest in provenance for digest in DEFAULT_FIXTURE_SHA256.values())


def test_learning_lab_tree_contains_no_legacy_notebook_or_dataset() -> None:
    forbidden_suffixes = {
        ".csv",
        ".feather",
        ".ipynb",
        ".parquet",
        ".sav",
        ".xlsx",
    }
    leaked = [
        path.relative_to(PROJECT_ROOT).as_posix()
        for path in PROJECT_ROOT.rglob("*")
        if path.is_file()
        and path.suffix.casefold() in forbidden_suffixes
        and not any(
            part in IGNORED_LOCAL_DIRECTORIES for part in path.relative_to(PROJECT_ROOT).parts
        )
    ]
    assert leaked == []


def test_credential_page_records_hashes_reviews_and_private_assessment_boundary() -> None:
    page = (REPOSITORY_ROOT / "CERTIFICATIONS.md").read_text(encoding="utf-8")
    normalized = page.casefold()

    for filename, evidence in CERTIFICATES.items():
        assert filename in page
        assert evidence["sha256"] in page
        assert evidence["credential_id"] in page
        assert evidence["verification_url"] in page
        assert any(re.search(pattern, page) for pattern in evidence["date_patterns"])

    assert "visible-content review" in normalized
    assert "metadata review" in normalized
    assert "gps" in normalized
    assert "author" in normalized
    for withheld_evidence in (
        "assessment prompts",
        "datasets",
        "solutions",
        "schemas",
        "metrics",
        "outputs",
        "grader rules",
    ):
        assert withheld_evidence in normalized


def test_approved_credential_assets_match_exact_owner_provided_hashes() -> None:
    asset_root = REPOSITORY_ROOT / "assets" / "certifications"

    for filename, evidence in CERTIFICATES.items():
        asset = asset_root / filename
        digest = hashlib.sha256(asset.read_bytes()).hexdigest()
        assert digest == evidence["sha256"]
