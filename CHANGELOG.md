# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Updated sync logic to continue processing when individual DDF downloads fail.
- Added end-of-run failed-download reporting with filename and error details.

### Fixed
- Fixed full sync abort behavior caused by a single upstream DDF endpoint returning HTTP 5xx.

## [0.2.0] - 2026-04-26

### Added
- Added a complete project README with installation, usage, sync behavior, and troubleshooting documentation.
- Added this `CHANGELOG.md` in Keep a Changelog format.
- Added `--full` CLI option to force a complete DDF sync.
- Added run summary output for both full and incremental sync modes.

### Changed
- Refactored script path handling to use absolute paths via `pathlib`, removing `chdir` side effects.
- Changed manifest retrieval to a single API fetch per sync pass.
- Improved incremental update logic with explicit version map comparisons and skip counting.
- Updated error handling to return non-zero exit codes with clear network and processing error messages.

### Fixed
- Fixed duplicate manifest API calls in full sync mode.
- Fixed broad exception usage in incremental sync logic by using explicit checks.
- Fixed potential stale-manifest handling by consistently replacing the active manifest only after a successful run.

## [0.1.0] - 2026-04-26

### Added
- Initial script for downloading Schneider Electric SNMP DDF files and organizing them by DDF state.
