#!/usr/bin/env python

import re
from pprint import pprint
import json

csv_file = 'LiPAD Launch - Recipient List - NGAs and MOA signatories (pipe delim).csv'

agencies_with_email = {
    'NAMRIA': ['lgrafil@namria.gov.ph', 'aaalcala@namria.gov.ph'],
    'LLDA': ['mis@llda.gov.ph'],
    'RBCO': ['fretzielcatugda@gmail.com'],
    'PRA': ['glastimosa@gmail.com'],
    'DND': ['ssurian@dnd.gov.ph'],
    'BMB': ['bmb@bmb.gov.ph'],
    'MBCO': ['genesis.mbco.mbdsr3@gmail.com', 'dwardbornilla@gmail.com'],

}
agencies = []
data = []
with open(csv_file, 'r') as open_file:
    first_line = True
    for line in open_file:
        tokens = line.strip().split('|')
        if first_line:
            first_line = False
            continue

        try:
            counter = int(tokens[0])
            name = tokens[3]
            if name == '':
                continue
            title = tokens[1]
            emails = re.findall(r'([\w\.-]+@[\w\.-]+)', tokens[5].lower())

            agency = ''
            try:
                agency = re.findall(r'\(([A-Z]+)\)', tokens[6].upper())[0]
                agencies.append(agency)

                if agency in agencies_with_email:
                    emails += agencies_with_email[agency]
            except IndexError:
                pass

            # print title, name, emails, agency
            data.append({'title': title,
                         'name': name,
                         'emails': emails})
        except ValueError:
            pass

pprint(sorted(agencies))
pprint(data)

json.dump(data, open('data.json', 'w'))
