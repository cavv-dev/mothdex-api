# Migrating from Crocdb API to Mothdex API

This guide covers the breaking changes and key differences when upgrading from the legacy Crocdb API to the Mothdex API (`v1`). For complete endpoint details and examples, see [Public HTTP API docs](https://mothdex.net/api-docs/).

## Base URL

The API base URL has changed and is now versioned:

- **Old:** `https://api.crocdb.net`
- **New:** `https://api.mothdex.net/v1`

## Schema and fields changes

### Entry object (`/search`, `/entry`, `/entry/random`)
- `rom_id` $\rightarrow$ **`serial`** (also applies to the `/search` request filter)
- `boxart_url` $\rightarrow$ **`cover_url`**

### Link object (`links` in `entry`)
- `name` has been removed (use `filename` and/or `extras` instead).
- `host` $\rightarrow$ **`source_name`**
- **New field:** `extras` (an array of strings containing revisions, languages, or metadata tags).

### Platform object (`/platforms`)
- **New field:** `class` (broad platform category, e.g. `"Home consoles"`).

## Endpoint changes

- **`/entry/random`:** Now only accepts `POST` requests (previously supported `GET` and `POST`). It now accepts optional JSON filter parameters (`search_key`, `platforms`, `regions`, `serial`) or an empty `{}` body.

## Error handling

Some application-level errors (such as a missing entry) now return an HTTP `200` status code while populating `error` in `info`. Always check both the HTTP status code and the `error` field when handling responses.
