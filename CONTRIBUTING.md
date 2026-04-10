# Contributing to StockSage

Welcome! We adhere to enterprise-grade standards including strict version control and automated testing.

## Agile Methodology
We follow Agile/Scrum.
- Use issue tracking for all features and bug fixes.
- 2-week sprint cycles.

## Gitflow Branching Strategy
- `main`: Production-ready code.
- `develop`: Active development.
- `feature/*`: Feature branches off `develop`.
- `hotfix/*`: Critical fixes off `main`.

## Testing Standards
All new routes and ML models must be accompanied by a `pytest` unit test in the `tests/` directory.

## Pull Requests
All PRs must pass the GitHub Actions CI pipeline (Pytest suite) before being eligible for a merge review.
