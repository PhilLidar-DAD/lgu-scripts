#!/usr/bin/env python3

import sqlite3
import traceback
from collections import defaultdict
from pprint import pprint
import re


def _init_db():
    ### Initialize db ###
    con = sqlite3.connect('lgu.db')
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    with con:
        # Create tables
        con.execute('''CREATE TABLE IF NOT EXISTS
                       lgu (
                            municipality TEXT,
                            province TEXT,
                            address TEXT,
                            landline TEXT,
                            fax TEXT,
                            email TEXT,
                            PRIMARY KEY(municipality, province))''')

    return con, cur


def _parse_all_lgu_csv():

    # Parse CSV file
    with open('LGUcomplete_pipedelim.csv', 'r') as open_file:
        first_line = True
        for line in open_file:

            # Skip column headers
            if first_line:
                first_line = False
                continue
            l = line.strip()

            if l:
                try:
                    tokens = l.split('|')
                    params = defaultdict(lambda: None, {})

                    province = tokens[0].strip()
                    params['province'] = province.lower()
                    # Skip this erroneous line
                    if province == '"':
                        continue

                    municipality = tokens[1].strip()
                    if municipality == '':
                        continue

                    # Remove the ff. words:
                    # municipality, city, provincial, government, of, capital
                    muni = municipality.lower().replace(
                        'municipality', '').replace('city', '').replace(
                        'provincial', '').replace('government', '').replace(
                        'of', '').replace('(capital)', '').strip()

                    params['municipality'] = muni
                    if not params['province']:
                        params['province'] = muni

                    address = tokens[2].strip()
                    params['address'] = address

                    landline = tokens[3].strip()
                    params['landline'] = landline

                    if len(tokens) >= 5:
                        fax = tokens[4].strip()
                        params['fax'] = fax

                    if len(tokens) >= 6:
                        email = tokens[5].strip()
                        params['email'] = email

                    # Insert to database
                    pprint(params)
                    with dbcon:
                        try:
                            dbcon.execute('''INSERT OR IGNORE INTO lgu
                                       VALUES (
                                                :municipality,
                                                :province,
                                                :address,
                                                :landline,
                                                :fax,
                                                :email)''', params)
                        except:
                            traceback.print_exc()
                            pprint(params)
                            exit(1)

                except IndexError:
                    traceback.print_exc()
                    print(repr(line))
                    exit(1)


def _parse_dream_lgu_csv():

    dream_lgus = []
    with open('lgu_dream_list.csv', 'r') as open_file:
        for l in open_file:
            line = l.strip()
            if line:
                dream_lgus.append(line)
    return dream_lgus


def _parse_number(text):

    num_sep = [';', '/']
    n = ''
    nos = []
    for l in text:

        if l.isdigit():
            n += l

        elif l in num_sep or l.isalpha():
            if n != '':
                nos.append(n)
                n = ''

        # print('n:', n)
        # print('nos:', nos)

    if n != '':
        nos.append(n)
        n = ''

    # print('n:', n)
    # print('nos:', nos)

    fnos = []
    for no in nos:
        if len(no) == 7:
            fnos.append(no[-7:-4] + ' ' + no[-4:])
        else:
            fnos.append('(' + no[:-7] + ') ' + no[-7:-4] + ' ' + no[-4:])

    return fnos


def _get_fax_number(fax, landline):
    # Get text to parse
    text = None
    if fax:
        text = fax.lower()

    elif landline:
        landline = landline.lower()
        if 'fax' in landline:
            text = landline
    # return text
    # Parse text
    if text:
        if not 'fax' in text:
            return _parse_number(text)
            # return None
        else:
            if text.count('tel') < 2:
                return _parse_number(text)
                # return None
            else:
                subtext = text[text.find('telefax'):]
                end = subtext.rfind('tel')
                if end > 0:
                    subtext = subtext[:end]
                # return subtext
                return _parse_number(subtext)
    else:
        return []


