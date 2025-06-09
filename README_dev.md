# Acestream Webplayer Development Guide

## Run test sites to scrape

```bash
./scripts/run-test-webservers.sh
```

## Config

`instance/config.toml`

```toml
# Configuration file for Acestream Webplayer v0.1.4 https://github.com/kism/acestream-webplayer
[app]
ace_address = "http://localhost:6878"

[app.ace_scrape_settings]
scrape_interval = 7200
disallowed_words = ["beelzebub"]
[[app.ace_scrape_settings.site_list]]
name = "Scrape Site Page 1"
url = "http://localhost:8999/site1/index.html"
html_class = "column_title"
check_sibling = true
stream_title_regex_postprocessing = ""

[[app.ace_scrape_settings.site_list]]
name = "Fun Scraping Site 2"
url = "http://localhost:8999/site2/index.html"
html_class = "streamtext"
check_sibling = true
stream_title_regex_postprocessing = "Server \\d+: "

[[app.ace_scrape_settings.site_list]]
name = "Edge Case Site 3"
url = "http://localhost:8999/site3/index.html"
html_class = ""
check_sibling = false
stream_title_regex_postprocessing = ""

[flask]
DEBUG = false
TESTING = false
SERVER_NAME = "http://127.0.0.1:5100"

[logging]
level = "INFO"
path = ""
```

## Run the application

```bash
flask --app acestreamwebplayer run --port 5100 --debug
```
