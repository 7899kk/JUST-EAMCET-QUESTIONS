# Deployment status

Status: **Blocked — site is not live**.

The complete collected archive is committed to https://github.com/7899kk/JUST-EAMCET-QUESTIONS and runs locally. GitHub Pages publishing is configured in `.github/workflows/pages.yml`.

The [deployment run](https://github.com/7899kk/JUST-EAMCET-QUESTIONS/actions/runs/37141161971) failed at `actions/configure-pages`:

> Create Pages site failed. Error: Resource not accessible by integration.

Direct creation through the connected GitHub integration also returned HTTP 403. No user approval was missing; the available credential lacks Pages configuration permission.

A repository administrator must choose **Settings → Pages → Source: GitHub Actions**, then rerun the publish workflow. Intended URL: https://7899kk.github.io/JUST-EAMCET-QUESTIONS/ . This URL is not claimed live.

The static export was tested locally under the repository URL prefix. Search, original PDF regions, mathematical rendering and offline bundle restoration passed. `python scripts/export_static.py` produces the deployment assets.

The optional Sites fallback was inspected but could not run: the [Sites hosting skill](skill://plugin_connector_1p_689987207de08191979cf68eca2941c6/sites-hosting/SKILL.md) requires “Run the bundled script directly in the selected checkout,” and its `site-workflow.mjs` publisher is unavailable in this execution environment. No unused Site was registered.
