# Quality Cache Culling Changes

## Summary

Change the quality check schedule from once-daily (3:33 AM) to four times daily at semi-random intervals (~6 hours +/- 30 minutes), and update the culling rules.

## Changes

### 1. Replace fixed daily schedule with 4x/day semi-random schedule

**File:** `acere/database/handlers/quality_cache.py`

- Remove `_DAILY_CHECK_HOUR`, `_DAILY_CHECK_MINUTE`, and `_seconds_until_daily_check()`.
- Add `_seconds_until_next_check()` that returns `6 * 3600 + random.uniform(-1800, 1800)` (6 hours +/- 30 minutes).
- Update `start_daily_check_thread()` (rename to `start_check_thread()`) to use the new interval function instead of targeting a specific clock time. The loop sleeps for the random interval, runs the check, then picks a new random interval.
- Update the thread name and log messages accordingly.

### 2. Update culling rules in `cull_stale_streams()`

**File:** `acere/database/handlers/quality_cache.py`

Replace the current two-rule culling with the new rules:

**Rule 1 — Never worked + not scraped in 1 day:**

- `last_scraped_time` is older than 1 day AND
- `has_ever_worked` is `False` (no quality cache entry, or `last_quality_success_time is None`)
- This covers the "attempted three times (in the check run) and never worked" case — `check_missing_quality` already retries 3 times per stream, so by the time culling runs, the stream has had its chance.

**Rule 2 — Not worked recently + not scraped in 3 days:**

- `last_scraped_time` is older than 3 days AND
- `last_quality_success_time` is `None` or older than 3 days
- This is for streams that once worked but have gone stale.

Update thresholds:

- `_CHECK_LAST_SCRAPE_THRESHOLD` → remove (now two separate thresholds)
- Add `_CULL_NEVER_WORKED_SCRAPE_THRESHOLD = timedelta(days=1)`
- Keep `_CHECK_LAST_WORKED_THRESHOLD = timedelta(days=3)` (rename to `_CULL_STALE_SCRAPE_THRESHOLD`)

Update log messages to accurately describe which rule triggered the cull.

### 3. Fix existing log message inconsistency

The current log says "not scraped in 1 day" but the threshold is 3 days. The new messages will be accurate.

## Files touched

- `acere/database/handlers/quality_cache.py` — all changes are in this one file