def _get_lgu_info(lgu, attrib=None):
    # attrib: [address, fax, email]
    m, p = lgu.split(',')
    municipality = m.lower().replace('city', '').strip()

    # Workarounds
    if municipality == 'albuquerque':
        municipality = 'alburquerque'

    elif municipality == 'kalookan':
        municipality = 'caloocan'

    elif municipality == 'padre garcia':
        municipality = 'padre v. garcia'

    elif municipality == 'alfonso lista':
        municipality = 'alfonso lista (potia)'

    elif municipality == 'banna':
        municipality = 'banna (espiritu)'

    elif municipality == 'enrique b. magalona':
        municipality = 'e.b. magalona'

    elif municipality == 'general nakar':
        municipality = 'gen. nakar'

    elif municipality == 'lal-lo':
        municipality = 'lallo'

    elif municipality == 'ma ayon':
        municipality = 'ma-ayon'

    elif municipality == 'panitan':
        municipality = 'panit-an'

    elif municipality == 'paoay lake':
        municipality = 'paoay'

    elif municipality == 'peñablanca':
        municipality = 'penablanca'

    elif municipality == 'rodriguez':
        municipality = 'rodriguez (montalban)'

    province = p.lower().strip()

    if province == 'metropolitan manila':
        province = 'ncr'

    if ((municipality == 'santa barbara' and province == 'iloilo') or
            (municipality == 'santa catalina' and province == 'ilocos sur') or
            (municipality == 'santa cruz' and province == 'davao del sur') or
            (municipality == 'santa maria' and province == 'isabela') or
            (municipality == 'santa teresita' and province == 'cagayan') or
            (municipality == 'santo domingo' and province == 'ilocos sur') or
            (municipality == 'santo tomas' and province == 'davao del norte') or
            (municipality == 'santo tomas' and province == 'la union')):
        municipality = municipality.replace(
            'santa', 'sta.').replace(
            'santo', 'sto.')

    if municipality == 'santo niño' and province == 'cagayan':
        municipality = 'sto. nino'
    if municipality == 'santo tomas' and province == 'isabela':
        municipality = 'sto.tomas'

    dbcur.execute('''SELECT * FROM lgu
                     WHERE municipality = :municipality AND
                     province = :province''',
                  {'municipality': municipality,
                   'province': province})
    row = dbcur.fetchone()
    # if len(rows) > 1:

    # for row in rows:
    #     print('-' * 20)
    #     for k, v in zip(row.keys(), row):
    #         print(k + ':', v)
    # pprint(row)

    if row and attrib:
        # print([v for v in row])

        if attrib == 'address':
            return row['address']

        elif attrib == 'email':
            if row['email']:
                email = row['email']
                # if email.count('@') > 1:
                if email:
                    # Extract all emails
                    return re.findall(r'([\w\.-]+@[\w\.-]+)', email.lower())
                # elif email.count('@') == 1:
                #     return [email.lower()]
            else:
                return []

        elif attrib == 'fax':
            return _get_fax_number(row['fax'], row['landline'])

            # if row['fax']:
            #     return row['fax']

            # elif row['landline']:
            #     landline = row['landline'].lower()
            #     if 'fax' in landline:
            #         return landline


if __name__ == '__main__':

    print('Initialize db...')
    dbcon, dbcur = _init_db()

    # print('Inserting LGUs to db...')
    # _parse_all_lgu_csv()

    print('Reading DREAM LGU list...')
    dream_lgus = _parse_dream_lgu_csv()
    # pprint(dream_lgus)

    for lgu in sorted(dream_lgus):
        # v = _get_lgu_info(lgu, 'fax')
        # if v:
        #     print('#' * 40)
        #     print(lgu)
        #     print(v)
            # break
        print('#' * 40)
        print(lgu)
        for attrib in ['address', 'email', 'fax']:
            print(attrib + ':', _get_lgu_info(lgu, attrib))
