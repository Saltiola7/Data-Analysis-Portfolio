from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

REPOSITORY = Path(__file__).resolve().parents[1]
README = REPOSITORY / "README.md"
QUALITY_WORKFLOW = REPOSITORY / ".github" / "workflows" / "quality.yml"
CERTIFICATIONS = REPOSITORY / "CERTIFICATIONS.md"
CERTIFICATION_ASSETS = REPOSITORY / "assets" / "certifications"

FLAGSHIP_MOLAB_LINKS = {
    "wellness": (
        "https://molab.marimo.io/github/Saltiola7/data-portfolio/"
        "blob/main/projects/wellness-data-pipeline/app.py/wasm"
    ),
    "classifier": (
        "https://molab.marimo.io/github/Saltiola7/data-portfolio/"
        "blob/main/projects/content-performance-classifier/src/app.py/wasm"
    ),
    "opportunity": (
        "https://molab.marimo.io/github/Saltiola7/data-portfolio/"
        "blob/main/projects/public-sector-opportunity-pipeline/app.py/wasm"
    ),
}

LEARNING_LABS = {
    "Airline Delay Quality Lab": "airline_delays.py",
    "Synthetic Health Risk Quality Lab": "synthetic_cohort.py",
    "Restaurant Location Quality Lab": "restaurant_locations.py",
    "Streaming Catalog Explorer": "streaming_catalog.py",
    "Judo Medal Explorer": "sports_outcomes.py",
}

CERTIFICATION_EVIDENCE = {
    "datacamp-data-scientist.jpg": {
        "credential_id": "DS0020270967326",
        "sha256": "41b1e4b20344bc75ff0debb054db594213707ca7a413272cd65316fac2c7a748",
    },
    "datacamp-data-engineer.jpg": {
        "credential_id": "DE0013887181066",
        "sha256": "a980ae6b80f08b294b57e6f5074f308544571ba4eaf68b7fff8fee500319f3ad",
    },
}

FORBIDDEN_PRIVATE_SOURCE_NAMES = {
    "ml_solution.py",
    "validate_solution.py",
    "solution.py",
    "run_and_export.py",
    "describe_data.py",
    "airline.ipynb",
    "cancer-patient-dataset.ipynb",
    "mcdonalds.ipynb",
    "notebook.ipynb",
    "winning-medal-in-judo.ipynb",
}

IGNORED_LOCAL_DIRECTORIES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "node_modules",
}


