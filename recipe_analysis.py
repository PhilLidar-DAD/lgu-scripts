#!/usr/bin/env python2

from __future__ import division
from collections import defaultdict
from pprint import pprint
from datetime import timedelta
import itertools
import json
import sqlite3

_version = '2016-02-12_23:46'


def _format_cost(c):
    g = int(c / 10000)
    g_s = str(g) + 'g ' if g > 0 else ''
    s = int((c - g * 10000) / 100)
    s_s = str(s) + 's ' if s > 0 else ''
    c = int(c - g * 10000 - s * 100)
    c_s = str(c) + 'c' if c > 0 else''
    return g_s + s_s + c_s


### Read JSON file ###
recipes = json.load(open('recipes.json', 'r'))
# pprint(recipes)


### Initialize db ###
con = sqlite3.connect("recipes.db")
con.row_factory = sqlite3.Row
c = con.cursor()
with con:
    # c.execute('''PRAGMA journal_mode = OFF''')
    con.execute('''PRAGMA foreign_keys = ON''')
    # Create tables
    # Create base table
    con.execute('''CREATE TABLE IF NOT EXISTS
                   base (
                        item TEXT PRIMARY KEY,
                        market_cost_pu INTEGER,
                        guild TEXT,
                        units INTEGER,
                        order_duration INTEGER,
                        order_duration_pu REAL,
                        order_cost INTEGER,
                        order_cost_pu REAL,
                        combo_count INTEGER)''')
    # Create recipes table
    con.execute('''CREATE TABLE IF NOT EXISTS
                   recipes (
                        recipe TEXT,
                        ingr TEXT,
                        ingr_units INTEGER,
                        PRIMARY KEY(recipe, ingr),
                        FOREIGN KEY(recipe) REFERENCES base(item),
                        FOREIGN KEY(ingr) REFERENCES base(item))''')
    # Create combos table
    con.execute('''CREATE TABLE IF NOT EXISTS
                   combos (
                        recipe TEXT,
                        combo_id INTEGER,
                        ingr TEXT,
                        source TEXT,
                        total_dur_per_ingr INTEGER,
                        total_cost_per_ingr INTEGER,
                        total_dur INTEGER,
                        total_dur_pu REAL,
                        total_cost INTEGER,
                        total_cost_pu REAL,
                        profit_pu REAL,
                        profit_pupd REAL,
                        profit_pupd_tier INTEGER,
                        PRIMARY KEY(recipe, combo_id, ingr, source),
                        FOREIGN KEY(recipe, ingr)
                            REFERENCES recipes(recipe,ingr))''')


### Update base table ###
print('Updating base table...')
for item, data in recipes['base'].items():
    params = defaultdict(lambda: None, data)
    params['item'] = item

    if 'units' in data:
        if 'order_duration' in data:
            params['order_duration_pu'] = (data['order_duration'] /
                                           data['units'])
        if 'order_cost' in data:
            # print 'Yes!'
            params['order_cost_pu'] = (data['order_cost'] /
                                       data['units'])

    else:
        params['units'] = 1

    # print '\nitem:', params['item']
    # print "params['order_duration']:", params['order_duration']
    # print "params['units']:", params['units']
    # print "params['order_duration_pu']:", params['order_duration_pu']
    # print "params['order_cost']:", params['order_cost']
    # print "params['order_cost_pu']:", params['order_cost_pu']

    with con:
        con.execute('''UPDATE base
                       SET market_cost_pu = :market_cost_pu
                       WHERE item = :item''', params)
        con.execute('''INSERT OR IGNORE INTO base
                       VALUES (:item, :market_cost_pu, :guild, :units,
                               :order_duration, :order_duration_pu, :order_cost,
                               :order_cost_pu, :combo_count)''',
                    params)


