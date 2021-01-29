"""data_pipeline.py: Module is used to fetch the images from the SDO data store"""

__author__ = "Chakraborty, S."
__copyright__ = "Copyright 2021, SuperDARN@VT"
__credits__ = []
__license__ = "MIT"
__version__ = "1.0."
__maintainer__ = "Chakraborty, S."
__email__ = "shibaji7@vt.edu"
__status__ = "Research"

import os
import datetime as dt
import argparse
from dateutil import parser as prs
from lxml import html
import requests

from to_remote import get_session

class SDOFiles(object):
    """ Class that holds SDO file objects """
    
    def __init__(self, _dict_):
        for p in _dict_.keys():
            setattr(self, p, _dict_[p])
        self.uri = "https://sdo.gsfc.nasa.gov/assets/img/browse/"
        self._fetch_file_list_()
        self.folder = "data/SDO-Database/{:4d}.{:02d}.{:02d}/{:d}/{:04d}/".format(self.date.year, self.date.month,
                                                                                  self.date.day, self.resolution, 
                                                                                  self.wavelength)
        if not os.path.exists(self.folder): os.system("mkdir -p " + self.folder)
        self.conn = get_session()
        return
    
    def _fetch_file_list_(self):
        uri = self.uri + "index.php?b={:4d}%2F{:02d}%2F{:02d}".format(self.date.year,                                                       
                                                                      self.date.month,
                                                                      self.date.day)
        if self.verbose: print(" URI:", uri)
        page = requests.get(uri)
        tree = html.fromstring(page.content)
        self.filenames = tree.xpath("//a[@class=\"name file\"]/text()")
        self.hrefs = []
        for a in tree.xpath("//a[@class=\"name file\"]"):
            items = a.items()
            for item in items:
                if item[0] == "href": self.hrefs.append(self.uri + item[1])
        return
    
    def get_files(self):
        tag = "{:d}_{:04d}.jpg".format(self.resolution, self.wavelength)
        filenames = []
        for href, fname in zip(self.hrefs, self.filenames):
            if tag in href: filenames.append(fname)
        return filenames, self.folder
    
    def fetch(self):
        tag = "{:d}_{:04d}.jpg".format(self.resolution, self.wavelength)
        create_dir = True
        for href, fname in zip(self.hrefs, self.filenames):
            if tag in href:
                self._download_sdo_data_(href, fname, create_dir)
                create_dir = False
        return self
    
    def close(self):
        self.conn.close()
        if os.path.exists(self.folder): os.system("rm -rf data/SDO-Database/*")
        return
    
    def _download_sdo_data_(self, h, fname, create_dir):
        if self.verbose: print(" Downloading from:", h, "-to-", self.folder.replace("data/SDO-Database/",""))
        r = requests.get(h)
        with open(self.folder + fname,"wb") as f: f.write(r.content)
        if create_dir: self.conn.create_remote_dir(self.folder)
        self.conn.to_remote_FS(self.folder + fname, is_local_remove=True)
        return

def fetch_sdo(_dict_):
    """ Parse SDO files from remote """
    sdo = SDOFiles(_dict_)
    sdo.fetch().close()
    return

def fetch_filenames(_dict_):
    """ Fetch file names and dirctory """
    sdo = SDOFiles(_dict_)
    _files_, _dirs_ = sdo.get_files()
    sdo.close()
    return _files_, _dirs_

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-dn", "--date", default=dt.datetime(2015,3,11), help="Date [2015-3-11]", type=prs.parse)
    parser.add_argument("-r", "--resolution", default=512, help="Resolution of the files [512]", type=int)
    parser.add_argument("-w", "--wavelength", default=193, help="Wavelength of the files [193]", type=int)
    parser.add_argument("-l", "--loc", default="sdo", help="Database [sdo]", type=str)
    parser.add_argument("-v", "--verbose", action="store_false", help="Increase output verbosity [True]")
    args = parser.parse_args()
    _dict_ = {}
    if args.verbose:
        print("\n Parameter list for Bgc simulation ")
        for k in vars(args).keys():
            print("     " + k + "->" + str(vars(args)[k]))
            _dict_[k] = vars(args)[k]
    if _dict_["loc"] == "sdo": fetch_sdo(_dict_)