import io
import zipfile

import requests

from refractivesqlite._constants import RII_DATABASE_URL


def download_rii_zip(output_folder="", riiurl=RII_DATABASE_URL):
    """
    Download the refractive index info database

    :param output_folder: The output folder ./ as default
    :param riiurl: The url from where to download the database
    :returns: True on success, false otherwise
    """
    print("Making request to", riiurl)
    r = requests.get(riiurl)
    if r.ok:
        print("Downloaded and extracting...")
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall(path=output_folder)
        print("Wrote", output_folder+"/database", "from", riiurl)
        return True
    else:
        print("There was a problem with the request.")
        return False
