# CREST Engineering Handoff Audit

Audit date: 24 June 2026

## Result

The codebase is clean for the private GitHub handoff. The final source tree contains no local environment file, full candidate dataset, embedding artifact, SQLite database, dependency directory, organizer PDF, or organizer presentation template.

## Verification

- Backend: 11 tests passed.
- Frontend: ESLint, the Vite production build, and the Playwright UI regression suite passed.
- Browser regression: landing WebGL health, all Analytics tabs and chart containment, current handoff copy, and fully loaded Pipeline columns passed at 1478x1000 and 1280x800 viewports.
- Frontend dependencies: `npm audit --omit=dev` found no known vulnerabilities.
- Python demo and full manifests: `pip-audit` found no known vulnerabilities after upgrading to FastAPI 0.138.0, Starlette 1.3.1, Uvicorn 0.49.0, Pydantic 2.13.4, and pytest 9.0.3.
- Submission: the organizer validator reports `Submission is valid.`
- Full ranking: 100,000 processed, 580 excluded, 100 ranked, 150.602 seconds.
- Automated ranking audit: every check in `backend/data/automated_audit_report.json` passes.
- Docker: the 89.5 MB local image served the frontend, health API, analytics, and the official 50-candidate sample ranking.
- Staged Git content: whitespace and secret scans passed; the staged source was under 1 MB excluding the official demo sample and generated artifacts.

## Remote verification

- Repository: `Zian-Surani/crest-redrob-candidate-intelligence`
- Visibility: private
- Default branch: `main`
- Initial verified commit: `95d971aa7f6165aee2a9f1ca523d7c2b200304fc`
- Author and committer: `Zian Surani <zian.surani@gmail.com>`
- Forbidden paths found in the remote tree: none

## Remaining human controls

- Complete the blank human-review fields in `manual_review_top50.csv` and `reasoning_audit_10.csv`.
- Approve a hosting target before publishing the Docker sandbox.
- Add the resulting sandbox URL to `submission_metadata.yaml`.
- Rename the final CSV to the registered participant ID required by the portal.