### Update recipe table ###
print('Updating recipe table...')
for recipe, data in recipes['recipes'].items():
    for ingr, ingr_units in data['ingr'].items():
        with con:
            con.execute('''INSERT OR IGNORE INTO recipes
                           VALUES (:recipe, :ingr, :ingr_units)''',
                        {'recipe': recipe,
                         'ingr': ingr,
                         'ingr_units': ingr_units})


### Compute combinations count ###
print('Computing combinations count...')

with con:
    con.execute('''CREATE VIEW IF NOT EXISTS max_count_view AS
                       SELECT   b1.item,
                                b1.order_cost AS item_oc,
                                b1.combo_count,
                                b1.units,
                                b1.order_duration,
                                b1.order_duration_pu,
                                t2.recipe,
                                t2.ingr,
                                t2.ingr_units,
                                t2.ingr_oc,
                                t2.ingr_cc
                       FROM base as b1
                       LEFT JOIN
                           (SELECT  r2.recipe,
                                    r2.ingr,
                                    r2.ingr_units,
                                    b2.order_cost AS ingr_oc,
                                    b2.combo_count AS ingr_cc
                            FROM recipes AS r2
                            INNER JOIN base AS b2 ON r2.ingr = b2.item) t2
                            ON b1.item = t2.recipe''')

while True:
    c.execute('''SELECT item, item_oc, recipe FROM max_count_view
                 WHERE combo_count IS NULL
                 GROUP BY item, item_oc, recipe''')
    row1s = c.fetchall()

    if len(row1s) == 0:
        break

    for row1 in row1s:

        skip_item = False
        combos = 0
        item, item_oc, recipe = row1

        print 'item:', item

        if not item_oc is None:
            # Item is gatherable/craftable
            combos = 1
            if not recipe is None:
                # Item is craftable
                c.execute('''SELECT ingr, ingr_cc FROM max_count_view
                             WHERE item = ?''', (item,))
                for row2 in c.fetchall():
                    ingr, ingr_cc = row2
                    if ingr_cc is None:
                        skip_item = True
                        break
                    combos *= ingr_cc

        if skip_item:
            continue

        # Add 1 for market
        combos += 1

        print 'combos:', combos

        # Update combo_count db
        with con:
            con.execute('''UPDATE base SET combo_count = :combo_count
                           WHERE item = :item''', {'combo_count': combos,
                                                   'item': item})


### Generate any missing combo & compute total craft duration ###
print 'Generating any missing combo & computing total craft duration...'

with con:
    con.execute('''CREATE VIEW IF NOT EXISTS combos_all_view AS
                    SELECT
                            c1.recipe,
                            c1.combo_id,
                            b1.market_cost_pu,
                            b1.units,
                            b1.order_duration,
                            b1.order_duration_pu,
                            b1.order_cost,
                            b1.order_cost_pu,
                            c1.ingr,
                            c1.ingr_units,
                            c1.source,
                            c1.total_dur_per_ingr,
                            c1.total_cost_per_ingr,
                            c1.total_dur,
                            c1.total_dur_pu,
                            c1.total_cost,
                            c1.total_cost_pu,
                            c1.profit_pu,
                            c1.profit_pupd,
                            c1.profit_pupd_tier
                    FROM (  SELECT *
                            FROM combos AS c2
                            LEFT JOIN recipes AS r2
                            ON c2.recipe = r2.recipe AND c2.ingr = r2.ingr) c1
                    INNER JOIN base as b1 ON c1.recipe = b1.item''')

    con.execute('''CREATE VIEW IF NOT EXISTS cur_count_view AS
                    SELECT *
                    FROM (
                        SELECT item, combo_count as max_count, units,
                               order_duration, order_duration_pu
                        FROM max_count_view
                        GROUP BY item) t1
                    LEFT JOIN (
                        SELECT recipe, MAX(combo_id) + 1 as cur_count
                        FROM combos_all_view
                        GROUP BY recipe) t2
                    ON t1.item = t2.recipe
                    GROUP BY item;''')


