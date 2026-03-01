"""
Wavelength unit conversion helpers.

All internal computations use micrometres (um). Query methods accept
wavelengths in nanometres (nm) by default; this module converts to/from
that convention as needed.

Supported units: 'm', 'mm', 'um', 'nm', 'A', 'cm-1', 'THz', 'eV'
"""
import numpy

_h = 6.62607015e-34   # Planck constant (J·s)
_c = 299792458.0      # Speed of light (m/s)
_e = 1.602176634e-19  # Elementary charge (C)

# hc in eV·nm
_hc_eV_nm = _h * _c / _e * 1e9   # ≈ 1239.84198 eV·nm
# c in nm·THz
_c_nm_THz = _c * 1e-3             # ≈ 299792.458 nm·THz

SUPPORTED_UNITS = ['m', 'mm', 'um', 'nm', 'A', 'cm-1', 'THz', 'eV']

# Each entry is (to_nm, from_nm): callables that convert between the given
# unit and nanometres. Both accept array-like input.
_UNITS = {
    'm':    (lambda x: numpy.asarray(x, dtype=float) * 1e9,
             lambda nm: numpy.asarray(nm, dtype=float) * 1e-9),
    'mm':   (lambda x: numpy.asarray(x, dtype=float) * 1e6,
             lambda nm: numpy.asarray(nm, dtype=float) * 1e-6),
    'um':   (lambda x: numpy.asarray(x, dtype=float) * 1e3,
             lambda nm: numpy.asarray(nm, dtype=float) * 1e-3),
    'nm':   (lambda x: numpy.asarray(x, dtype=float),
             lambda nm: numpy.asarray(nm, dtype=float)),
    'A':    (lambda x: numpy.asarray(x, dtype=float) * 0.1,
             lambda nm: numpy.asarray(nm, dtype=float) * 10.0),
    'cm-1': (lambda x: 1e7 / numpy.asarray(x, dtype=float),
             lambda nm: 1e7 / numpy.asarray(nm, dtype=float)),
    'THz':  (lambda x: _c_nm_THz / numpy.asarray(x, dtype=float),
             lambda nm: _c_nm_THz / numpy.asarray(nm, dtype=float)),
    'eV':   (lambda x: _hc_eV_nm / numpy.asarray(x, dtype=float),
             lambda nm: _hc_eV_nm / numpy.asarray(nm, dtype=float)),
}


def to_nm(wavelength, unit):
    """Convert *wavelength* expressed in *unit* to nanometres.

    Parameters
    ----------
    wavelength : float or array-like
    unit : str  one of SUPPORTED_UNITS

    Returns
    -------
    numpy.ndarray  wavelength in nm
    """
    if unit not in _UNITS:
        raise ValueError(
            "Unknown unit '{}'. Supported: {}".format(unit, SUPPORTED_UNITS))
    return _UNITS[unit][0](wavelength)


def from_nm(wavelength_nm, unit):
    """Convert *wavelength_nm* (in nm) to *unit*.

    Parameters
    ----------
    wavelength_nm : float or array-like
    unit : str  one of SUPPORTED_UNITS

    Returns
    -------
    numpy.ndarray  wavelength in the requested unit
    """
    if unit not in _UNITS:
        raise ValueError(
            "Unknown unit '{}'. Supported: {}".format(unit, SUPPORTED_UNITS))
    return _UNITS[unit][1](wavelength_nm)
