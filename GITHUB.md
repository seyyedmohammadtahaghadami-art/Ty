# GitHub setup

The repository root must contain `index.html`. Do not upload only the files from `backend/` into the root.

Expected root folders: `.github`, `assets`, `backend`, `css`, `docs`, `js`.

Enable Settings → Pages → GitHub Actions. The workflow deploys the repository root.

For a custom domain, set the domain in GitHub Pages and configure DNS. A `CNAME` file may be populated with the exact domain.
