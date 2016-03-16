#!/usr/bin/env python2

import sqlite3
import traceback
from collections import defaultdict
from pprint import pprint

def _parse_csv():
	### Initialize db ###
	con = sqlite3.connect("lgu.db")
	con.row_factory = sqlite3.Row
	c = con.cursor()
	with con:
	    # Create tables
	    con.execute('''CREATE TABLE IF NOT EXISTS
	                   lgu (
	                        municipality TEXT,
	                        province TEXT,
	                        address TEXT,
	                        landline TEXT,
	                        fax TEXT,
	                        email TEXT)''')

	with open('LGUcomplete_pipedelim.csv', 'r') as open_file:
		first_line = True
		for line in open_file:
			# Skip headers
			if first_line:
				first_line = False
				continue
			l = line.strip()
			if l:
				try:
					tokens = l.split('|')
					params = defaultdict(lambda: None, {})
					# print tokens
					# if len(tokens) >= 1:
					province = tokens[0].strip()
					params['province'] = province
					if province == '"':
						continue
					# if len(tokens) >= 2:
					municipality = tokens[1].strip()
					if municipality == '':
						continue
					# if (not 'Municipality' in municipality) and (not 'City' in municipality) and (not 'Provincial' in municipality):
					# 	print repr(municipality)
					# 	# if municipality == '':
					# 	# 	print repr(province)
					# 	# 	print repr(line)
					muni = municipality.lower().replace('municipality', 
						'').replace('city', 
						'').replace('provincial', 
						'').replace('government', 
						'').replace('of', 
						'').replace('(capital)',
						'').strip()
					# print muni
					params['municipality'] = muni
					# if len(tokens) >= 3:
					address = tokens[2].strip()
					params['address'] = address
					# if len(tokens) >= 4:
					landline = tokens[3].strip()
					params['landline'] = landline
					if len(tokens) >= 5:
						fax = tokens[4].strip()
						params['fax'] = fax					
					if len(tokens) >= 6:
						email = tokens[5].strip()
						params['email'] = email

					pprint(params)

				except IndexError, e:
					traceback.print_exc()
					print repr(line)
					exit(1)

_parse_csv()