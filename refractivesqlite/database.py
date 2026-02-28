import os
import sqlite3
from collections import OrderedDict

import numpy as np

from refractivesqlite._constants import RII_DATABASE_URL
from refractivesqlite.builder import create_sqlite_database
from refractivesqlite.downloader import download_rii_zip
from refractivesqlite.material import Material


class Database:
    def __init__(self, sqlitedbpath):
        '''
        Construct a database instance

        :param sqlitedbpath: The path of the sqlitedatabse
                             it has to exist even if you want to create
                             a new database
        '''
        self.db_path = sqlitedbpath
        if not os.path.isfile(sqlitedbpath):
            print("Database file not found.")
        else:
            print("Database file found at", sqlitedbpath)

    def create_database_from_folder(self, yml_database_path,
                                    interpolation_points=100):
        '''
        Create a sql database from a yml database path

        :param yml_database_path: The path to the yaml database
        :param interpolation_points: The number of interpolation_points to use
        '''
        create_sqlite_database(yml_database_path,
                               self.db_path,
                               interpolation_points=interpolation_points)

    def create_database_from_url(self,
                                 riiurl=RII_DATABASE_URL,
                                 interpolation_points=100):
        '''
        Create a sqlite database from an url

        :param riiurl: The url where to download the zip compressed
                       refractive index database from
        :param interpolation_points: The number of interpolation_points to use
        '''
        download_rii_zip(riiurl=riiurl)
        self.create_database_from_folder(
            "database", interpolation_points=interpolation_points)

    def check_url_version(self):
        print(RII_DATABASE_URL)

    def search_custom(self, sqlquery):
        '''
        Make a custom sql query

        :param sqlquery: The sql query to make
        :retrurn: Return all results of the query
        '''
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(sqlquery)
        results = c.fetchall()
        if len(results) == 0:
            print("No results found.")
        else:
            print(len(results), "results found.")
        conn.close()
        return results

    def search_pages(self, term="", exact=False):
        '''
        Search for pages by a looking for the searchterm
        in shelf, book, page and filename

        :param term: The search term to look for
        :param exact: If false term is extended to %term%
        '''
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        if not exact:
            c.execute('SELECT * FROM pages WHERE shelf like ? or book like'
                      '? or page like ? or filepath like ?',
                      ["%"+term+"%" for i in range(4)])
        else:
            c.execute('SELECT * FROM pages WHERE shelf like ? or book like'
                      '? or page like ? or filepath like ?',
                      [term for i in range(4)])
        results = c.fetchall()
        if len(results) == 0:
            print("No results found.")
        else:
            print(len(results), "results found.")
            columns = self._get_pages_columns()
            print("\t".join(columns))
            for r in results:
                print("\t".join(map(str, r[:])))
        conn.close()

    def search_id(self, pageid):
        '''
        Print page informations

        :param pageid: The id of the page to print
        '''
        info = self._get_page_info(pageid)
        if info is None:
            print("PageID not found.")
        else:
            print("\t".join(info.keys()))
            print("\t".join(map(str, info.values())))

    def search_n(self, n, delta_n):
        '''
        Search for materials with a fraction index between
        n and delta_n

        :param n: The lower bound of the fraction index
        :param delta_m: The upper bound of the fraction index
        '''
        print("*Search n =", n, "delta_n = ", delta_n)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        interval = [n-delta_n, n+delta_n]
        c.execute('''select r.pageid,shelf,book,page,r.wave,r.refindex
                    from refractiveindex r join pages p on r.pageid = p.pageid
                    where refindex between ? and ? ''', interval)
        results = c.fetchall()
        if len(results) == 0:
            print("No results found.")
        else:
            print(len(results), "results found.")
            print("pageid|shelf|book|page|wavelength|n")
            for r in results:
                print(r)
        conn.close()

    def search_k(self, k, delta_k):
        '''
        Search for materials with an extinction coefficient between
        k and delta_k

        :param k: The lower bound of the extinction coefficient
        :param delta_k: The upper bound of the extinction coefficient
        '''
        print("*Search k =", k, "delta_k = ", delta_k)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        interval = [k-delta_k, k+delta_k]
        c.execute('''select e.pageid,shelf,book,page,e.wave,e.coeff
                    from extcoeff e join pages p on e.pageid = p.pageid
                    where coeff between ? and ?''', interval)
        results = c.fetchall()
        if len(results) == 0:
            print("No results found.")
        else:
            print(len(results), "results found.")
            print("pageid|shelf|book|page|wavelength|k")
            for r in results:
                print(r)
        conn.close()

    def search_nk(self, n, delta_n, k, delta_k):
        '''
        Search for materials with fraction indice and extinction
        coefficient between n and delta_n and k and delta_k

        :param n: The lower bound of the fraction index
        :param delta_n: The upper bound of the fraction index
        :param k: The lower bound of the extinction coefficient
        :param delta_k: The upper bound of the extinction coefficient
        '''
        print("*Search n =", n, "delta_n = ", delta_n, "k = ", k,
              "delta_k = ", delta_k)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        interval = [n-delta_n, n+delta_n, k-delta_k, k+delta_k]
        c.execute('''select r.pageid, shelf, book, page, r.wave, r.refindex,
                     e.coeff from refractiveindex r join extcoeff e on
                     r.pageid = e.pageid and r.wave = e.wave join pages p
                     on r.pageid = p.pageid where refindex between
                     ? and ? and coeff between ? and ?''', interval)
        results = c.fetchall()
        if len(results) == 0:
            print("No results found.")
        else:
            print(len(results), "results found.")
            print("pageid|shelf|book|page|wavelength|n|k")
            for r in results:
                print(r)
        conn.close()

    def get_material(self, pageid):
        '''
        Get the material from a pageid

        :param pageid: The pageid of the material
        :returns: Material
        '''
        pagedata = self._get_page_info(pageid)
        if pagedata is None:
            print("PageID not found.")
            return None
        else:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            wavelengths_r = None
            wavelengths_e = None
            refractive = None
            extinction = None
            if pagedata['hasrefractive'] == 1:
                c.execute('''select wave,refindex
                            from refractiveindex
                            where pageid = ?
                            order by wave asc''', [pageid])
                results = c.fetchall()
                wavelengths_r = [r[0] for r in results]
                refractive = [r[1] for r in results]
            if pagedata['hasextinction'] == 1:
                c.execute('''select wave,coeff
                            from extcoeff
                            where pageid = ?
                            order by wave asc''', [pageid])
                results = c.fetchall()
                wavelengths_e = [r[0] for r in results]
                extinction = [r[1] for r in results]
            conn.close()
            print("Material", pagedata['filepath'], "loaded.")
            return Material.FromLists(pagedata,
                                      wavelengths_r=wavelengths_r,
                                      refractive=refractive,
                                      wavelengths_e=wavelengths_e,
                                      extinction=extinction)

    def get_material_n_numpy(self, pageid):
        '''
        Get the refraction index of a material

        :param pageid: The pageid of the material
        :return: The refraction data as a numpy array
        '''
        mat = self.get_material(pageid)
        if mat is None:
            return None
        n = mat.get_complete_refractive()
        if n is None:
            print("Material has no refractive data.")
            return None
        return np.array(n)

    def get_material_k_numpy(self, pageid):
        '''
        Get the extinction coefficient of a material

        :param pageid: The pageid of the material
        :return: The extinction data as a numpy array
        '''
        mat = self.get_material(pageid)
        if mat is None:
            return None
        k = mat.get_complete_extinction()
        if k is None:
            print("Material has no extinction data.")
            return None
        return np.array(k)

    def get_material_csv(self, pageid, output="", folder=""):
        '''
        Safe a material as a comma seperated value list

        :param pageid: The pageid of the material
        :param output: The name of the output file
                       default is [pageid][shelf][book][page].csv
        :param folder: The output folder default is ./
        '''
        mat = self.get_material(pageid)
        if mat is None:
            print("PageID not found.")
            return None
        matInfo = mat.get_page_info()
        if output == "":
            output = ",".join([str(matInfo['pageid']), matInfo['shelf'],
                              matInfo['book'], matInfo['page']])+".csv"
        if folder != "":
            output = folder+os.sep+output
        mat.to_csv(output)

    def get_material_csv_all(self, outputfolder):
        '''
        Safe all materials as comma seperated value lists

        :param outputfolder: The output folder
        '''
        allids = self._get_all_pageids()
        for id in allids:
            print("Processing", id)
            self.get_material_csv(pageid=id, output="", folder=outputfolder)

    def _get_pages_columns(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('PRAGMA table_info(pages);')
        results = c.fetchall()
        names = [r[1] for r in results]
        conn.close()
        return names

    def _get_page_info(self, pageid):
        '''
        Query all page information for a page

        :param pageid: The id of the page to query
        :returns: An ordered dict of page informations
        '''
        columns = self._get_pages_columns()
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT * FROM pages WHERE pageid = ?', [pageid])
        results = c.fetchall()
        if len(results) == 0:
            conn.close()
            return None
        else:
            row = results[0]
            data = OrderedDict.fromkeys(columns)
            for idx, col in enumerate(columns):
                data[col] = row[idx]
            conn.close()
            return data

    def _get_all_pageids(self):
        '''
        Query all page ids from the sqlite database

        :returns: A lis of pageids
        '''
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT pageid FROM pages')
        results = c.fetchall()
        if len(results) == 0:
            conn.close()
            return None
        else:
            pageids = [row[0] for row in results]
            return pageids
