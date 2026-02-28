import yaml

from refractivesqlite.optical_data import (
    RefractiveIndexData,
    TabulatedRefractiveIndexData,
    ExtinctionCoefficientData,
)
from refractivesqlite.exceptions import NoExtinctionCoefficient


class Material:
    """ Material class"""
    def __init__(self, filename, interpolation_points=100, empty=False):
        """

        :param filename: The name of the material file
        :interpolation_points=100: The number of interpolation_points
        :empty=False: Create an empty material instance
        """
        self.refractiveIndex = None
        self.extinctionCoefficient = None
        self.points = interpolation_points
        if empty:
            return

        f = open(filename)
        try:
            material = yaml.safe_load(f)
        except yaml.YAMLError:
            raise Exception('Bad Material YAML File.')
        finally:
            f.close()

        previous_formula = False
        for data in material['DATA']:
            if (data['type'].split())[0] == 'tabulated':
                rows = data['data'].split('\n')
                splitrows = [c.split() for c in rows]
                wavelengths = []
                n = []
                k = []
                for s in splitrows:
                    if len(s) > 0:
                        wavelengths.append(float(s[0]))
                        n.append(float(s[1]))
                        if len(s) > 2:
                            k.append(float(s[2]))
                self.points = len(wavelengths)

                if (data['type'].split())[1] == 'n':
                    if self.refractiveIndex is not None:
                        Exception('Bad Material YAML File')

                    self.refractiveIndex = RefractiveIndexData.\
                        SetupRefractiveIndex(formula=-1,
                                             wavelengths=wavelengths,
                                             values=n)
                elif (data['type'].split())[1] == 'k':
                    self.extinctionCoefficient = ExtinctionCoefficientData.\
                        SetupExtinctionCoefficient(wavelengths, n)
                    if previous_formula:
                        self.refractiveIndex = RefractiveIndexData.\
                            SetupRefractiveIndex(
                                formula=formula, rangeMin=rangeMin,
                                rangeMax=rangeMax, coefficients=coefficients,
                                interpolation_points=self.points)
                elif (data['type'].split())[1] == 'nk':
                    if self.refractiveIndex is not None:
                        Exception('Bad Material YAML File')
                    self.refractiveIndex = RefractiveIndexData.\
                        SetupRefractiveIndex(formula=-1,
                                             wavelengths=wavelengths,
                                             values=n)
                    self.extinctionCoefficient = ExtinctionCoefficientData.\
                        SetupExtinctionCoefficient(wavelengths, k)
            elif (data['type'].split())[0] == 'formula':

                if self.refractiveIndex is not None:
                    Exception('Bad Material YAML File')

                formula = int((data['type'].split())[1])
                coefficients = [float(s) for s in data['coefficients'].split()]
                rangeMin, rangeMax = map(float,
                                         data['wavelength_range'].split())
                previous_formula = True
                self.refractiveIndex = RefractiveIndexData.\
                    SetupRefractiveIndex(formula=formula,
                                         rangeMin=rangeMin,
                                         rangeMax=rangeMax,
                                         coefficients=coefficients,
                                         interpolation_points=self.points)
        if self.refractiveIndex is not None:
            self.rangeMin = self.refractiveIndex.rangeMin
            self.rangeMax = self.refractiveIndex.rangeMax
        else:
            self.rangeMin = self.extinctionCoefficient.rangeMin
            self.rangeMax = self.extinctionCoefficient.rangeMax

    def get_refractiveindex(self, wavelength):
        """
        Get the refractive index at a certain wavelenght

        :param wavelength: The wavelength in nm
        :returns: refractive index
        :raises Exception:
        """
        if self.refractiveIndex is None:
            raise Exception('No refractive index specified for this material')
        else:
            return self.refractiveIndex.get_refractiveindex(wavelength)

    def get_extinctioncoefficient(self, wavelength):
        """
        Get the extinction coefficient

        :param wavelength:
        :returns: extiction coefficient
        :raises NoExtinctionCoefficient:
        """
        if self.extinctionCoefficient is None:
            raise NoExtinctionCoefficient('No extinction coefficient'
                                          'specified for this material')
        else:
            return self.extinctionCoefficient.\
                get_extinction_coefficient(wavelength)

    def get_complete_extinction(self):
        '''
        Get the complete extinction coefficient information

        :returns: The extinction coefficient informations as a list of lists
        '''

        if self.has_extinction():
            return self.extinctionCoefficient.get_complete_extinction()
        else:
            return None

    def get_complete_refractive(self):
        '''
        Get the complete refractive information

        :returns: The refractive index informations as a list of lists
        '''
        if self.has_refractive():
            return self.refractiveIndex.get_complete_refractive()
        else:
            return None

    def has_refractive(self):
        '''
        Checks if there is a refractive index
        '''
        return self.refractiveIndex is not None

    def has_extinction(self):
        '''
        Checks if there is a extinction coefficient
        '''
        return self.extinctionCoefficient is not None

    def get_page_info(self):
        '''
        Get the page informations
        '''
        return self.pageinfo

    def to_csv(self, output):
        '''
        Safe this material as a comma seperated value list

        :param output: The output file
        '''
        refr = self.get_complete_refractive()
        ext = self.get_complete_extinction()
        # FizzFuzz
        if self.has_refractive() and self.has_extinction() and\
                len(refr) == len(ext):
            header = "wl,n,k\n"
            output_f = open(output.replace(".csv", "(nk).csv"), 'w')
            output_f.write(header)
            for i in range(len(refr)):
                output_f.write(",".join(list(
                    map(str, [refr[i][0], refr[i][1], ext[i][1]])))+"\n")
            output_f.close()
            print("Wrote", output.replace(".csv", "(nk).csv"))
        else:
            if self.has_refractive():
                output_f = open(output.replace(".csv", "(n).csv"), 'w')
                header = "wl,n\n"
                output_f.write(header)
                for i in range(len(refr)):
                    output_f.write(",".join(list(
                        map(str, [refr[i][0], refr[i][1]])))+"\n")
                output_f.close()
                print("Wrote", output.replace(".csv", "(n).csv"))
            if self.has_extinction():
                output_f = open(output.replace(".csv", "(k).csv"), 'w')
                header = "wl,k\n"
                output_f.write(header)
                for i in range(len(ext)):
                    output_f.write(",".join(list(
                        map(str, [ext[i][0], ext[i][1]])))+"\n")
                output_f.close()
                print("Wrote", output.replace(".csv", "(k).csv"))

    @staticmethod
    def FromLists(pageinfo, wavelengths_r=None, refractive=None,
                  wavelengths_e=None, extinction=None):
        '''
        Create a material from lists of wavelength refractive indices
        and extinction coefficients

        :param pageinfo: The pageinfo of the material
        :param wavelengths_r: A list of wavelengths for the refractive index
        :param refractive: A list of refractive indices
        :param wavelengths_e: A list of wavelengths_e for the extinction coeff
        :param extinction: A list of extinction coefficients
        :returns: A material
        '''
        mat = Material("", empty=True)
        mat.pageinfo = pageinfo
        if refractive is not None:
            mat.refractiveIndex = TabulatedRefractiveIndexData.\
                FromLists(wavelengths_r, refractive)
            mat.rangeMin = mat.refractiveIndex.rangeMin
            mat.rangeMax = mat.refractiveIndex.rangeMax
        if extinction is not None:
            mat.extinctionCoefficient = ExtinctionCoefficientData.\
                FromLists(wavelengths_e, extinction)
            mat.rangeMin = mat.extinctionCoefficient.rangeMin
            mat.rangeMax = mat.extinctionCoefficient.rangeMax
        return mat
