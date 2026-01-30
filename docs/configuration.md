# Configuration

There are two things you will need to configure, Scrapers and EPG sources.

## Scraper Configuration

Scrapers are what look for AceStream links, they can scrape web pages, IPTV playlists or use a mysterious API site I found but won't provide.

Scrapers right now are configured via json, even in the frontend. Each scraper has a name filter option so you can filter the results.

### IPTV Scraper

For an IPTV source, you will need to provide a URL to an m3u or m3u8 playlist. The scraper will then look for AceStream links in the playlist.

A playlist that is scrapable will look something like this:

```text
#EXTM3U
#EXTINF:-1 group-title="General", IPTV1
acestream://1000000000000000000000000000000000000001
#EXTINF:-1 group-title="General", IPTV2
acestream://1000000000000000000000000000000000000002
#EXTINF:-1 group-title="General", IPTV3
acestream://4000000000000000000000000000000000000003
#EXTINF:-1 group-title="General", IPTV4
acestream://1000000000000000000000000000000000000004
```

Other URI schemes will also work.

```text
acestream://",
http://127.0.0.1:6878/ace/getstream?id=
http://127.0.0.1:6878/ace/getstream?content_id=
http://127.0.0.1:6878/ace/manifest.m3u8?id=
http://127.0.0.1:6878/ace/manifest.m3u8?content_id=
plugin://script.module.horus?action=play&id=
http://127.0.0.1:6878/ace/getstream?infohash=
http://127.0.0.1:6878/ace/manifest.m3u8?infohash=
```

The config will look something like this:

```{literalinclude} generated/iptv_example.json
:language: json
```

### HTML Scraper

Second we have a scraper that will scrape any HTML page for acestream links. You provide a URL and it will look for links on the page. Finding titles for the streams, there are two extra settings in the scraper config to help:

- target_class: Specify the HTML class to look for titles in.
- check_sibling: Specifies if the title is in a sibling element to the link.

In this example

```{literalinclude} generated/html_example.json
:language: json
```

In this example, the scraper will look for links on the page, and then look for a sibling element with the class `stream-title` to get the title of the stream. The regex_postprocessing will remove any "Mirror X: " from the title.

### API Scraper

There is a API server I found that lists a bunch of AceStream links. You can use this by providing the link. The server provides a response as a list of JSON objects:

The server will give an api response a bit like this:

```{literalinclude} generated/api_site_response_example.json
:language: json
```

To scrape this, your config will look something like this:

```{literalinclude} generated/api_example.json
:language: json
```

When get scraped, the scraper will need to use ace to convert the infohash to a content_id.

### Title Filter

This is a method to filter the titles of streams found by scrapers.

Items in regex_postprocessing will be applied to remove parts of the title via re.sub.

The other lists will be evaluated in order:

- always_exclude_words
- always_include_words
- exclude_words
- include_words (if populated, otherwise allow any)

In this example, i'm looking for English language IPTV streams, and excluding any adult content. This assumes that the stream titles have country codes in brackets, like `[AU]` or `[IE]`.

```{literalinclude} generated/iptv_example_titlefilter.json
:language: json
```

### Name Overrides

There is a section in the config and web interface for name overrides. This lets you map a content_id or infohash to a specific title, this is useful for streams that have bad or no titles.

The best practice for titles is channel name, followed by the two character country code in brackets. Example: `Channel 1 [AU]`

## EPG Configuration

Load the example in the web interface. The program will normalise the channel ids to `Channel 1.au` format, which is what open-epg uses. You can use the tvg_id_overrides section to map channel ids in the EPG to match your stream's tvg ids.
