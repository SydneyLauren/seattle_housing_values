from __future__ import division
import multiprocessing
import pandas as pd
import numpy as np
import psycopg2
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import matplotlib
from matplotlib.collections import PatchCollection
from mpl_toolkits.basemap import Basemap
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon
from shapely.prepared import prep
import fiona
from descartes import PolygonPatch
import matplotlib.pyplot as plt
from collections import defaultdict


def database_connect(dbnm, username):
    '''
    INPUT: name of existing postgres database, username
    OUTPUT: database connection and cursor
    Take database name and username and establish conncetion to database
    '''
    conn = psycopg2.connect(dbname=dbnm, user=username, host='/tmp')
    c = conn.cursor()
    return conn, c


def remove_rows(df, colname, colval):
    '''
    INPUT: dataframe, column name, column value
    OUTPUT: dataframe
    take a dataframe and remove all rows in which the value for colname = colval
    '''
    return df[df[colname] != colval]


def remove_outliers(df, colname, iqr_mult):
    '''
    INPUT: dataframe, column name, multiplier for inter quartile range
    OUTPUT: dataframe
    take a dataframe and return a dataframe with outliers removed
    '''
    print colname
    q1 = df[colname].quantile(.25)
    q3 = df[colname].quantile(.75)
    iqr = df[colname].quantile(.75) - df[colname].quantile(.25)  # calculate interquartile range
    df = df[df[colname] >= q1 - iqr * iqr_mult]  # remove low outliers
    df = df[df[colname] <= q3 + iqr * iqr_mult]  # remove high outliers
    return df


conn, c = database_connect('housingdata_clean', 'sydneydecoto')

c.execute("SELECT * FROM housing_data LIMIT 10")
data = c.fetchall()

c.execute("SELECT v2015 FROM housing_data")
val2015 = c.fetchall()
c.execute("SELECT v2016 FROM housing_data")
val2016 = c.fetchall()
c.execute("SELECT hood FROM housing_data")
hoods = c.fetchall()
conn.commit()
conn.close()

df = pd.DataFrame()
df['Neighborhood'] = [hood_name[0] for hood_name in hoods]
df['value_2015'] = [v[0] for v in val2015]
df['value_2016'] = [v[0] for v in val2016]
df['pct_inc16'] = (df['value_2016'] - df['value_2015']) / df['value_2015']*100.

print df.head()

'''remove bad data (null values, zero home values)'''
df.dropna(axis=0, inplace=True)
df = remove_rows(df, 'value_2015', 0)
df = remove_rows(df, 'value_2016', 0)
df = remove_outliers(df, 'pct_inc16', 3)
df.info()

grouped = df.groupby(['Neighborhood']).mean()
hoods = np.array(grouped.index)
pctincs = np.array(grouped['pct_inc16'])

print '{} has maximum value increase of {}%'.format(hoods[pctincs == max(pctincs)][0], round(max(pctincs), 1))
print '{} has minimum value increase of {}%'.format(hoods[pctincs == min(pctincs)][0], round(min(pctincs), 1))

df_permits = pd.read_csv('data/permitting.csv')  # Load the data from csv
dates = pd.to_datetime(df_permits['Application Date'])  # Convert Application Date column to datetime
df_permits['year'] = [d.year for d in dates]   # Retrieve year from date and add year column to dataframe
df_permits = df_permits[df_permits.year == 2015]  # keep all 2015 data
df_permits.dropna(axis=0, subset=['Latitude', 'Longitude'], inplace=True)  # drop rows with no latitude and longitude
lons = df_permits['Longitude']
lats = df_permits['Latitude']


def parse_shapes(shapefilepath):
    '''Read in a shape file (.shp) and return coordinates and dataframe for plotting'''
    shp = fiona.open(shapefilepath+'.shp')
    coords = shp.bounds
    shp.close
    return coords


def plot_prepper(m, shapefilename, df_key):
    '''Generate dataframe for plotting'''
    _out = m.readshapefile(shapefilename, name='seattle', drawbounds=False, color='none', zorder=2)
    # set up a map dataframe for neighborhood outlines
    cent_lons = [float((Polygon(points).centroid.wkt).split()[1][1:]) for points in m.seattle]
    cent_lats = [float((Polygon(points).centroid.wkt).strip(')').split()[2]) for points in m.seattle]

    df = pd.DataFrame({
        'poly': [Polygon(points) for points in m.seattle],
        'name': [item[df_key] for item in m.seattle_info],
    })
    df['centroid_1'] = cent_lons
    df['centroid_2'] = cent_lats
    return _out, df

# Read in neighborhood shape file

hood_shapefilename = '/Users/sydneydecoto/Documents/PythonScripts/Neighborhoods/WGS84/Neighborhoods'
hood_coords = parse_shapes(hood_shapefilename)

w, h = hood_coords[2] - hood_coords[0], hood_coords[3] - hood_coords[1]
extra = 0.005

# Initialize the plot
figwidth = 8
fig = plt.figure(figsize=(figwidth, figwidth*h/w))
ax = fig.add_subplot(111, axisbg='w', frame_on=False)
m = Basemap(
    projection='tmerc', ellps='WGS84',
    lon_0=np.mean([hood_coords[0], hood_coords[2]]),
    lat_0=np.mean([hood_coords[1], hood_coords[3]]),
    llcrnrlon=hood_coords[0] - extra * w,
    llcrnrlat=hood_coords[1] - (extra * h),
    urcrnrlon=hood_coords[2] + extra * w,
    urcrnrlat=hood_coords[3] + (extra * h),
    resolution='i',  suppress_ticks=True)

# get dataframe for plotting
_out, df_map = plot_prepper(m, hood_shapefilename, 'S_HOOD')
nbr_names = df_map['name'].unique()

pt = []
count = 0

pt = [Point(m(mapped_x, mapped_y)) for mapped_x, mapped_y in zip(lons, lats)]


def get_neighborhood(p):
    label = 'no neighborhood'
    for polygon in df_map['poly']:
        nm = df_map.loc[df_map['poly'] == polygon, 'name'].iloc[0]
        if polygon.contains(p) and len(nm.strip()) >= 4:
            return label
    return label

print pt[0]
l = get_neighborhood(pt[0])
print l
asdasd


pool = multiprocessing.Pool(4)
output = pool.map(get_neighborhood, pt[:10])
print output
df_permits['Neighborhood'] = output
df_permits.to_csv('permits_data.csv', sep=',')