def _add_combo(params):
    with con:
        con.execute('''INSERT OR IGNORE INTO combos
                       VALUES (
                            :recipe,
                            :combo_id,
                            :ingr,
                            :source,
                            :total_dur_per_ingr,
                            :total_cost_per_ingr,
                            :total_dur,
                            :total_dur_pu,
                            :total_cost,
                            :total_cost_pu,
                            :profit_pu,
                            :profit_pupd,
                            :profit_pupd_tier)''', params)


c.execute('''SELECT item, cur_count, max_count, units,
                    order_duration, order_duration_pu
             FROM cur_count_view
             WHERE cur_count < max_count OR cur_count ISNULL
             ORDER BY max_count ASC''')
row1s = c.fetchall()

for row1 in row1s:
    item, _, _, units, order_duration, order_duration_pu = row1
    print 'item:', item

    # Check item if market only/gather/craft
    c.execute('''SELECT item_oc, units, ingr, ingr_units
                 FROM max_count_view
                 WHERE item = :item''', {'item': item})
    row2s = c.fetchall()

    # col_headers = True
    # for row2 in row2s:
    #     if col_headers:
    #         print '\t'.join(row2.keys())
    #         col_headers = False
    #     print '\t'.join([str(r) for r in row2])

    if len(row2s) > 1:
        # Item is craftable
        iterables = []
        for row2 in row2s:
            ingr = row2['ingr']
            # Get combo ids for ingr
            c.execute('''SELECT combo_id
                         FROM combos
                         WHERE recipe = :recipe
                         GROUP BY combo_id''', {'recipe': ingr})
            iterables.append([str(i[0]) for i in c.fetchall()])

        combo_id = 1
        for p in itertools.product(*iterables):
            total_dur = order_duration
            for source, row2 in itertools.izip(p, row2s):
                ingr = row2['ingr']
                ingr_units = row2['ingr_units']

                c.execute('''SELECT total_dur_pu
                             FROM combos
                             WHERE recipe = :recipe AND combo_id = :combo_id''',
                          {'recipe': ingr, 'combo_id': source})
                total_dur_pu = c.fetchone()[0]

                total_dur_per_ingr = ingr_units * total_dur_pu
                total_dur += total_dur_per_ingr

                params = defaultdict(lambda: None,
                                     {'recipe': item,
                                      'combo_id': combo_id,
                                      'ingr': ingr,
                                      'source': source,
                                      'total_dur_per_ingr':
                                      total_dur_per_ingr})
                _add_combo(params)

            units = row2['units']
            total_dur_pu = total_dur / units

            with con:
                con.execute('''UPDATE combos
                               SET  total_dur = :total_dur,
                                    total_dur_pu = :total_dur_pu
                               WHERE recipe = :recipe AND
                                     combo_id = :combo_id''',
                            {'recipe': item,
                             'combo_id': combo_id,
                             'total_dur': total_dur,
                             'total_dur_pu': total_dur_pu})

            combo_id += 1
    else:
        # Item is either market only or gatherable
        item_oc = row2s[0]['item_oc']
        # print 'item_oc:', item_oc
        if not item_oc is None:
            # Item is gatherable
            combo_id = 1
            source = 'G'
            total_dur = order_duration
            total_dur_pu = order_duration_pu
            params = defaultdict(lambda: None,
                                 {'recipe': item,
                                  'combo_id': combo_id,
                                  'source': source,
                                  'total_dur': total_dur,
                                  'total_dur_pu': total_dur_pu})
            _add_combo(params)

    # Add market option
    combo_id = 0
    source = 'M'
    total_dur = 1
    total_dur_pu = total_dur / units
    params = defaultdict(lambda: None,
                         {'recipe': item,
                          'combo_id': combo_id,
                          'source': source,
                          'total_dur': total_dur,
                          'total_dur_pu': total_dur_pu})
    _add_combo(params)