def _repository_files() -> list[Path]:
    return [
        path
        for path in REPOSITORY.rglob("*")
        if path.is_file()
        and not any(
            part in IGNORED_LOCAL_DIRECTORIES for part in path.relative_to(REPOSITORY).parts
        )
    ]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256(usedforsecurity=False)
    with path.open("rb") as source:
        for block in iter(lambda: source.read(64 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _learning_lab_molab_link(app_filename: str) -> str:
    return (
        "https://molab.marimo.io/github/Saltiola7/data-portfolio/"
        "blob/main/projects/analytics-learning-labs/apps/"
        f"{app_filename}/wasm"
    )


def test_repository_has_no_static_portfolio_site() -> None:
    assert not (REPOSITORY / "site").exists()


def test_quality_workflow_has_no_pages_delivery() -> None:
    assert QUALITY_WORKFLOW.is_file()
    assert not (REPOSITORY / ".github" / "workflows" / "quality-pages.yml").exists()

    workflow = QUALITY_WORKFLOW.read_text(encoding="utf-8")
    forbidden = (
        "actions/upload-pages-artifact",
        "actions/deploy-pages",
        "pages: write",
        "id-token: write",
        "github-pages",
        "--scenario landing",
    )
    assert all(marker not in workflow for marker in forbidden)


def test_root_title_is_data_portfolio() -> None:
    readme_lines = README.read_text(encoding="utf-8").splitlines()

    assert readme_lines[0] == "# Data Portfolio"


def test_readme_is_github_first_with_eight_molab_apps() -> None:
    readme = README.read_text(encoding="utf-8")

    assert "https://github.com/Saltiola7/data-portfolio" in readme
    assert "saltiola7.github.io/data-portfolio" not in readme.lower()
    assert "GitHub Pages" not in readme
    assert all(link in readme for link in FLAGSHIP_MOLAB_LINKS.values())
    assert all(_learning_lab_molab_link(app) in readme for app in LEARNING_LABS.values())


def test_learning_labs_are_supporting_work_below_flagships() -> None:
    readme = README.read_text(encoding="utf-8")

    assert "## Supporting learning labs" in readme
    assert readme.index("## Flagship projects") < readme.index("## Supporting learning labs")


@pytest.mark.parametrize(("title", "app_filename"), LEARNING_LABS.items())
def test_each_learning_lab_has_source_and_durable_molab_link(
    title: str,
    app_filename: str,
) -> None:
    readme = README.read_text(encoding="utf-8")
    app = REPOSITORY / "projects" / "analytics-learning-labs" / "apps" / app_filename

    assert app.is_file()
    assert title in readme
    assert _learning_lab_molab_link(app_filename) in readme


def test_certification_assets_have_exact_approved_filenames() -> None:
    actual_filenames = (
        {path.name for path in CERTIFICATION_ASSETS.iterdir() if path.is_file()}
        if CERTIFICATION_ASSETS.is_dir()
        else set()
    )

    assert actual_filenames == set(CERTIFICATION_EVIDENCE)


@pytest.mark.parametrize(("filename", "evidence"), CERTIFICATION_EVIDENCE.items())
def test_certification_evidence_matches_approved_asset_and_verification(
    filename: str,
    evidence: dict[str, str],
) -> None:
    assert CERTIFICATIONS.is_file()

    page = CERTIFICATIONS.read_text(encoding="utf-8")
    asset = CERTIFICATION_ASSETS / filename
    credential_id = evidence["credential_id"]
    verification_url = f"https://careerhub-api.datacamp.com/certificates/{credential_id}/pdf"

    assert asset.is_file()
    assert _sha256(asset) == evidence["sha256"]
    assert filename in page
    assert evidence["sha256"] in page
    assert credential_id in page
    assert verification_url in page


def test_private_assessment_and_notebook_sources_are_absent() -> None:
    repository_files = _repository_files()
    private_root = "/" + "Users/tis/github/" + "tsc-data"
    searchable_suffixes = {".json", ".md", ".py", ".toml", ".txt", ".yaml", ".yml"}

    leaked_names = sorted(
        path.relative_to(REPOSITORY).as_posix()
        for path in repository_files
        if path.name in FORBIDDEN_PRIVATE_SOURCE_NAMES
    )
    leaked_paths = sorted(
        path.relative_to(REPOSITORY).as_posix()
        for path in repository_files
        if path.suffix in searchable_suffixes
        and private_root in path.read_text(encoding="utf-8", errors="ignore")
    )

    assert leaked_names == []
    assert leaked_paths == []


def test_mgm_internal_tools_are_not_standalone_portfolio_projects() -> None:
    readme = README.read_text(encoding="utf-8").lower()

    assert "article explorer" not in readme
    assert "keyword intelligence" not in readme
    assert not (REPOSITORY / "projects" / "article-explorer").exists()
    assert not (REPOSITORY / "projects" / "keyword-intelligence").exists()


def test_ci_exercises_all_eight_marimo_apps() -> None:
    workflow = QUALITY_WORKFLOW.read_text(encoding="utf-8")

    expected_scenarios = (
        "--scenario wellness --path apps/wellness-data-pipeline/",
        "--scenario classifier --path apps/content-performance-classifier/",
        "--scenario opportunity --path apps/public-sector-opportunity-pipeline/",
    )
    assert all(scenario in workflow for scenario in expected_scenarios)
    assert "uv sync --project projects/analytics-learning-labs --locked" in workflow
    assert all(app_filename in workflow for app_filename in LEARNING_LABS.values())
    assert "--scenario learning-labs" in workflow


def test_ci_exercises_direct_molab_routes_at_exact_pushed_sha() -> None:
    workflow = QUALITY_WORKFLOW.read_text(encoding="utf-8")

    assert "github.event.pull_request.head.sha || github.sha" in workflow
    assert "molab.marimo.io/github/Saltiola7/data-portfolio/blob/${MOLAB_SHA}" in workflow
    assert all(
        f"projects/analytics-learning-labs/apps/{app_filename}/wasm" in workflow
        for app_filename in LEARNING_LABS.values()
    )
    assert workflow.count("--url") >= len(LEARNING_LABS)
