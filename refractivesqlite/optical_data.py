import numpy
import scipy.interpolate


class RefractiveIndexData:
    """Abstract RefractiveIndex class"""

    @staticmethod
    def SetupRefractiveIndex(formula, **kwargs):
        """
        :param formula: An integer value specifying the formula to use.
                        Pass -1 to create tabulated refractive index data.
        :param kwargs: Passed to FormulaRefractiveIndexData or
                       TabulatedRefractiveIndexData.
        :returns: A formula or tabulated refractive index data object.
        :raises Exception:
        """
        if formula >= 0:
            return FormulaRefractiveIndexData(formula, **kwargs)
        elif formula == -1:
            return TabulatedRefractiveIndexData(**kwargs)
        else:
            raise Exception('Bad RefractiveIndex data type')

    def get_refractiveindex(self, wavelength):
        raise NotImplementedError(
            'Different for formula and tabulated materials')


class FormulaRefractiveIndexData:
    """Formula-based refractive index (dispersion formulas 1–9)."""

    def __init__(self, formula, rangeMin, rangeMax, coefficients,
                 interpolation_points):
        self.formula = formula
        self.rangeMin = rangeMin
        self.rangeMax = rangeMax
        self.coefficients = coefficients
        self.interpolation_points = interpolation_points

    def get_complete_refractive(self):
        """Return refractive index over the full wavelength range.

        Returns a list of [wavelength_um, n] pairs of length
        *interpolation_points*.
        """
        wavelength = numpy.linspace(
            self.rangeMin, self.rangeMax, num=self.interpolation_points)
        return [
            [wavelength[i], float(self.get_refractiveindex(wavelength[i] * 1000))]
            for i in range(len(wavelength))
        ]

    def get_refractiveindex(self, wavelength):
        """Return the refractive index at *wavelength* (in nm).

        Accepts scalar or array-like input. Out-of-range values return NaN.

        :param wavelength: Wavelength in nm (scalar or array-like).
        :returns: Refractive index (float or ndarray).
        """
        wl_arr = numpy.asarray(wavelength, dtype=float) / 1000.0  # nm → um
        scalar_input = wl_arr.ndim == 0
        wl_arr = numpy.atleast_1d(wl_arr)

        in_range = (wl_arr >= self.rangeMin) & (wl_arr <= self.rangeMax)
        result = numpy.full(wl_arr.shape, numpy.nan)

        wl = wl_arr[in_range]
        if wl.size == 0:
            return float('nan') if scalar_input else result

        formula_type = self.formula
        C = self.coefficients
        n = numpy.zeros(wl.shape)

        if formula_type == 1:  # Sellmeier
            nsq = 1.0 + C[0]
            for i in range(1, len(C), 2):
                nsq = nsq + C[i] * wl**2 / (wl**2 - C[i + 1]**2)
            n = numpy.sqrt(nsq)

        elif formula_type == 2:  # Sellmeier-2
            nsq = 1.0 + C[0]
            for i in range(1, len(C), 2):
                nsq = nsq + C[i] * wl**2 / (wl**2 - C[i + 1])
            n = numpy.sqrt(nsq)

        elif formula_type == 3:  # Polynomial
            nsq = C[0]
            for i in range(1, len(C), 2):
                nsq = nsq + C[i] * wl**C[i + 1]
            n = numpy.sqrt(nsq)

        elif formula_type == 4:  # RefractiveIndex.INFO
            # Fixed: step-4 loop for Lorentz terms, step-2 for polynomial tail
            # Zero-pad to avoid index errors with short coefficient lists
            padded = list(C) + [0.0] * 20
            nsq = padded[0]
            for i in range(1, min(9, len(C)), 4):
                nsq = nsq + padded[i] * wl**padded[i + 1] / (
                    wl**2 - padded[i + 2]**padded[i + 3])
            for i in range(9, len(C), 2):
                nsq = nsq + padded[i] * wl**padded[i + 1]
            n = numpy.sqrt(nsq)

        elif formula_type == 5:  # Cauchy
            n = C[0]
            for i in range(1, len(C), 2):
                n = n + C[i] * wl**C[i + 1]

        elif formula_type == 6:  # Gases
            n = 1.0 + C[0]
            for i in range(1, len(C), 2):
                n = n + C[i] / (C[i + 1] - wl**(-2))

        elif formula_type == 7:  # Herzberger
            n = C[0]
            n = n + C[1] / (wl**2 - 0.028)
            n = n + C[2] * (1.0 / (wl**2 - 0.028))**2
            for i, cc in enumerate(C[3:]):
                n = n + cc * wl**(2 * (i + 1))

        elif formula_type == 8:  # Retro
            tmp = C[0]
            tmp = tmp + C[1] * wl**2 / (wl**2 - C[2])
            tmp = tmp + C[3] * wl**2
            n = numpy.sqrt(-(2 * tmp + 1) / (tmp - 1))

        elif formula_type == 9:  # Exotic
            tmp = C[0]
            tmp = tmp + C[1] / (wl**2 - C[2])
            tmp = tmp + C[3] * (wl - C[4]) / ((wl - C[4])**2 + C[5])
            n = numpy.sqrt(tmp)

        else:
            raise Exception('Bad formula type: {}'.format(formula_type))

        result[in_range] = n
        return float(result[0]) if scalar_input else result


