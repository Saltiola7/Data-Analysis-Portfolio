# Maintenance and Retirement

- GitHub project source, locked environments, tests, and provenance are the
  maintained evidence.
- Molab is a replaceable third-party runtime; CI proves the Marimo apps through
  temporary WASM builds even if Molab availability changes.
- Direct Molab links are checked during integration and whenever app paths or
  repository ownership change.
- GitHub Pages, the `site/` tree, and their deployment permissions are retired.
- No owner-operated runtime, visitor-data store, account system, or uptime
  commitment exists.
- Legacy notebooks remain outside public history. A future clean-room rebuild
  must start a new bounded cycle and pass the same admission contract.
- Review every project lock, critical-vulnerability scan, SPDX SBOM, and all
  eight Molab routes at least quarterly and after material Marimo, Pyodide,
  pandas, package-format, app-path, or repository-ownership changes.
- Keep learning-lab default fixture hashes pinned to generator version, seed,
  and canonical serialization. A fixture change requires generator-version,
  provenance, claim, and browser-evidence review.
- Recheck Marimo's generated numeric-input accessible name on each runtime
  upgrade. Remove the documented limitation only after the live accessibility
  tree exposes plain `Seed` and the browser gate asserts it.
- Replacing a credential screenshot requires renewed owner approval, exact
  checksum, dimensions, visible-content and metadata review, and a working
  issuer verification URL. Assessment material remains permanently excluded.
- Retire a lab link before its source when default execution, provenance,
  privacy, live dependency compatibility, or evidence reproducibility fails.
  Preserve the retirement reason in the changelog.
- Roll back source through a normal Git revert of the affected gate commit.
  No data migration or owner-service rollback exists because fixtures are
  generated on demand and visitor state is not retained.
