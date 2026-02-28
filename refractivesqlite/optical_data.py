import numpy
import scipy.interpolate


class RefractiveIndexData:
    """Abstract RefractiveIndex class"""

    @staticmethod
    def SetupRefractiveIndex(formula, **kwargs):
        """
        :param formula: An integer value specifying the formula to use
                        pass -1 to create a tabulated refractive index data
        :param kwargs: kwargs passed to the FormulaRefractiveIndexData
                       or TabulatedRefractiveIndexData
        :returns: A formula or tabulated refractive index data
        :raises Exception:
        """
        if formula >= 0:
            return FormulaRefractiveIndexData(formula, **kwargs)
        elif formula == -1:
            return TabulatedRefractiveIndexData(**kwargs)
        else:
            raise Exception('Bad RefractiveIndex data type')

    def get_refractiveindex(self, wavelength):
        """
        Not implemented yet

        :param wavelength:
        :raise NotImplementedError:
        """
        raise NotImplementedError('Different for functionally'
                                  'and experimentally defined materials')


class FormulaRefractiveIndexData:
    """Formula RefractiveIndex class"""

    def __init__(self, formula, rangeMin, rangeMax, coefficients,
                 interpolation_points):
        """
        :param formula: An integer value specifying the formula
        :param rangeMin: The lower bound for the wavelength
        :param rangeMax: The upper bound for the wavelength
        :param coefficients: Coefficient to interpolate over
        """
        self.formula = formula
        self.rangeMin = rangeMin
        self.rangeMax = rangeMax
        self.coefficients = coefficients
        self.interpolation_points = interpolation_points

    def get_complete_refractive(self):
        '''
        Get the complete refractive index for the whole wavelength intervall

        :returns: A list of refractive indices over the whole
                  wavelength intervall (len = interpolation_points)
        '''
        wavelength = numpy.linspace(
            self.rangeMin, self.rangeMax, num=self.interpolation_points)
        extlist = [[
            wavelength[i],
            self.get_refractiveindex(wavelength[i] * 1000)]
            for i in range(len(wavelength))]
        return extlist

    def get_refractiveindex(self, wavelength):
        """
        Get the refractive index at a certain wavelength
        using the speficied interpolation formula

        :param wavelength:
        :returns: The interpolated refractive index at wavelength
        :raises Exception:
        """
        wavelength /= 1000.0
        if self.rangeMin <= wavelength <= self.rangeMax:
            formula_type = self.formula
            coefficients = self.coefficients
            n = 0
            if formula_type == 1:  # Sellmeier
                nsq = 1 + coefficients[0]

                def sellmeier(c1, c2, w):
                    return c1 * (w ** 2) / (w ** 2 - c2 ** 2)

                for i in range(1, len(coefficients), 2):
                    nsq += sellmeier(coefficients[i],
                                     coefficients[i + 1],
                                     wavelength)
                n = numpy.sqrt(nsq)
            elif formula_type == 2:  # Sellmeier-2
                nsq = 1 + coefficients[0]

                def sellmeier2(c1, c2, w):
                    return c1 * (w ** 2) / (w ** 2 - c2)
                for i in range(1, len(coefficients), 2):
                    nsq += sellmeier2(coefficients[i],
                                      coefficients[i + 1],
                                      wavelength)
                n = numpy.sqrt(nsq)
            elif formula_type == 3:  # Polynomal
                def polynomial(c1, c2, w):
                    return c1 * w ** c2
                nsq = coefficients[0]
                for i in range(1, len(coefficients), 2):
                    nsq += polynomial(coefficients[i],
                                      coefficients[i + 1],
                                      wavelength)
                n = numpy.sqrt(nsq)
            elif formula_type == 4:  # RefractiveIndex.INFO
                def riinfo(wl, ci, cj, ck, cl):
                    return ci * wl**cj / (wl**2 - ck**cl)
                n = coefficients[0]
                n += riinfo(wavelength, *coefficients[1:5])
                n += riinfo(wavelength, *coefficients[5:9])
                for kk in range(len(coefficients[9:]) // 2):
                    n += coefficients[9+kk] * wavelength**coefficients[9+kk+1]

                n = numpy.sqrt(n)
            elif formula_type == 5:  # Cauchy
                def cauchy(c1, c2, w):
                    return c1 * w ** c2
                n = coefficients[0]
                for i in range(1, len(coefficients), 2):
                    n += cauchy(coefficients[i],
                                coefficients[i + 1],
                                wavelength)
            elif formula_type == 6:  # Gasses
                def gasses(c1, c2, w):
                    return c1 / (c2 - w ** (-2))
                n = 1 + coefficients[0]
                for i in range(1, len(coefficients), 2):
                    n += gasses(coefficients[i],
                                coefficients[i + 1],
                                wavelength)
            elif formula_type == 7:  # Herzberger
                n = coefficients[0]
                n += coefficients[1] / (wavelength**2 - 0.028)
                n += coefficients[2] * (1 / (wavelength**2 - 0.028))**2
                for i, cc in enumerate(coefficients[3:]):
                    n += cc * wavelength**(2*(i+1))
            elif formula_type == 8:  # Retro
                n = coefficients[0]
                n += coefficients[1] * wavelength**2 /\
                    (wavelength**2 - coefficients[2])
                n += coefficients[3] * wavelength**2
                n = numpy.sqrt(-(2 * n + 1) / (n - 1))
            elif formula_type == 9:  # Exotic
                n = coefficients[0]
                n += coefficients[1] / (wavelength**2 - coefficients[2])
                n += coefficients[3] * (wavelength - coefficients[4]) / \
                    ((wavelength - coefficients[4])**2 + coefficients[5])
                n = numpy.sqrt(n)
            else:
                raise Exception('Bad formula type')
            return n
        else:
            raise Exception('Wavelength {} is out of bounds.'
                            'Correct range(um): ({}, {})'.
                            format(wavelength, self.rangeMin, self.rangeMax))


class TabulatedRefractiveIndexData:
    """Tabulated RefractiveIndex class"""

    def __init__(self, wavelengths, values):
        """
        Crete a TabulatedRefractiveIndexData from a list of
        wavelengths and values

        :param wavelengths:
        :param values:
        """
        self.rangeMin = numpy.min(wavelengths)
        self.rangeMax = numpy.max(wavelengths)

        if self.rangeMin == self.rangeMax:
            self.refractiveFunction = values[0]
        else:
            self.refractiveFunction = scipy.interpolate.interp1d(wavelengths,
                                                                 values)
        self.wavelengths = wavelengths
        self.coefficients = values

    @staticmethod
    def FromLists(wavelengths, values):
        """
        Crete a TabulatedRefractiveIndexData from a list of
        wavelengths and values
        """
        return TabulatedRefractiveIndexData(wavelengths, values)

    def get_refractiveindex(self, wavelength):
        """
        Get the refractive index at a certain wavelength
        :param wavelength:
        :returns: The refractive at wavelength
        :raises Exception:
        """
        wavelength /= 1000.0
        if self.rangeMin == self.rangeMax and self.rangeMin == wavelength:
            return self.refractiveFunction
        elif self.rangeMin <= wavelength <= self.rangeMax and\
                self.rangeMin != self.rangeMax:
            return self.refractiveFunction(wavelength)
        else:
            raise Exception('Wavelength {} is out of bounds.'
                            'Correct range(um): ({}, {})'
                            .format(wavelength, self.rangeMin, self.rangeMax))

    def get_complete_refractive(self):
        """
        Geth the complete refractive inde data as a list of lists

        :returns: The refractive index data in the form [wavlenght, index]
        """
        extlist = [[
            self.wavelengths[i], self.coefficients[i]]
            for i in range(len(self.wavelengths))]
        return extlist


class ExtinctionCoefficientData:
    """ExtinctionCofficient class"""

    @staticmethod
    def SetupExtinctionCoefficient(wavelengths, values):
        """
        :param wavelengths:
        :param values:
        :return:
        """
        return ExtinctionCoefficientData(wavelengths, values)

    @staticmethod
    def FromLists(wavelengths, values):
        return ExtinctionCoefficientData(wavelengths, values)

    def __init__(self, wavelengths, coefficients):
        """
        :param wavelengths: A list of wavelengths
        :param coefficients: A list of extinction coefficients
        """
        self.extCoeffFunction = scipy.interpolate.interp1d(wavelengths,
                                                           coefficients)
        self.rangeMin = numpy.min(wavelengths)
        self.rangeMax = numpy.max(wavelengths)
        self.wavelengths = wavelengths
        self.coefficients = coefficients

    def get_extinction_coefficient(self, wavelength):
        """
        Get the interpolated extinction coefficient at a wavelength

        :param wavelength:
        :returns: The extinction coefficient at wavelength
        :raises Exception:
        """
        wavelength /= 1000.0
        if self.rangeMin <= wavelength <= self.rangeMax:
            return self.extCoeffFunction(wavelength)
        else:
            raise Exception('Wavelength {} is out of bounds.'
                            'Correct range(um): ({}, {})'.
                            format(wavelength, self.rangeMin, self.rangeMax))

    def get_complete_extinction(self):
        '''
        Get the complete extinction coefficient for the whole
        wavelength intervall

        :returns: A list of refractive indices over the whole
                  wavelength intervall (len = interpolation_points)
        '''
        extlist = [[
            self.wavelengths[i], self.coefficients[i]]
            for i in range(len(self.wavelengths))]
        return extlist