class TabulatedRefractiveIndexData:
    """Tabulated refractive index with linear interpolation."""

    def __init__(self, wavelengths, values):
        self.rangeMin = float(numpy.min(wavelengths))
        self.rangeMax = float(numpy.max(wavelengths))
        self.wavelengths = wavelengths
        self.coefficients = values

        if self.rangeMin == self.rangeMax:
            _val = float(values[0])
            self.refractiveFunction = lambda x: numpy.full(
                numpy.asarray(x).shape or (), _val)
        else:
            self.refractiveFunction = scipy.interpolate.interp1d(
                wavelengths, values, bounds_error=False,
                fill_value=numpy.nan)

    @staticmethod
    def FromLists(wavelengths, values):
        return TabulatedRefractiveIndexData(wavelengths, values)

    def get_refractiveindex(self, wavelength):
        """Return the refractive index at *wavelength* (nm).

        Accepts scalar or array-like input. Out-of-range values return NaN.
        """
        wl = numpy.asarray(wavelength, dtype=float) / 1000.0  # nm → um
        scalar_input = wl.ndim == 0
        result = self.refractiveFunction(wl)
        if scalar_input:
            return float(result)
        return result

    def get_complete_refractive(self):
        return [
            [self.wavelengths[i], self.coefficients[i]]
            for i in range(len(self.wavelengths))
        ]


class ExtinctionCoefficientData:
    """Tabulated extinction coefficient with linear interpolation."""

    @staticmethod
    def SetupExtinctionCoefficient(wavelengths, values):
        return ExtinctionCoefficientData(wavelengths, values)

    @staticmethod
    def FromLists(wavelengths, values):
        return ExtinctionCoefficientData(wavelengths, values)

    def __init__(self, wavelengths, coefficients):
        self.rangeMin = float(numpy.min(wavelengths))
        self.rangeMax = float(numpy.max(wavelengths))
        self.wavelengths = wavelengths
        self.coefficients = coefficients
        self.extCoeffFunction = scipy.interpolate.interp1d(
            wavelengths, coefficients, bounds_error=False,
            fill_value=numpy.nan)

    def get_extinction_coefficient(self, wavelength):
        """Return the extinction coefficient at *wavelength* (nm).

        Accepts scalar or array-like input. Out-of-range values return NaN.
        """
        wl = numpy.asarray(wavelength, dtype=float) / 1000.0  # nm → um
        scalar_input = wl.ndim == 0
        result = self.extCoeffFunction(wl)
        if scalar_input:
            return float(result)
        return result

    def get_complete_extinction(self):
        return [
            [self.wavelengths[i], self.coefficients[i]]
            for i in range(len(self.wavelengths))
        ]
