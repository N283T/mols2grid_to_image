# PyPI Publishing & CI Setup

## Context

The project is functionally complete (30 tests passing, clean code) but lacks PyPI metadata, a LICENSE file, and CI/CD. This plan adds everything needed to publish on PyPI with automated testing and release workflows.

## Branch

`feature/pypi-publishing`

## Step 1: Add MIT LICENSE

Create `LICENSE` with standard MIT text, copyright 2025 N283T.

## Step 2: Update pyproject.toml

- `requires-python`: `>=3.13` → `>=3.10` (code already compatible — PEP 604 unions work from 3.10)
- Add `license = "MIT"`, `authors = [{name = "N283T"}]`
- Add `keywords` (chemistry, mols2grid, rdkit, smiles, etc.)
- Add `classifiers` (Beta, Science/Research, MIT, Python 3.10-3.13, Chemistry)
- Add `[project.urls]` (Homepage, Repository, Issues → GitHub)
- Add `pytest-cov` to dev dependencies

## Step 3: GitHub Actions — Test (`test.yml`)

- Trigger: push to main, PRs
- Matrix: Python 3.10, 3.11, 3.12, 3.13 (`fail-fast: false`)
- Steps: checkout → `astral-sh/setup-uv` → `uv sync` → `playwright install --with-deps chromium` → `pytest --cov`

## Step 4: GitHub Actions — Lint (`lint.yml`)

- Trigger: push to main, PRs
- Single Python 3.13
- Steps: `ruff format --check .` → `ruff check .`

## Step 5: GitHub Actions — Publish (`publish.yml`)

- Trigger: `release: published`
- Two jobs (least privilege):
  - **build**: `uv build` → upload artifact
  - **publish**: download artifact → `pypa/gh-action-pypi-publish` with trusted publisher (OIDC, `id-token: write`, `environment: pypi`)

## Step 6: Update .gitignore

Add `.ruff_cache/`, `.coverage`, `coverage.xml`, `htmlcov/`

## Step 7: Update README.md

- Add badges (PyPI version, Python versions, MIT license)
- Add `pip install mols2grid-to-image` to installation section
- Add License section at bottom
- Note: Playwright browser install step (`playwright install chromium`) in installation

## Manual Steps (after merge)

1. PyPI: https://pypi.org/manage/account/publishing/ → pending publisher (`mols2grid-to-image`, owner `N283T`, repo `mols2grid_to_image`, workflow `publish.yml`, environment `pypi`)
2. GitHub: Settings → Environments → create `pypi`
3. Create GitHub Release → triggers publish

## Files

| File | Action |
|------|--------|
| `LICENSE` | Create |
| `pyproject.toml` | Update |
| `.github/workflows/test.yml` | Create |
| `.github/workflows/lint.yml` | Create |
| `.github/workflows/publish.yml` | Create |
| `.gitignore` | Update |
| `README.md` | Update |

## Verification

```bash
uv sync
uv run pytest --cov=src/m2g_image --cov-report=term-missing
uv build  # Verify package builds
```

---

- [ ] **DONE** - Phase complete
