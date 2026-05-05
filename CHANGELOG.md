## 2.3.5 (May 5, 2026)

- Bump project version (2.3.4 release was tagged without a version bump).

## 2.3.4 (May 5, 2026)

- Security patch from dependabot.
- Update GitHub actions to run on Node.js 24

## 2.3.3 (March 9, 2026)

- Expose the backend version in the API for the Terms of Use page.
- Add a subgallery helper for gallery tagging in the admin.
- Add a copyright stamp position selector for image renditions.
- Harden media form validation and error handling.
- Add `include_subgalleries` to media queries and document the parameter.
- Include subgalleries when filtering media by gallery and exclude gallery filters.
- Default subgallery parent selection to blank in the admin helper.

## 2.3.2 (February 25, 2026)

- Add copyright stamp watermark overlay to image renditions.
- Add "Recreate renditions" admin action for re-processing existing images.

## 2.3.1 (February 18, 2026)

- Add new contributor organizations to tag fields.

## 2.3.0 (February 16, 2026)

- Add image labeling library for automated imaging instruments, including guide images, admin upload form, plankton group navigation, and summary statistics.
- Security hardening and improved login UX with attempt warnings and failure logging.
- Dependency updates (Django 5.2.11, Pillow, sqlparse).

## 2.2.2 (December 18, 2025)

- Security patch from dependabot.

## 2.2.1 (November 7, 2025)

- Security patch from dependabot.

## 2.2.0 (November 5, 2025)

- Add uv project management.
- Add ruff formating and linting.
- Add pre-commit to (optionally) check format and linting on each commit.
- Add github action steps for checking format and linting.
- New URI template for Dyntaxa links.
- Add parameter to include child taxon in media query.
- Add parameter to filter only most prioritized media for each taxon in media query.
- Import added columns in `facts_external_links_gbif.txt`.
- Security mitigations from dependabot.

## 2.1.1 (October 20, 2024)

Includes a minor fix for an integrity error when changing taxon for an image under certain circumstances.

## 2.1.0 (October 16, 2024)

- Add `label` for external link data structures
- Add IOC-UNESCO Toxins as a data source for external links
- Use _Bacillariophyceae_ instead of _Bacillariophyta_ as closest parent for the Diatoms group in filters

## 2.0.1 (October 15, 2024)

Patch release that includes security updates for Django.

## 2.0.0 (April 11, 2024)

Initial public release.
