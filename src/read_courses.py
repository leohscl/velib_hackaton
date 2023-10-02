import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
import contextily as ctx
from shapely.geometry import Point, LineString
import glob


files = glob.glob("../data/raw/14-Hackathon/01_Courses_usagers/2023_02/*.csv")
files.sort()
courses = pd.DataFrame()
list_df = [pd.read_csv(file) for file in files]
courses = pd.concat(list_df)


# QC

courses["Latitude station départ"] = courses["Latitude station départ"].str.replace(',', '.').astype(float)
courses["Longitude station départ"] = courses["Longitude station départ"].str.replace(',', '.').astype(float)
courses["Latitude station arrivée"] = courses["Latitude station arrivée"].str.replace(',', '.').astype(float)
courses["Longitude station arrivée"] = courses["Longitude station arrivée"].str.replace(',', '.').astype(float)

geometry = gpd.points_from_xy(courses["Longitude station départ"], courses["Latitude station départ"])

geo_stations = gpd.GeoDataFrame(
    courses, crs=4326, geometry=geometry
)

geo_stations = geo_stations.to_crs(epsg = 3857)
districts = gpd.read_file("../data/raw/quartier_paris.geojson").to_crs(epsg=3857)
courses_velo_specifique = geo_stations[geo_stations["Numéro de Vélo"] == 2041]
courses_velo_specifique["trip_number"] = range(courses_velo_specifique.shape[0])
# only plot 30 data points
courses_velo_specifique = courses_velo_specifique[courses_velo_specifique["trip_number"] < 20]
courses_velo_specifique['LINE'] = [(LineString([[a.x, a.y],[b.x, b.y]]) if b!=None else None) for (a,b) in zip(courses_velo_specifique.geometry, courses_velo_specifique.geometry.shift(-1, axis=0))]
courses_velo_lines = gpd.GeoDataFrame(courses_velo_specifique, geometry='LINE')


fig, ax = plt.subplots()
districts.plot(ax=ax, alpha=0.5, edgecolor="white")
# add alternating colors for lines
colors = ['r' if i % 2 == 0 else 'g' for i in range(courses_velo_lines.shape[0])]

# plot points and lines
courses_velo_specifique.plot(ax=ax)
courses_velo_lines.plot(ax=ax, colors = colors)
# geo_stations

# add numbers
for x, y, label in zip(courses_velo_specifique.geometry.x, courses_velo_specifique.geometry.y, courses_velo_specifique.trip_number):
    ax.annotate(label, xy=(x, y), xytext=(3, 3), textcoords="offset points")

ax.set_axis_off()
ctx.add_basemap(ax)
plt.show()
#plt.savefig('../img/one_velib_30_trips.png')