# exit(1)
### Update costs ###
print 'Updating costs...'


def _update_combo_cost(params):
    with con:
        con.execute('''UPDATE combos
                       SET  total_cost = :total_cost,
                            total_cost_pu = :total_cost_pu,
                            profit_pu = :profit_pu,
                            profit_pupd = :profit_pupd,
                            profit_pupd_tier = :profit_pupd_tier
                        WHERE recipe = :recipe AND combo_id = :combo_id''',
                    params)

c.execute('''SELECT *, MAX(combo_id) + 1 as count
             FROM combos_all_view
             GROUP BY recipe
             ORDER BY count ASC''')
for row1 in c.fetchall():
    recipe = row1['recipe']
    market_cost_pu = row1['market_cost_pu']
    units = row1['units']
    order_cost = row1['order_cost']
    order_cost_pu = row1['order_cost_pu']

    # print 'recipe:', recipe
    # print 'market_cost_pu:', market_cost_pu

    for combo_id in range(row1['count']):

        # print 'combo_id:', combo_id

        c.execute('''SELECT ingr, ingr_units, source, total_dur_pu
                     FROM combos_all_view
                     WHERE recipe = :recipe AND combo_id = :combo_id''',
                  {'recipe': recipe, 'combo_id': combo_id})
        row2s = c.fetchall()

        if len(row2s) > 1:
            # Item is craftable
            total_cost = order_cost
            for row2 in row2s:
                ingr = row2['ingr']
                ingr_units = row2['ingr_units']
                source = row2['source']

                c.execute('''SELECT total_cost_pu
                             FROM combos_all_view
                             WHERE recipe = :recipe AND combo_id = :combo_id''',
                          {'recipe': ingr, 'combo_id': source})
                total_cost_pu = c.fetchone()[0]

                total_cost_per_ingr = ingr_units * total_cost_pu
                total_cost += total_cost_per_ingr

                with con:
                    con.execute('''UPDATE combos
                                   SET total_cost_per_ingr =
                                   :total_cost_per_ingr
                                   WHERE recipe = :recipe AND
                                         combo_id = :combo_id AND
                                         ingr = :ingr''',
                                {'recipe': recipe,
                                 'combo_id': combo_id,
                                 'ingr': ingr,
                                 'total_cost_per_ingr': total_cost_per_ingr})

            total_cost_pu = total_cost / units
            profit_pu = market_cost_pu - total_cost_pu
            total_dur_pu = row2['total_dur_pu']
            profit_pupd = profit_pu / total_dur_pu * 60 * 24
            profit_pupd_tier = int(profit_pupd / 10000)
            params = defaultdict(lambda: None,
                                 {'recipe': recipe,
                                  'combo_id': combo_id,
                                  'total_cost': total_cost,
                                  'total_cost_pu': total_cost_pu,
                                  'profit_pu': profit_pu,
                                  'profit_pupd': profit_pupd,
                                  'profit_pupd_tier': profit_pupd_tier})
            _update_combo_cost(params)

        else:
            source = row2s[0]['source']
            # print 'source:', source
            if source == 'G':
                # Item source is gather
                total_cost = order_cost
                total_cost_pu = total_cost / units
                # print 'total_cost_pu:', total_cost_pu
                profit_pu = market_cost_pu - total_cost_pu
                # print 'profit_pu:', profit_pu
                total_dur_pu = row2s[0]['total_dur_pu']
                # print 'total_dur_pu:', total_dur_pu
                profit_pupd = profit_pu / total_dur_pu * 60 * 24
                profit_pupd_tier = int(profit_pupd / 10000)
                params = defaultdict(lambda: None,
                                     {'recipe': recipe,
                                      'combo_id': combo_id,
                                      'total_cost': total_cost,
                                      'total_cost_pu': total_cost_pu,
                                      'profit_pu': profit_pu,
                                      'profit_pupd': profit_pupd,
                                      'profit_pupd_tier': profit_pupd_tier})
                _update_combo_cost(params)

            elif source == 'M':
                # Item source is market
                total_cost_pu = market_cost_pu
                params = defaultdict(lambda: None,
                                     {'recipe': recipe,
                                      'combo_id': combo_id,
                                      'total_cost_pu': total_cost_pu})
                _update_combo_cost(params)


