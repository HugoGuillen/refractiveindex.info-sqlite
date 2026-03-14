import os
import sqlite3

try:
    from yaml import CSafeLoader as _YamlLoader
except ImportError:
    from yaml import SafeLoader as _YamlLoader
import yaml

from refractivesqlite.models import Shelf, Book, Page, Entry
from refractivesqlite import material as material_module

# Module-level cache so repeated calls with the same path skip I/O
_catalog_cache = {}


def _find_catalog_file(db_path):
    """Locate the catalog YAML file in *db_path*.

    Newer databases (>= 2025) use ``catalog-nk.yml``; older ones use
    ``library.yml``.  Returns the full path to whichever is found.

    :raises FileNotFoundError: If neither file exists.
    """
    for name in ('catalog-nk.yml', 'library.yml'):
        path = os.path.join(db_path, name)
        if os.path.isfile(path):
            return path
    raise FileNotFoundError(
        'No catalog file found in {}. '
        'Expected catalog-nk.yml or library.yml.'.format(db_path))


def extract_entry_list(db_path):
    """Return a list of :class:`~refractivesqlite.models.Entry` objects
    parsed from the catalog file in *db_path*.

    Supports both ``catalog-nk.yml`` (>= 2025) and ``library.yml``
    (legacy).  Results are cached per normalised path so that the YAML
    file is read at most once per process.
    """
    entries = []
    referencePath = os.path.normpath(db_path)

    if referencePath in _catalog_cache:
        catalog = _catalog_cache[referencePath]
    else:
        catalog_path = _find_catalog_file(referencePath)
        with open(catalog_path, 'r') as f:
            catalog = yaml.load(f, Loader=_YamlLoader)
        _catalog_cache[referencePath] = catalog

    idx = 0
    for sh in catalog:
        if 'DIVIDER' in sh or 'SHELF' not in sh:
            continue
        shelf = Shelf(sh['SHELF'], sh['name'])
        for b in sh['content']:
            if 'DIVIDER' not in b:
                book = Book(b['BOOK'], b['name'])
                for p in b['content']:
                    if 'DIVIDER' not in p:
                        page = Page(
                            p['PAGE'],
                            p['name'],
                            os.path.join(referencePath, 'data',
                                         os.path.normpath(p['data'])))
                        entries.append(Entry(str(idx), shelf, book, page))
                        idx += 1
    return entries


def pretty_entry(entry):
    e = entry
    return ','.join([e.id, e.shelf.shelf, e.book.book, e.page.page])


def print_pretty_entry_list(entries):
    for e in entries:
        print(pretty_entry(e))


def create_sqlite_database(refractiveindex_db_path,
                           new_sqlite_db,
                           interpolation_points=100):
    """Create a new SQLite database with ``pages``, ``refractiveindex`` and
    ``extcoeff`` tables populated from the refractiveindex.info YML data.

    :param refractiveindex_db_path: Path to the refractiveindex.info data dir.
    :param new_sqlite_db: Destination path for the SQLite file.
    :param interpolation_points: Interpolation points for formula materials.
    """
    conn = sqlite3.connect(new_sqlite_db)
    c = conn.cursor()
    c.execute('DROP TABLE IF EXISTS pages;')
    c.execute('DROP TABLE IF EXISTS refractiveindex;')
    c.execute('DROP TABLE IF EXISTS extcoeff;')
    c.execute(
        'CREATE TABLE pages'
        '(pageid int, shelf text COLLATE NOCASE,'
        'book text COLLATE NOCASE, page text COLLATE NOCASE,'
        'filepath text COLLATE NOCASE,'
        'hasrefractive integer, hasextinction integer,'
        'rangeMin real, rangeMax real, points int)')
    c.execute(
        'CREATE TABLE refractiveindex'
        '(pageid int, wave real, refindex real)')
    c.execute('CREATE TABLE extcoeff (pageid int, wave real, coeff real)')
    conn.commit()
    conn.close()
    _populate_sqlite_database(refractiveindex_db_path,
                              new_sqlite_db,
                              interpolation_points=interpolation_points)


def _populate_sqlite_database(refractiveindex_db_path,
                              new_sqlite_db,
                              interpolation_points=100):
    """Insert material data into an existing SQLite database."""
    entries = extract_entry_list(refractiveindex_db_path)
    conn = sqlite3.connect(new_sqlite_db)
    c = conn.cursor()
    for e in entries:
        try:
            mat = material_module.Material(
                filename=e.page.path,
                interpolation_points=interpolation_points)
            hasrefractive = 0
            hasextinction = 0
            if mat.has_refractive():
                refr = mat.get_complete_refractive()
                hasrefractive = 1
                values = [[e.id, r[0], r[1]] for r in refr]
                c.executemany(
                    'INSERT INTO refractiveindex VALUES (?,?,?)', values)
            if mat.has_extinction():
                ext = mat.get_complete_extinction()
                hasextinction = 1
                values = [[e.id, ex[0], ex[1]] for ex in ext]
                c.executemany('INSERT INTO extcoeff VALUES (?,?,?)', values)
            c.execute(
                'INSERT INTO pages VALUES (?,?,?,?,?,?,?,?,?,?)',
                [e.id,
                 e.shelf.shelf,
                 e.book.book,
                 e.page.page,
                 os.sep.join(e.page.path.split(os.sep)[-3:]),
                 hasrefractive,
                 hasextinction,
                 mat.rangeMin,
                 mat.rangeMax,
                 mat.points])
        except Exception as error:
            print('LOG:', pretty_entry(e), ':', error)
    conn.commit()
    conn.close()
    print('***Wrote SQLite DB on', new_sqlite_db)
