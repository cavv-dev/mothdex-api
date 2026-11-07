# Mothdex API

The Mothdex API provides read-only access to the Mothdex ROM database through HTTP/JSON requests. Authentication is not required.

Base URL: `https://api.mothdex.net/v1`

## Index

- [Response format](#response-format)
- [Data fields](#data-fields)
    - [Entry](#entry)
    - [Link](#link)
- [Endpoints](#endpoints)
    - [Search entries](#search-entries)
    - [Get entry](#get-entry)
    - [Get random entry](#get-random-entry)
    - [List platforms](#list-platforms)
    - [List regions](#list-regions)
    - [Database information](#database-information)
- [Status codes](#status-codes)
- [Limits and CORS](#limits-and-cors)

## Response format

Every response uses the same top-level JSON object:

```json
{
  "info": {},
  "data": {}
}
```

`data` contains the actual data returned by the endpoint.

`info` is normally empty. It may contain an `error` message when the API reports an error.

Some application-level errors, such as a missing entry, keep the HTTP response successful (see [Status codes](#status-codes)) but put the error in `info`; always check both the HTTP status and the presence of `error` in `info`.

## Data fields

### Entry

An entry describes one database item:

| Field | Type | Description |
|---|---|---|
| `slug` | string | Stable identifier used with `/entry`. |
| `title` | string | Entry title. |
| `platform` | string | Platform identifier, such as `snes` or `gba`. See [`/platforms`](#list-platforms). |
| `regions` | array of strings | Region identifiers associated with the entry. See [`/regions`](#list-regions). |
| `serial` | string | Platform serial or catalog identifier, when available. |
| `cover_url` | string | URL of the cover artwork, when available. |
| `links` | array of links (see [Link](#link)) | Download links associated with the entry. |

### Link

Each object in `links` contains:

| Field | Type | Description |
|---|---|---|
| `type` | string | Link category, for example `Game`. |
| `extras` | array of strings | Additional languages, revisions, or other source metadata. |
| `format` | string | File or content format, such as `gba` or `bin+cue`. |
| `filename` | string | Name of the downloaded file. |
| `url` | string | Direct URL used to access the file. |
| `size` | integer | File size in bytes. |
| `size_str` | string | Human-readable file size. |
| `source_name` | string | Name of the source. |
| `source_url` | string | URL of the source collection or page. |

## Endpoints

### Search entries

Searches entries with optional filters.

#### `/search` `POST`

Request body:

| Field | Type | Required | Description |
|---|---|---|---|
| `search_key` | string | No | Case-insensitive text search applied to the title. It does not need to be an exact match: partial matches and substrings are supported. |
| `platforms` | array of strings | No | Platform identifiers to include, such as `["snes", "gba"]`. |
| `regions` | array of strings | No | Region identifiers to include, such as `["us", "jp"]`. |
| `serial` | string | No | Exact ROM serial filter. |
| `max_results` | integer | No | Results per page. Default: `100`. Max: `100`. |
| `page` | integer | No | Page number, starting at `1`. Defaults to `1`. |

All fields are optional. An empty body (`{}`) is valid and returns the first page of entries.

Example request body:

```json
{
  "search_key": "doom",
  "platforms": ["dos"],
  "regions": ["eu", "us"],
  "max_results": 10,
  "page": 1
}
```

Example response:

```json
{
  "info": {},
  "data": {
    "results": [
      {
        "slug": "doom-1993-dos",
        "title": "DOOM (1993)",
        "platform": "dos",
        "regions": [],
        "serial": null,
        "cover_url": "https://images.igdb.com/igdb/image/upload/t_cover_big/co5rav.jpg",
        "links": [
          {
            "type": "Game",
            "extras": [
              "Installer",
              "SW"
            ],
            "format": "exe",
            "filename": "DOOM (Installer) [SW] (1993)(id Software, Inc.) [Action].zip",
            "url": "https://proxy.mothdex.net/file/54OLVmcrle",
            "size": 2164841,
            "size_str": "2.06M",
            "source_name": "MiNERVA Archive",
            "source_url": "https://minerva-archive.org/browse/Total%20DOS%20Collection/Games/Files/"
          },
          {
            "type": "Game",
            "extras": [
              "SW"
            ],
            "format": "exe",
            "filename": "DOOM [SW] (1993)(id Software, Inc.) [Action].zip",
            "url": "https://proxy.mothdex.net/file/lCgkhaYQBb",
            "size": 2079973,
            "size_str": "1.98M",
            "source_name": "MiNERVA Archive",
            "source_url": "https://minerva-archive.org/browse/Total%20DOS%20Collection/Games/Files/"
          },
          {
            "type": "Game",
            "extras": [
              "v0.2",
              "Alpha"
            ],
            "format": "exe",
            "filename": "DOOM v0.2 Alpha (1993)(id Software, Inc.) [Action].zip",
            "url": "https://proxy.mothdex.net/file/0s0VD811fj",
            "size": 261558,
            "size_str": "255.43K",
            "source_name": "MiNERVA Archive",
            "source_url": "https://minerva-archive.org/browse/Total%20DOS%20Collection/Games/Files/"
          },
          ...
        ]
      },
      ...
    ],
    "current_results": 10,
    "total_results": 68,
    "current_page": 1,
    "total_pages": 7
  }
}
```

Returned fields:

| Field | Type | Description |
|---|---|---|
| `results` | array of entries (see [Entry](#entry)) | Entries returned for this page. |
| `current_results` | integer | Number of entries in `results`. |
| `total_results` | integer | Total number of entries. |
| `current_page` | integer | Current page number. |
| `total_pages` | integer | Number of available pages. |

If `page` is greater than the last page, the last page is returned. Values below `1` are treated as page `1`.

### Get entry

#### `/entry` `POST`

Example request body:

```json
{
  "slug": "phoenix-wright-ace-attorney-nds-eu"
}
```

Example response:

```json
{
  "info": {},
  "data": {
    "entry": {
      "slug": "phoenix-wright-ace-attorney-nds-eu",
      "title": "Phoenix Wright - Ace Attorney",
      "platform": "nds",
      "regions": [
        "eu"
      ],
      "serial": "AGYP",
      "cover_url": "https://art.gametdb.com/ds/coverS/EN/AGYP.png",
      "links": [
        {
          "type": "Game",
          "extras": [
            "De,Es,It"
          ],
          "format": "nds",
          "filename": "Phoenix Wright - Ace Attorney (Europe) (De,Es,It).zip",
          "url": "https://proxy.mothdex.net/file/7CxnfZ2zNY",
          "size": 41522301,
          "size_str": "39.6M",
          "source_name": "MiNERVA Archive",
          "source_url": "https://minerva-archive.org/browse/No-Intro/Nintendo%20-%20Nintendo%20DS%20%28Decrypted%29/"
        },
        {
          "type": "Game",
          "extras": [
            "En,Fr"
          ],
          "format": "nds",
          "filename": "Phoenix Wright - Ace Attorney (Europe) (En,Fr).zip",
          "url": "https://proxy.mothdex.net/file/niCy6IfrPe",
          "size": 39948392,
          "size_str": "38.1M",
          "source_name": "MiNERVA Archive",
          "source_url": "https://minerva-archive.org/browse/No-Intro/Nintendo%20-%20Nintendo%20DS%20%28Decrypted%29/"
        },
        ...
      ]
    }
  }
}
```

### Get random entry

#### `/entry/random` `POST`

Returns one randomly selected entry matching the optional filters. The filter
fields are the same as [`/search`](#search-entries), limited to
`search_key`, `platforms`, `regions`, and `serial`.

Provide the filters as a JSON request body. An empty body (`{}`) is valid:

```json
{
  "search_key": "mario",
  "platforms": ["snes", "gba"],
  "regions": ["us", "jp"]
}
```

The response has the same shape as [`/entry`](#get-entry).

### List platforms

#### `/platforms` `GET` `POST`

No request body is required.

Example response:

```json
{
  "info": {},
  "data": {
    "platforms": {
      "nes": {
        "class": "Home consoles",
        "brand": "Nintendo",
        "name": "Nintendo Entertainment System"
      },
      "fds": {
        "class": "Home consoles",
        "brand": "Nintendo",
        "name": "Famicom Disk System"
      },
      "snes": {
        "class": "Home consoles",
        "brand": "Nintendo",
        "name": "Super Nintendo Entertainment System"
      },
      ...
    }
  }
}
```

The `platforms` object maps each platform identifier, such as `nes`, `fds`, or `snes`.

Each platform value contains `class` (the broad platform category), `brand` (the manufacturer or platform brand), and `name` (the full human-readable platform name).

Use the identifier as a value in the `platforms` search filter and as the `platform` value returned on an entry.

### List regions

#### `/regions` `GET` `POST`

No request body is required.

Example response:

```json
{
  "info": {},
  "data": {
    "regions": {
      "eu": "Europe",
      "us": "USA",
      "jp": "Japan",
      "other": "Other"
    }
  }
}
```

The `regions` object maps each region identifier, such as `eu`, `us`, `jp`, or `other`, to its human-readable name.

Use the identifier as a value in the `regions` search filter and as a value in an entry's `regions` array.

### Database information

#### `/info` `GET` `POST`

No request body is required.

Example response:

```json
{
  "info": {},
  "data": {
    "total_entries": 346298
  }
}
```

`total_entries` is the current number of entries in the database and may change as the database is updated.

## Status codes

Common HTTP statuses:

| Status | Meaning |
|---|---|
| `200` | Request completed. Always check `error` in `info` for application-level errors. |
| `400` | Invalid API version, malformed JSON, or invalid/missing request fields. |
| `404` | The requested route does not exist. |
| `429` | Rate limit exceeded. |
| `500` | Unexpected server error. |

## Limits and CORS

- Requests are subject to rate limits. Please use the API responsibly and do not abuse it.
- CORS is enabled for all origins (`Access-Control-Allow-Origin: *`).