### Create report ###
print 'Creating report...'
with con:
    con.execute('''CREATE VIEW IF NOT EXISTS summary AS
                    SELECT  recipe,
                            combo_id,
                            market_cost_pu,
                            units,
                            total_dur,
                            total_dur_pu,
                            total_cost,
                            total_cost_pu,
                            profit_pu,
                            profit_pupd,
                            profit_pupd_tier
                    FROM combos_all_view
                    GROUP BY recipe, combo_id
                    ORDER BY profit_pupd_tier DESC, profit_pu DESC''')


def _breakdown(recipe, combo_id, d):

    c.execute('''SELECT ingr,
                        ingr_units,
                        source,
                        total_dur_per_ingr,
                        total_cost_per_ingr
                 FROM combos_all_view
                 WHERE recipe = :recipe AND combo_id = :combo_id''',
              {'recipe': recipe, 'combo_id': combo_id})

    rows = c.fetchall()

    if len(rows) == 1:
        s1 = rows[0]['source']
        print 'S:', s1

    else:
        print ''
        print '-' * 40
        for row in rows:
            i1 = row['ingr']
            iu1 = row['ingr_units']
            s1 = row['source']
            tdpi1 = row['total_dur_per_ingr']
            tcpi1 = row['total_cost_per_ingr']

            print ' ' * d, 'x' + str(iu1), i1, \
                'D:', timedelta(minutes=tdpi1) if tdpi1 else tdpi1, \
                'C:', _format_cost(tcpi1) if tcpi1 else tcpi1,

            _breakdown(i1, s1, d + 4)

        print '-' * 40

c.execute('''SELECT *
             FROM summary
             WHERE NOT profit_pupd IS NULL AND profit_pu > 10000
             ORDER BY profit_pu DESC''')

top = {}
for row1 in c.fetchall():
    recipe = row1['recipe']

    # if not recipe in top:
    #     top[recipe] = 0
    # top[recipe] += 1
    # if top[recipe] > 10:
    #     continue

    combo_id = row1['combo_id']
    market_cost_pu = row1['market_cost_pu']
    units = row1['units']
    total_dur = row1['total_dur']
    total_dur_pu = row1['total_dur_pu']
    total_cost = row1['total_cost']
    total_cost_pu = row1['total_cost_pu']
    profit_pu = row1['profit_pu']
    profit_pupd = row1['profit_pupd']
    profit_pupd_tier = row1['profit_pupd_tier'] * 10000

    print '\n', '#' * 80, '\n'
    print 'recipe:\t{0}\n'.format(recipe)

    print 'profit_pupd_tier:\t{0}'.format(_format_cost(profit_pupd_tier) if profit_pupd_tier else profit_pupd_tier)
    print 'profit_pupd:\t{0}'.format(_format_cost(profit_pupd) if profit_pupd else profit_pupd)
    print 'profit_pu:\t{0}'.format(_format_cost(profit_pu) if profit_pu else profit_pu)
    print 'market_cost_pu:\t{0}'.format(_format_cost(market_cost_pu))
    print 'total_cost:\t{0}'.format(_format_cost(total_cost))
    print 'total_cost_pu:\t{0}\n'.format(_format_cost(total_cost_pu))

    print 'total_dur:\t{0}'.format(timedelta(minutes=total_dur))
    print 'total_dur_pu:\t{0}'.format(timedelta(minutes=total_dur_pu))

    _breakdown(recipe, combo_id, 0)

con.close()
# exit(1)
