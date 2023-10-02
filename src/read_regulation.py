import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
import contextily as ctx
from shapely.geometry import Point, LineString

# doc: ../data/raw/14-Hackathon/03_R├йgulation_mouvements_stations/Descriptif_r├йgulation_mouvements_stations.txt
file = "../data/raw/14-Hackathon/03_R├йgulation_mouvements_stations/2023_02/2023-02-01_Mouvements_de_r├йgulation.csv"
regulation = pd.read_csv(file)
regulation.head()
regulation.columns

regulation["Latitude station prise"] = regulation["Latitude station prise"].str.replace(',', '.').astype(float)
regulation["Longitude station prise"] = regulation["Longitude station prise"].str.replace(',', '.').astype(float)
regulation["Latitude station dépose"] = regulation["Latitude station dépose"].str.replace(',', '.').astype(float)
regulation["Longitude station dépose"] = regulation["Longitude station dépose"].str.replace(',', '.').astype(float)

geometry_start = gpd.points_from_xy(regulation["Longitude station prise"], regulation["Latitude station prise"])
geometry_end = gpd.points_from_xy(regulation["Longitude station dépose"], regulation["Latitude station dépose"])
geometry_line = [(LineString([[a.x, a.y],[b.x, b.y]]) if b!=None else None) for (a,b) in zip(geometry_start, geometry_end)]

regulation_start = gpd.GeoDataFrame(regulation, crs=4326, geometry=geometry_start)
regulation_end = gpd.GeoDataFrame(regulation, crs=4326, geometry=geometry_end)
regulation_line = gpd.GeoDataFrame(regulation, crs=4326, geometry=geometry_line)
regulation_start = regulation_start.to_crs(epsg = 3857)
regulation_end = regulation_end.to_crs(epsg = 3857)
regulation_line = regulation_line.to_crs(epsg = 3857)
districts = gpd.read_file("../data/raw/quartier_paris.geojson").to_crs(epsg=3857)

fig, ax = plt.subplots()
districts.plot(ax=ax, alpha=0.5, edgecolor="white")
# plot points and lines
regulation_start.plot(ax=ax, color = "green")
regulation_end.plot(ax=ax, color = "red")
regulation_line.plot(ax=ax, color = "lightblue")
ax.set_axis_off()
ctx.add_basemap(ax)


plt.savefig('../img/regulation_first_night.png')

# plt.show()
