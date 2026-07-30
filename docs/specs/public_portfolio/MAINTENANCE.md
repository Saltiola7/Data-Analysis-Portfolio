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
