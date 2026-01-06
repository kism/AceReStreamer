# Acestream Webplayer Development Guide

## Sync frontend and backend

```bash
./scripts/generate-client.sh
```

## Run test sites to scrape

```bash
./scripts/run-test-webservers.sh
```

## Config

`instance/config.json`

```json
{
  "app": {
    "password": "",
    "ace_address": "http://localhost:6878",
    "transcode_audio": false,
    "ace_max_streams": 4
  },
  "flask": {
    "DEBUG": false,
    "TESTING": false,
    "SERVER_NAME": "http://127.0.0.1:5100"
  },
  "logging": {
    "level": "INFO",
    "path": ""
  },
  "scraper": {
    "html": [
      {
        "name": "Scrape Site Page 1",
        "slug": "Scrape-Site-Page-1",
        "url": "http://localhost:8999/site1/index.html",
        "target_class": "column_title",
        "check_sibling": true,
        "title_filter": {
          "always_exclude_words": [],
          "always_include_words": [],
          "exclude_words": [],
          "include_words": [],
          "regex_postprocessing": ""
        }
      },
      {
        "name": "Scrape Site Page 2",
        "slug": "Scrape-Site-Page-2",
        "url": "http://localhost:8999/site2/index.html",
        "target_class": "streamtext",
        "check_sibling": true,
        "title_filter": {
          "always_exclude_words": [],
          "always_include_words": [],
          "exclude_words": [],
          "include_words": [],
          "regex_postprocessing": "Server \\d+: "
        }
      },
      {
        "name": "Scrape Site Page 3",
        "slug": "Scrape-Site-Page-3",
        "url": "http://localhost:8999/site3/index.html",
        "target_class": "",
        "check_sibling": false,
        "title_filter": {
          "always_exclude_words": [],
          "always_include_words": [],
          "exclude_words": [],
          "include_words": [],
          "regex_postprocessing": ""
        }
      }
    ],
    "iptv_m3u8": [
      {
        "name": "IPTV List",
        "slug": "IPTV-List",
        "url": "http://localhost:8999/site4/list.m3u8",
        "title_filter": {
          "always_exclude_words": [],
          "always_include_words": [],
          "exclude_words": [],
          "include_words": [],
          "regex_postprocessing": ""
        }
      }
    ]
  },
  "epgs": []
}
```

## Run the application

```bash
flask --app acerestreamer run --port 5100 --debug
```
