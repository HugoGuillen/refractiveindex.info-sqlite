import io
import os
import zipfile

import requests

from refractivesqlite._constants import RII_DATABASE_URL


def download_rii_zip(output_folder="", riiurl=RII_DATABASE_URL):
    """
    Download and extract the refractive index info database zip.

    :param output_folder: Directory to extract into (default: current dir).
    :param riiurl: URL of the database zip archive.
    :returns: Path to the extracted database folder on success, or None.
    """
    print("Making request to", riiurl)
    r = requests.get(riiurl)
    if not r.ok:
        print("There was a problem with the request.")
        return None

    print("Downloaded and extracting...")
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall(path=output_folder)

    # Detect the extracted database folder by looking for the catalog file
    db_folder = _find_database_folder(output_folder)
    print("Wrote", db_folder, "from", riiurl)
    return db_folder


def _find_database_folder(base_path):
    """Find the database folder inside *base_path* after zip extraction.

    Looks for a directory containing ``catalog-nk.yml`` or ``library.yml``.
    Falls back to ``database`` if neither is found (backwards-compatible).
    """
    base = base_path or "."
    # Check common locations
    for candidate in ("database", "."):
        folder = os.path.join(base, candidate) if candidate != "." else base
        for catalog_name in ("catalog-nk.yml", "library.yml"):
            if os.path.isfile(os.path.join(folder, catalog_name)):
                return folder
    # Walk one level to find any folder with a catalog file
    if os.path.isdir(base):
        for name in os.listdir(base):
            folder = os.path.join(base, name)
            if os.path.isdir(folder):
                for catalog_name in ("catalog-nk.yml", "library.yml"):
                    if os.path.isfile(os.path.join(folder, catalog_name)):
                        return folder
    # Default fallback
    return os.path.join(base, "database")
