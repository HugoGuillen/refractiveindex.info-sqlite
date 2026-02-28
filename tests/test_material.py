import pytest

from refractivesqlite.material import Material
from refractivesqlite.exceptions import NoExtinctionCoefficient


class TestMaterialFromLists:
    def _make_n_only(self):
        pageinfo = {'pageid': 1, 'shelf': 'main', 'book': 'Ag', 'page': 'n'}
        return Material.FromLists(
            pageinfo,
            wavelengths_r=[0.3, 0.5, 0.7],
            refractive=[1.5, 1.4, 1.3],
        )

    def _make_k_only(self):
        pageinfo = {'pageid': 2, 'shelf': 'main', 'book': 'Ag', 'page': 'k'}
        return Material.FromLists(
            pageinfo,
            wavelengths_e=[0.3, 0.5, 0.7],
            extinction=[0.01, 0.02, 0.015],
        )

    def _make_nk(self):
        pageinfo = {'pageid': 3, 'shelf': 'main', 'book': 'Ag', 'page': 'nk'}
        return Material.FromLists(
            pageinfo,
            wavelengths_r=[0.3, 0.5, 0.7],
            refractive=[1.5, 1.4, 1.3],
            wavelengths_e=[0.3, 0.5, 0.7],
            extinction=[0.01, 0.02, 0.015],
        )

    def test_has_refractive(self):
        mat = self._make_n_only()
        assert mat.has_refractive()
        assert not mat.has_extinction()

    def test_has_extinction(self):
        mat = self._make_k_only()
        assert mat.has_extinction()
        assert not mat.has_refractive()

    def test_has_both(self):
        mat = self._make_nk()
        assert mat.has_refractive()
        assert mat.has_extinction()

    def test_get_refractiveindex(self):
        mat = self._make_n_only()
        n = mat.get_refractiveindex(500)
        assert 1.3 < n < 1.6

    def test_get_extinctioncoefficient(self):
        mat = self._make_k_only()
        k = mat.get_extinctioncoefficient(500)
        assert 0.0 < k < 0.05

    def test_get_extinctioncoefficient_missing_raises(self):
        mat = self._make_n_only()
        with pytest.raises(NoExtinctionCoefficient):
            mat.get_extinctioncoefficient(500)

    def test_get_page_info(self):
        mat = self._make_n_only()
        info = mat.get_page_info()
        assert info['shelf'] == 'main'

    def test_get_complete_refractive(self):
        mat = self._make_n_only()
        result = mat.get_complete_refractive()
        assert len(result) == 3

    def test_get_complete_extinction(self):
        mat = self._make_k_only()
        result = mat.get_complete_extinction()
        assert len(result) == 3

    def test_range_set_from_refractive(self):
        mat = self._make_n_only()
        assert mat.rangeMin == 0.3
        assert mat.rangeMax == 0.7

    def test_range_set_from_extinction_when_no_refractive(self):
        mat = self._make_k_only()
        assert mat.rangeMin == 0.3
        assert mat.rangeMax == 0.7
