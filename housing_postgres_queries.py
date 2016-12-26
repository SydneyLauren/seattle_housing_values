from __future__ import division
import psycopg2
import matplotlib.pyplot as plt
from collections import defaultdict
import numpy as np


def database_connect(dbnm, username):
    '''
    INPUT: name of existing postgres database, username
    OUTPUT: database connection and cursor
    Take database name and username and establish conncetion to database
    '''
    conn = psycopg2.connect(dbname=dbnm, user=username, host='/tmp')
    c = conn.cursor()
    return conn, c


# connect to the database
conn, c = database_connect('housingdata_clean', 'sydneydecoto')

'''calculate the percent increase in houses built each decade (rounding to nearest 10 years)'''
c.execute('''SELECT ROUND(year/10)*10
    , ROUND(100 * SUM(COUNT(address))
        OVER (ORDER BY ROUND(year/10)*10) / (SELECT COUNT(address) FROM housing_data), 2)
        AS running_total
    FROM housing_data
    GROUP BY ROUND(year/10)*10;''')

header = '\n{:>6} | {:>10}\n'.format('Year',  '% Built')
print header, '-'*len(header)
for d in c.fetchall():
    print '{:>6} | {:>10}'.format(int(d[0]), d[1])


'''find the 10 neighborhoods with recent growth based on percent of houses built between 2014 and 2016'''
c.execute('''SELECT hood, 100 * A.total2016 / A.total :: float AS PctInc14_16
                FROM (SELECT
                       hood
                       , COUNT(address) AS total
                       , SUM( CASE WHEN year > 2013 THEN 1 ELSE 0 END) AS total2016
                      FROM housing_data
                      GROUP BY hood) AS A
                WHERE hood IS NOT null
                ORDER BY PctInc14_16 DESC
                LIMIT 10;''')

header = '\n{} | {}\n'.format('Neighborhood    ', 'Pct Inc House Count Since 2014')
print header, '-'*len(header)
for d in c.fetchall():
    print '{:>16} | {:14.2f}'.format(d[0], d[1])

'''Find the neighborhoods that have seen the highest percent increase in home value
between 2015 and 2016.'''

c.execute('''SELECT hood, 100 * AVG((v2016 - v2015) / v2015) AS PctInc
             FROM housing_data
             WHERE v2016 > 1000 AND v2015 > 1000 AND hood IS NOT null
             GROUP BY hood
             HAVING COUNT(address) > 300 AND 100 * AVG((v2016 - v2015) / v2015) > 2
             ORDER BY PctInc DESC;''')

header = '\n{:>22} | {}\n'.format('Neighborhood', 'Pct Inc Value 2016')
print header, '-'*len(header)
increased_value_hoods = []
for d in c.fetchall():
    print '{:>22} | {:14.2f}'.format(d[0], d[1])
    increased_value_hoods.append(d[0])


'''Plot percent growth (new construction) over time for each neighborhood'''
c.execute('''SELECT hood, year, SUM(COUNT(address))
             OVER (PARTITION BY hood ORDER BY year)
             FROM housing_data
             GROUP BY hood, year
             ORDER BY hood;''')

house_counts = c.fetchall()
house_dict = defaultdict(list)

for hc in house_counts:
    house_dict[hc[0]].append((hc[1], int(hc[2])))
plt.figure(figsize=(10, 5))
legend_text = []
for k in house_dict:
    if k in increased_value_hoods:
        years, count = zip(*house_dict[k])
        plt.plot(years, np.array(count) / max(count), lw=2)
        legend_text.append(k)
# plt.figsize([10,4])
plt.xlabel('Year')
plt.ylabel('Percent of houses built')
# plt.legend(legend_text, fontsize=9,bbox_to_anchor=(1.3, 1))
plt.legend(legend_text, loc='center left', bbox_to_anchor=(1, 0.5),prop={'size':9})
plt.subplots_adjust(left=0.1, right=0.8, top=0.9, bottom=0.1)
# plt.tight_layout(pad=7)

plt.show()
years = [t[0] for t in pct_data]
construction_increase = [t[1] for t in pct_data]
plt.plot(years, )
conn.commit()
conn.close()
