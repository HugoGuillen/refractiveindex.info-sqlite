import yaml

from refractivesqlite.optical_data import (
    RefractiveIndexData,
    TabulatedRefractiveIndexData,
    ExtinctionCoefficientData,
)
from refractivesqlite.exceptions import NoExtinctionCoefficient
from refractivesqlite._units import to_nm, from_nm


class Material:
    """Material class — holds refractive index and extinction coefficient."""

    def __init__(self, filename, interpolation_points=100, empty=False):
        """
        :param filename: Path to the material YAML file.
        :param interpolation_points: Number of interpolation points for
                                     formula-based materials.
        :param empty: If True, create an uninitialised instance (used by
                      :meth:`FromLists`).
        """
        self.refractiveIndex = None
        self.extinctionCoefficient = None
        self.points = interpolation_points
        if empty:
            return

        with open(filename) as f:
            try:
                material = yaml.safe_load(f)
            except yaml.YAMLError:
                raise Exception('Bad Material YAML File.')

        previous_formula = False
        formula = None
        rangeMin = None
        rangeMax = None
        coefficients = None

        for data in material['DATA']:
            dtype = data['type'].split()
            if dtype[0] == 'tabulated':
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

                if dtype[1] == 'n':
                    if self.refractiveIndex is not None:
                        raise Exception('Bad Material YAML File')
                    self.refractiveIndex = RefractiveIndexData.\
                        SetupRefractiveIndex(formula=-1,
                                             wavelengths=wavelengths,
                                             values=n)
                elif dtype[1] == 'k':
                    self.extinctionCoefficient = ExtinctionCoefficientData.\
                        SetupExtinctionCoefficient(wavelengths, n)
                    if previous_formula:
                        self.refractiveIndex = RefractiveIndexData.\
                            SetupRefractiveIndex(
                                formula=formula, rangeMin=rangeMin,
                                rangeMax=rangeMax, coefficients=coefficients,
                                interpolation_points=self.points)
                elif dtype[1] == 'nk':
                    if self.refractiveIndex is not None:
                        raise Exception('Bad Material YAML File')
                    self.refractiveIndex = RefractiveIndexData.\
                        SetupRefractiveIndex(formula=-1,
                                             wavelengths=wavelengths,
                                             values=n)
                    self.extinctionCoefficient = ExtinctionCoefficientData.\
                        SetupExtinctionCoefficient(wavelengths, k)

            elif dtype[0] == 'formula':
                if self.refractiveIndex is not None:
                    raise Exception('Bad Material YAML File')

                formula = int(dtype[1])
                coefficients = [float(s) for s in data['coefficients'].split()]

                # Support both 'range' (newer upstream) and 'wavelength_range'
                range_key = 'range' if 'range' in data else 'wavelength_range'
                rangeMin, rangeMax = map(float, data[range_key].split())

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

    # ------------------------------------------------------------------
    # Query methods
    # ------------------------------------------------------------------

    def get_refractiveindex(self, wavelength, unit='nm'):
        """Return the refractive index at *wavelength*.

        :param wavelength: Wavelength (scalar or array-like) in *unit*.
        :param unit: Wavelength unit — one of 'm', 'mm', 'um', 'nm', 'A',
                     'cm-1', 'THz', 'eV'. Default: 'nm'.
        :returns: Refractive index (float or ndarray).
        :raises Exception: If no refractive index is defined.
        """
        if self.refractiveIndex is None:
            raise Exception('No refractive index specified for this material')
        wl_nm = to_nm(wavelength, unit)
        return self.refractiveIndex.get_refractiveindex(wl_nm)

    def get_extinctioncoefficient(self, wavelength, unit='nm'):
        """Return the extinction coefficient at *wavelength*.

        :param wavelength: Wavelength (scalar or array-like) in *unit*.
        :param unit: Wavelength unit. Default: 'nm'.
        :returns: Extinction coefficient (float or ndarray).
        :raises NoExtinctionCoefficient: If no k data is defined.
        """
        if self.extinctionCoefficient is None:
            raise NoExtinctionCoefficient(
                'No extinction coefficient specified for this material')
        wl_nm = to_nm(wavelength, unit)
        return self.extinctionCoefficient.get_extinction_coefficient(wl_nm)

    def get_epsilon(self, wavelength, unit='nm',
                    convention='exp_minus_i_omega_t'):
        """Return the complex permittivity ε = (n + ik)² at *wavelength*.

        If no extinction coefficient is available, k is taken as 0.

        :param wavelength: Wavelength (scalar or array-like) in *unit*.
        :param unit: Wavelength unit. Default: 'nm'.
        :param convention: Sign convention for the imaginary part.
            ``'exp_minus_i_omega_t'`` (default, physics/optics) gives
            ε = (n + ik)²; ``'exp_plus_i_omega_t'`` (engineering) gives
            ε = (n − ik)².
        :returns: Complex permittivity (complex or ndarray of complex).
        """
        n = self.get_refractiveindex(wavelength, unit=unit)
        try:
            k = self.get_extinctioncoefficient(wavelength, unit=unit)
        except NoExtinctionCoefficient:
            k = 0.0
        if convention == 'exp_minus_i_omega_t':
            return (n + 1j * k) ** 2
        else:
            return (n - 1j * k) ** 2

    def get_wl_range(self, unit='nm'):
        """Return the valid wavelength range as *(min, max)* in *unit*.

        :param unit: Wavelength unit. Default: 'nm'.
        :returns: Tuple (wl_min, wl_max) in the requested unit.
        """
        # rangeMin/rangeMax are stored in um; convert to nm first, then to unit
        lo = float(from_nm(self.rangeMin * 1000.0, unit))
        hi = float(from_nm(self.rangeMax * 1000.0, unit))
        return (min(lo, hi), max(lo, hi))

    # ------------------------------------------------------------------
    # Bulk data retrieval
    # ------------------------------------------------------------------

    def get_complete_refractive(self):
        """Return all refractive index data as a list of [wl_um, n] pairs."""
        if self.has_refractive():
            return self.refractiveIndex.get_complete_refractive()
        return None

    def get_complete_extinction(self):
        """Return all extinction coefficient data as a list of [wl_um, k] pairs."""
        if self.has_extinction():
            return self.extinctionCoefficient.get_complete_extinction()
        return None

    # ------------------------------------------------------------------
    # Predicates
    # ------------------------------------------------------------------

    def has_refractive(self):
        """True if a refractive index is available."""
        return self.refractiveIndex is not None

    def has_extinction(self):
        """True if an extinction coefficient is available."""
        return self.extinctionCoefficient is not None

    # ------------------------------------------------------------------
    # Metadata / I/O
    # ------------------------------------------------------------------

    def get_page_info(self):
        """Return the page info dict."""
        return self.pageinfo

    def to_csv(self, output):
        """Write this material's data to CSV file(s).

        :param output: Output path. Suffix ``(nk).csv``, ``(n).csv`` or
                       ``(k).csv`` is appended automatically.
        """
        refr = self.get_complete_refractive()
        ext = self.get_complete_extinction()
        if self.has_refractive() and self.has_extinction() and \
                len(refr) == len(ext):
            path = output.replace('.csv', '(nk).csv')
            with open(path, 'w') as f:
                f.write('wl,n,k\n')
                for i in range(len(refr)):
                    f.write(','.join(
                        map(str, [refr[i][0], refr[i][1], ext[i][1]])) + '\n')
            print('Wrote', path)
        else:
            if self.has_refractive():
                path = output.replace('.csv', '(n).csv')
                with open(path, 'w') as f:
                    f.write('wl,n\n')
                    for row in refr:
                        f.write(','.join(map(str, row)) + '\n')
                print('Wrote', path)
            if self.has_extinction():
                path = output.replace('.csv', '(k).csv')
                with open(path, 'w') as f:
                    f.write('wl,k\n')
                    for row in ext:
                        f.write(','.join(map(str, row)) + '\n')
                print('Wrote', path)

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @staticmethod
    def FromLists(pageinfo, wavelengths_r=None, refractive=None,
                  wavelengths_e=None, extinction=None):
        """Create a :class:`Material` directly from Python lists.

        :param pageinfo: Dict with keys ``shelf``, ``book``, ``page``, etc.
        :param wavelengths_r: Wavelengths (um) for refractive index.
        :param refractive: Refractive index values.
        :param wavelengths_e: Wavelengths (um) for extinction coefficient.
        :param extinction: Extinction coefficient values.
        :returns: :class:`Material`
        """
        mat = Material('', empty=True)
        mat.pageinfo = pageinfo
        if refractive is not None:
            mat.refractiveIndex = TabulatedRefractiveIndexData.FromLists(
                wavelengths_r, refractive)
            mat.rangeMin = mat.refractiveIndex.rangeMin
            mat.rangeMax = mat.refractiveIndex.rangeMax
        if extinction is not None:
            mat.extinctionCoefficient = ExtinctionCoefficientData.FromLists(
                wavelengths_e, extinction)
            if refractive is None:
                mat.rangeMin = mat.extinctionCoefficient.rangeMin
                mat.rangeMax = mat.extinctionCoefficient.rangeMax
        return mat
