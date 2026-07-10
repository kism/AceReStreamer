# CLI Tools

## Scraper Mode

`acerestreamer-scrape` / `python -m acere.cli.scraper` is a tool that will scrape streams and provide them in m3u8 format for use with Horus and other Ace Stream clients.

### Scraper Mode as a GitHub Action

This is intended to be run as a github action to generate playlist files, which are served by github itself.

1. Create a git repo
2. Enable lfs for the repo
3. Add a workflow file in `.github/workflows/scrape.yml` with something like this:

```yaml
name: Create M3U Playlists

on:
  schedule:
    - cron: "30 14 * * *" # Run this workflow daily at 14:30 UTC
  workflow_dispatch: # Allow manual triggering

jobs:
  update-list:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout Repo
        uses: actions/checkout@v5

      - name: Configure Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.14"

      - name: Install uv
        uses: astral-sh/setup-uv@v5

      - name: Run the scraper
        run: uvx --from "git+https://github.com/kism/acerestreamer" acerestreamer-scrape --app-config config.json
        env:
          UV_GIT_LFS: 1

      - name: Configure git
        run: |
          git config --global user.name "github-actions"
          git config --global user.email "actions@github.com"

      - name: Commit and Push Changes
        run: |
          git add .
          if [ "$(git diff --cached --numstat | wc -l)" -gt 1 ]; then
            git commit -m "Update m3u"
            git push
          else
            echo "No changes to commit, ignoring README.md."
          fi
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

4. In the repo, run adhoc to generate the config file and test.

```bash
UV_GIT_LFS=1 uvx --from "git+https://github.com/kism/acerestreamer" acerestreamer-scrape --app-config config.json
```
