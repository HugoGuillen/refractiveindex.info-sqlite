import math

import numpy
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

    def test_get_refractiveindex_default_unit(self):
        mat = self._make_n_only()
        n = mat.get_refractiveindex(500)  # nm
        assert 1.3 < n < 1.6

    def test_get_refractiveindex_um_unit(self):
        mat = self._make_n_only()
        n = mat.get_refractiveindex(0.5, unit='um')  # 0.5 um = 500 nm
        assert 1.3 < n < 1.6

    def test_get_refractiveindex_eV_unit(self):
        mat = self._make_n_only()
        # 500 nm ↔ ~2.48 eV
        n = mat.get_refractiveindex(2.48, unit='eV')
        assert 1.3 < n < 1.6

    def test_get_refractiveindex_array_input(self):
        mat = self._make_n_only()
        wls = numpy.array([300, 500, 700])  # nm
        result = mat.get_refractiveindex(wls)
        assert result.shape == (3,)
        assert not numpy.any(numpy.isnan(result))

    def test_get_extinctioncoefficient_default_unit(self):
        mat = self._make_k_only()
        k = mat.get_extinctioncoefficient(500)  # nm
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

    # ------------------------------------------------------------------
    # get_epsilon
    # ------------------------------------------------------------------

    def test_get_epsilon_n_only(self):
        mat = self._make_n_only()
        eps = mat.get_epsilon(500)
        # k=0 → eps = n² (real)
        n = mat.get_refractiveindex(500)
        assert abs(eps.real - n ** 2) < 1e-12
        assert abs(eps.imag) < 1e-12

    def test_get_epsilon_nk(self):
        mat = self._make_nk()
        eps = mat.get_epsilon(500)
        n = mat.get_refractiveindex(500)
        k = mat.get_extinctioncoefficient(500)
        expected = (n + 1j * k) ** 2
        assert abs(eps - expected) < 1e-12

    def test_get_epsilon_engineering_convention(self):
        mat = self._make_nk()
        eps = mat.get_epsilon(500, convention='exp_plus_i_omega_t')
        n = mat.get_refractiveindex(500)
        k = mat.get_extinctioncoefficient(500)
        expected = (n - 1j * k) ** 2
        assert abs(eps - expected) < 1e-12

    # ------------------------------------------------------------------
    # get_wl_range
    # ------------------------------------------------------------------

    def test_get_wl_range_nm(self):
        mat = self._make_n_only()
        lo, hi = mat.get_wl_range(unit='nm')
        assert lo == pytest.approx(300.0)
        assert hi == pytest.approx(700.0)

    def test_get_wl_range_um(self):
        mat = self._make_n_only()
        lo, hi = mat.get_wl_range(unit='um')
        assert lo == pytest.approx(0.3)
        assert hi == pytest.approx(0.7)

    def test_get_wl_range_eV(self):
        mat = self._make_n_only()
        lo, hi = mat.get_wl_range(unit='eV')
        # 300 nm → higher eV, 700 nm → lower eV; returned as (min, max)
        assert lo < hi
        assert lo > 0
