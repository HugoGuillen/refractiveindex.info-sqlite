import math

import numpy
import pytest

from refractivesqlite.optical_data import (
    FormulaRefractiveIndexData,
    TabulatedRefractiveIndexData,
    ExtinctionCoefficientData,
    RefractiveIndexData,
)


class TestRefractiveIndexDataFactory:
    def test_formula_dispatch(self):
        data = RefractiveIndexData.SetupRefractiveIndex(
            formula=1,
            rangeMin=0.3,
            rangeMax=1.0,
            coefficients=[0, 1.0, 0.1],
            interpolation_points=10,
        )
        assert isinstance(data, FormulaRefractiveIndexData)

    def test_tabulated_dispatch(self):
        data = RefractiveIndexData.SetupRefractiveIndex(
            formula=-1,
            wavelengths=[0.3, 0.5, 1.0],
            values=[1.5, 1.4, 1.3],
        )
        assert isinstance(data, TabulatedRefractiveIndexData)

    def test_bad_formula_raises(self):
        with pytest.raises(Exception):
            RefractiveIndexData.SetupRefractiveIndex(formula=-2)


class TestTabulatedRefractiveIndexData:
    def setup_method(self):
        self.wavelengths = [0.3, 0.5, 0.7, 1.0]
        self.values = [1.6, 1.5, 1.4, 1.3]
        self.data = TabulatedRefractiveIndexData(self.wavelengths, self.values)

    def test_range(self):
        assert self.data.rangeMin == 0.3
        assert self.data.rangeMax == 1.0

    def test_get_refractiveindex_in_range(self):
        # 500 nm = 0.5 um
        n = self.data.get_refractiveindex(500)
        assert 1.3 < n < 1.6

    def test_get_refractiveindex_out_of_range_returns_nan(self):
        n = self.data.get_refractiveindex(2000)
        assert math.isnan(n)

    def test_get_refractiveindex_array_input(self):
        wls = numpy.array([300, 500, 700, 1000])
        result = self.data.get_refractiveindex(wls)
        assert result.shape == (4,)
        assert not numpy.any(numpy.isnan(result))

    def test_get_refractiveindex_array_partial_nan(self):
        wls = numpy.array([300, 500, 2000])
        result = self.data.get_refractiveindex(wls)
        assert not numpy.isnan(result[0])
        assert not numpy.isnan(result[1])
        assert numpy.isnan(result[2])

    def test_get_complete_refractive(self):
        result = self.data.get_complete_refractive()
        assert len(result) == len(self.wavelengths)
        assert result[0] == [self.wavelengths[0], self.values[0]]

    def test_from_lists(self):
        data = TabulatedRefractiveIndexData.FromLists(
            self.wavelengths, self.values
        )
        assert isinstance(data, TabulatedRefractiveIndexData)


class TestExtinctionCoefficientData:
    def setup_method(self):
        self.wavelengths = [0.3, 0.5, 0.7, 1.0]
        self.coefficients = [0.01, 0.02, 0.015, 0.005]
        self.data = ExtinctionCoefficientData(self.wavelengths,
                                              self.coefficients)

    def test_range(self):
        assert self.data.rangeMin == 0.3
        assert self.data.rangeMax == 1.0

    def test_get_extinction_in_range(self):
        k = self.data.get_extinction_coefficient(500)
        assert 0.0 < k < 0.05

    def test_get_extinction_out_of_range_returns_nan(self):
        k = self.data.get_extinction_coefficient(2000)
        assert math.isnan(k)

    def test_get_extinction_array_input(self):
        wls = numpy.array([300, 500, 700, 1000])
        result = self.data.get_extinction_coefficient(wls)
        assert result.shape == (4,)
        assert not numpy.any(numpy.isnan(result))

    def test_get_complete_extinction(self):
        result = self.data.get_complete_extinction()
        assert len(result) == len(self.wavelengths)


class TestFormulaRefractiveIndexData:
    def _make_sellmeier(self):
        # BK7 glass Sellmeier coefficients (formula 1)
        return FormulaRefractiveIndexData(
            formula=1,
            rangeMin=0.3,
            rangeMax=2.5,
            coefficients=[0, 1.03961212, 0.00600069867,
                          0.231792344, 0.0200179144,
                          1.01046945, 103.560653],
            interpolation_points=50,
        )

    def test_get_refractiveindex_in_range(self):
        data = self._make_sellmeier()
        n = data.get_refractiveindex(589)  # 589 nm
        assert 1.4 < n < 1.6

    def test_get_refractiveindex_out_of_range_returns_nan(self):
        data = self._make_sellmeier()
        n = data.get_refractiveindex(100)  # 100 nm, below rangeMin
        assert math.isnan(n)

    def test_get_refractiveindex_array_input(self):
        data = self._make_sellmeier()
        wls = numpy.array([400, 500, 600, 700])  # nm
        result = data.get_refractiveindex(wls)
        assert result.shape == (4,)
        assert not numpy.any(numpy.isnan(result))

    def test_get_refractiveindex_array_partial_nan(self):
        data = self._make_sellmeier()
        wls = numpy.array([100, 589, 3000])  # nm — first and last out of range
        result = data.get_refractiveindex(wls)
        assert numpy.isnan(result[0])
        assert not numpy.isnan(result[1])
        assert numpy.isnan(result[2])

    def test_get_complete_refractive_length(self):
        data = self._make_sellmeier()
        result = data.get_complete_refractive()
        assert len(result) == 50

    def test_formula4_correctness(self):
        # TiO2 (anatase) — formula 4 from refractiveindex.info
        # Coefficients from Devore (1951), valid 0.43–1.53 um
        data = FormulaRefractiveIndexData(
            formula=4,
            rangeMin=0.43,
            rangeMax=1.53,
            coefficients=[
                5.913, 0.2441, 0.0803, 0.0, 0.0,
                0.0, 0.0, 0.0, 0.0,
            ],
            interpolation_points=20,
        )
        n = data.get_refractiveindex(600)  # 600 nm
        # TiO2 has n ~ 2.5 in the visible
        assert 2.0 < n < 3.5

    def test_formula4_short_coefficients(self):
        # Ensure formula 4 doesn't crash with fewer than 9 coefficients
        data = FormulaRefractiveIndexData(
            formula=4,
            rangeMin=0.3,
            rangeMax=1.0,
            coefficients=[2.0],  # only C0
            interpolation_points=5,
        )
        n = data.get_refractiveindex(500)
        assert not math.isnan(n)
        assert n == pytest.approx(math.sqrt(2.0), rel=1e-6)
