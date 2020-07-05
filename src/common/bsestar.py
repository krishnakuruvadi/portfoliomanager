import requests
from os.path import isfile
import csv
#from shared.utils import *

class BSEStar:
    #all_schemes_url = 
    def __init__(self):
        self.session = requests.Session()
    
    def get_all_schemes(self, filename):
        schemes = dict()
        if isfile(filename):
            with open(filename, mode='r', encoding='utf-8-sig') as csv_file:
                print("opened file as csv:", filename)
                csv_reader = csv.DictReader(csv_file, delimiter="|")
                for row in csv_reader:
                    #print(row)
                    isin = row['ISIN']
                    scheme_name = row['Scheme Name']
                    print('isin:', isin, ' scheme:', scheme_name)
                    schemes[isin] = scheme_name
        return schemes

if __name__ == "__main__":
    bse_star = BSEStar()
    bse_star.get_all_schemes('/Users/kkuruvad/Downloads/SCHMSTRDET_04072020.txt')

