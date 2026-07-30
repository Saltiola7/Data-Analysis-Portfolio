from __future__ import annotations

from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
README = REPOSITORY / "README.md"
QUALITY_WORKFLOW = REPOSITORY / ".github" / "workflows" / "quality.yml"

MOLAB_LINKS = {
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


def test_readme_is_github_first_with_three_molab_apps() -> None:
    readme = README.read_text(encoding="utf-8")

    assert "https://github.com/Saltiola7/data-portfolio" in readme
    assert "saltiola7.github.io/data-portfolio" not in readme.lower()
    assert "GitHub Pages" not in readme
    assert all(link in readme for link in MOLAB_LINKS.values())


def test_ci_still_exercises_all_three_browser_journeys() -> None:
    workflow = QUALITY_WORKFLOW.read_text(encoding="utf-8")

    expected_scenarios = (
        "--scenario wellness --path apps/wellness-data-pipeline/",
        "--scenario classifier --path apps/content-performance-classifier/",
        "--scenario opportunity --path apps/public-sector-opportunity-pipeline/",
    )
    assert all(scenario in workflow for scenario in expected_scenarios)
