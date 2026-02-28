import os
import sqlite3
import tempfile

import pytest

from refractivesqlite.database import Database


def _make_minimal_db(path):
    """Create a minimal in-memory sqlite db matching the schema."""
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute(
        'CREATE TABLE pages '
        '(pageid int, shelf text, book text, page text, filepath text, '
        'hasrefractive integer, hasextinction integer, '
        'rangeMin real, rangeMax real, points int)'
    )
    c.execute(
        'CREATE TABLE refractiveindex (pageid int, wave real, refindex real)'
    )
    c.execute('CREATE TABLE extcoeff (pageid int, wave real, coeff real)')
    c.execute(
        'INSERT INTO pages VALUES (1,"main","Ag","Johnson","main/Ag/Johnson.yml",1,1,0.3,1.0,10)'
    )
    for i, w in enumerate([0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]):
        c.execute('INSERT INTO refractiveindex VALUES (1,?,?)', (w, 1.5 - i*0.05))
        c.execute('INSERT INTO extcoeff VALUES (1,?,?)', (w, 0.01 + i*0.001))
    conn.commit()
    conn.close()


@pytest.fixture
def db_path(tmp_path):
    p = str(tmp_path / "test.db")
    _make_minimal_db(p)
    return p


class TestDatabase:
    def test_init_found(self, db_path):
        db = Database(db_path)
        assert db.db_path == db_path

    def test_init_not_found(self, tmp_path):
        db = Database(str(tmp_path / "missing.db"))
        assert db.db_path is not None

    def test_search_custom_returns_results(self, db_path):
        db = Database(db_path)
        results = db.search_custom("SELECT * FROM pages")
        assert len(results) == 1

    def test_search_custom_no_results(self, db_path):
        db = Database(db_path)
        results = db.search_custom("SELECT * FROM pages WHERE shelf='nonexistent'")
        assert results == []

    def test_get_material_returns_material(self, db_path):
        db = Database(db_path)
        mat = db.get_material(1)
        assert mat is not None
        assert mat.has_refractive()
        assert mat.has_extinction()

    def test_get_material_not_found(self, db_path):
        db = Database(db_path)
        mat = db.get_material(9999)
        assert mat is None

    def test_get_material_n_numpy(self, db_path):
        db = Database(db_path)
        arr = db.get_material_n_numpy(1)
        assert arr is not None
        assert arr.shape[1] == 2

    def test_get_material_k_numpy(self, db_path):
        db = Database(db_path)
        arr = db.get_material_k_numpy(1)
        assert arr is not None
        assert arr.shape[1] == 2
