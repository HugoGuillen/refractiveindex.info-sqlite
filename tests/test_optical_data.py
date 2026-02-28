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
        # wavelength arg is in nm; 500 nm = 0.5 um
        n = self.data.get_refractiveindex(500)
        assert 1.3 < n < 1.6

    def test_get_refractiveindex_out_of_range(self):
        with pytest.raises(Exception, match="out of bounds"):
            self.data.get_refractiveindex(2000)

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

    def test_get_extinction_out_of_range(self):
        with pytest.raises(Exception, match="out of bounds"):
            self.data.get_extinction_coefficient(2000)

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
        n = data.get_refractiveindex(589000)  # 589 um in nm
        assert 1.4 < n < 1.6

    def test_get_refractiveindex_out_of_range(self):
        data = self._make_sellmeier()
        with pytest.raises(Exception, match="out of bounds"):
            data.get_refractiveindex(100)

    def test_get_complete_refractive_length(self):
        data = self._make_sellmeier()
        result = data.get_complete_refractive()
        assert len(result) == 50
