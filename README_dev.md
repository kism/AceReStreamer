# Acestream Webplayer Development Guide

## Run test sites to scrape

```bash
./scripts/run-test-webservers.sh
```

## Config

`instance/config.toml`

```toml
# Configuration file for Ace ReStreamer v0.3.0 https://github.com/kism/ace-restreamer
epgs = []

[app]
password = ""
ace_address = "http://localhost:6878"
transcode_audio = true
ace_max_streams = 4

[flask]
DEBUG = false
TESTING = false
SERVER_NAME = "http://127.0.0.1:5100"

[logging]
level = "INFO"
path = ""

[scraper]
user_agent = ""

[[scraper.html]]
name = "Scrape Site Page 1"
slug = "Scrape-Site-Page-1"
url = "http://localhost:8999/site1/index.html"
target_class = "column_title"
check_sibling = true

[scraper.html.title_filter]
always_exclude_words = []
always_include_words = []
exclude_words = []
include_words = []
regex_postprocessing = ""

[[scraper.html]]
name = "Scrape Site Page 2"
slug = "Scrape-Site-Page-2"
url = "http://localhost:8999/site2/index.html"
target_class = "streamtext"
check_sibling = true

[scraper.html.title_filter]
always_exclude_words = []
always_include_words = []
exclude_words = []
include_words = []
regex_postprocessing = "Server \\d+: "

[[scraper.html]]
name = "Scrape Site Page 3"
slug = "Scrape-Site-Page-3"
url = "http://localhost:8999/site3/index.html"
target_class = ""
check_sibling = false

[scraper.html.title_filter]
always_exclude_words = []
always_include_words = []
exclude_words = []
include_words = []
regex_postprocessing = ""

[[scraper.iptv_m3u8]]
name = "IPTV List"
slug = "IPTV-List"
url = "http://localhost:8999/site4/list.m3u8"

[scraper.iptv_m3u8.title_filter]
always_exclude_words = []
always_include_words = []
exclude_words = []
include_words = []
regex_postprocessing = ""

```

## Run the application

```bash
flask --app acerestreamer run --port 5100 --debug
```
