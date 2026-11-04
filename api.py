import sqlite3
import os
from functools import wraps
from unidecode import unidecode

try:
    from .db.utils import create_db_search_key, normalize_repeated_chars, replace_invalid_chars
except ImportError:
    from db.utils import create_db_search_key, normalize_repeated_chars, replace_invalid_chars

DB_PATH = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), 'db', 'roms.db')


def get_valid_search_key(search_key):
    """Process a user search string before passing it to the API search."""
    search_key = replace_invalid_chars(search_key)
    search_key = unidecode(search_key)
    return normalize_repeated_chars(search_key, ' ')


def prepare_search_key(search_key):
    """Make the given string safe for use in a SQL MATCH operator and apply prefix matching."""
    words = search_key.split()
    if not words:
        return ''

    escaped_words = [word.replace('"', '""') for word in words]

    quoted_words = [f'"{word}"' for word in escaped_words[:-1]
                    ] + [f'"{escaped_words[-1]}"*']
    spaced_query = ' '.join(quoted_words)

    if len(words) > 1:
        solid_word = ''.join(escaped_words)
        return f'({spaced_query}) OR "{solid_word}"*'

    return spaced_query


def with_db(func):
    """Decorator that provides a read-only database connection and cursor to a function."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        """Open a read-only database connection for the wrapped function."""
        conn = None
        cursor = None
        try:
            conn = sqlite3.connect(
                f'file:{DB_PATH}?mode=ro', uri=True, timeout=5)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            result = func(cursor, *args, **kwargs)
        finally:
            cursor.close()
            conn.close()
        return result
    return wrapper


def build_response(info=None, data=None):
    """Build the universal response structure used in the API."""
    return {
        'info': info or {},
        'data': data or {}
    }


def build_link(cursor, row):
    """Convert a link row into the public link structure."""
    cursor.execute('''
        SELECT extra FROM extras_links
        WHERE link = ?
    ''', (row['id'],))
    extras = [extra[0] for extra in cursor.fetchall()]

    link = {
        'type': row['type'],
        'extras': extras,
        'format': row['format'],
        'filename': row['filename'],
        'url': row['url'],
        'size': row['size'],
        'size_str': row['size_str'],
        'source_name': row['source_name'],
        'source_url': row['source_url']
    }

    return link


def build_entry(cursor, row):
    """Convert an entry row into the public entry structure."""
    cursor.execute('''
        SELECT region FROM regions_entries
        WHERE entry = ?
    ''', (row['slug'],))
    regions = [region[0] for region in cursor.fetchall()]

    cursor.execute('''
        SELECT *
        FROM links
        WHERE entry = ?
    ''', (row['slug'],))
    links = []
    for link_row in cursor.fetchall():
        links.append(build_link(cursor, link_row))

    entry = {
        'slug': row['slug'],
        'title': row['title'],
        'platform': row['platform'],
        'regions': regions,
        'serial': row['serial'],
        'cover_url': row['cover_url'],
        'links': links
    }
    return entry


def handle_exception(func):
    """Decorator that handles exceptions for all API endpoints."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        """Return a standard error response when the wrapped function fails."""
        try:
            return func(*args, **kwargs)
        except sqlite3.OperationalError:
            return build_response({'error': "Database operation failed"})
        except sqlite3.DatabaseError:
            return build_response({'error': "A database error occurred"})
        except ValueError:
            return build_response({'error': "Invalid input provided"})
        except Exception:
            return build_response({'error': "An unexpected error occurred"})
    return wrapper


@handle_exception
@with_db
def get_search(
    cursor,
    search_key=None,
    platforms=None,
    regions=None,
    serial=None,
    max_results=100,
    page=1
):
    """Perform a search using given filters."""
    platforms = platforms or []
    regions = regions or []
    max_results = max(1, min(max_results, 100))
    page = max(1, page)

    base_query = '''
    SELECT DISTINCT *
    FROM entries e
    '''
    where_clauses = []
    params = []

    if search_key:
        valid_search_key = get_valid_search_key(search_key)
        prepared_search_key = prepare_search_key(valid_search_key)
        base_query += ' JOIN entries_fts fts ON fts.rowid = e.rowid '
        where_clauses.append('fts.search_key MATCH ?')
        params.append(prepared_search_key)

    if platforms:
        placeholders = ','.join(['?' for _ in platforms])
        where_clauses.append(f'e.platform IN ({placeholders})')
        params.extend(platforms)

    if regions:
        base_query += 'LEFT JOIN regions_entries re ON re.entry = e.slug'
        where_clauses.append('(re.region IN ({}) OR re.region IS NULL)'.format(
            ','.join(['?' for _ in regions])
        ))
        params.extend(regions)

    if serial:
        where_clauses.append('e.serial = ?')
        params.append(serial)

    if where_clauses:
        base_query += ' WHERE ' + ' AND '.join(where_clauses)

    count_query = f'SELECT COUNT(*) FROM ({base_query})'
    cursor.execute(count_query, params)
    total_results = cursor.fetchone()[0]

    total_pages = (total_results + max_results -
                   1) // max_results if max_results > 0 else 1
    page = min(page, total_pages)
    offset = (page - 1) * max_results

    if search_key:
        search_match_key = create_db_search_key(valid_search_key)
        final_query = base_query + \
            ' ORDER BY CASE WHEN e.search_key = ? THEN 0 WHEN e.search_key LIKE ? THEN 1 ELSE 2 END, length(e.search_key), fts.rank LIMIT ? OFFSET ?'
        params_with_pagination = params + \
            [search_match_key, f'{search_match_key}%', max_results, offset]
    else:
        final_query = base_query + ' LIMIT ? OFFSET ?'
        params_with_pagination = params + [max_results, offset]

    cursor.execute(final_query, params_with_pagination)
    results = []

    for row in cursor.fetchall():
        results.append(build_entry(cursor, row))

    return build_response(
        {},
        {
            'results': results,
            'current_results': len(results),
            'total_results': total_results,
            'current_page': page,
            'total_pages': total_pages
        }
    )


@handle_exception
@with_db
def get_entry(cursor, slug=None, random=False):
    """Select an entry directly by its slug or get a random entry."""
    if random:
        cursor.execute('''
            SELECT *
            FROM entries
            ORDER BY RANDOM()
            LIMIT 1
        ''')
        row = cursor.fetchone()
    else:
        if not slug:
            return build_response({'error': 'Slug is required'})
        cursor.execute('''
            SELECT *
            FROM entries
            WHERE slug = ?
        ''', (slug,))
        row = cursor.fetchone()
        if not row:
            return build_response({'error': 'Entry not found'})
    entry = build_entry(cursor, row)

    return build_response({}, {'entry': entry})


@handle_exception
@with_db
def get_platforms(cursor):
    """Get the available platforms in the database."""
    cursor.execute('''
        SELECT *
        FROM platforms
    ''')
    platforms = {id: {'class': platform_class, 'brand': brand, 'name': name}
                 for id, platform_class, brand, name in cursor.fetchall()}
    return build_response({}, {'platforms': platforms})


@handle_exception
@with_db
def get_regions(cursor):
    """Get the available regions in the database."""
    cursor.execute('''
        SELECT *
        FROM regions
    ''')
    regions = {id: name for id, name in cursor.fetchall()}
    return build_response({}, {'regions': regions})


@handle_exception
@with_db
def get_info(cursor):
    """Get information on the current state of the database."""
    cursor.execute('SELECT COUNT(*) FROM entries')
    total_entries = cursor.fetchone()[0]
    return build_response({}, {'total_entries': total_entries})
