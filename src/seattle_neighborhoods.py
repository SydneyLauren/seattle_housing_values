from __future__ import division
#import psycopg2
import pandas as pd
import numpy as np
from matplotlib.patches import Polygon
import matplotlib
from matplotlib.collections import PatchCollection
from mpl_toolkits.basemap import Basemap
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon
from shapely.prepared import prep
import fiona
from descartes import PolygonPatch
# import matplotlib.pyplot as plt
# from matplotlib.path.Path import contains_points


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

    df = pd.DataFrame({
        'poly': [Polygon(points) for points in m.seattle],
        'name': [item[df_key] for item in m.seattle_info],
    })
    return _out, df


def assign_neighborhood(lat, lon):
    # Read in neighborhood shape file
    hood_shapefilename = '/Users/sydneydecoto/Documents/PythonScripts/Neighborhoods/WGS84/Neighborhoods'
    hood_coords = parse_shapes(hood_shapefilename)

    w, h = hood_coords[2] - hood_coords[0], hood_coords[3] - hood_coords[1]
    extra = 0.005

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

    # map neighborhoods to polygon patches
    df_map['patches'] = df_map['poly'].map(lambda x: PolygonPatch(x, ec='#111111', lw=.8, alpha=1., zorder=4))

    # convert latitude and longitude to point on basemap
    xpt, ypt = m(lon, lat)
    pt = Point(xpt, ypt)

    # loop through neighborhoods until neighborhood containing point is found
    for polygon in df_map['poly']:
        hood_name = df_map.loc[df_map['poly'] == polygon, 'name'].iloc[0]
        if len(hood_name.strip()) < 4:
            continue
        if polygon.contains(pt):
            return hood_name
