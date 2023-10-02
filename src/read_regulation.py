import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
import contextily as ctx
from shapely.geometry import Point, LineString
import glob

# doc: ../data/raw/14-Hackathon/03_R├йgulation_mouvements_stations/Descriptif_r├йgulation_mouvements_stations.txt
# file = "../data/raw/14-Hackathon/03_R├йgulation_mouvements_stations/2023_02/2023-02-01_Mouvements_de_r├йgulation.csv"
# regulation = pd.read_csv(file)
files = glob.glob("../data/raw/14-Hackathon/03_R├йgulation_mouvements_stations/2023_02/*.csv")
files.sort()

regulation = pd.DataFrame()
list_df = [pd.read_csv(file) for file in files]
for i, df in enumerate(list_df):
    df["day"] = i + 1

regulation = pd.concat(list_df)

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
departements = gpd.read_file("../data/raw/departements.geojson").to_crs(epsg=3857)

departements_idf_no_paris = departements[departements["code"].isin(["92", "93", "94", "78", "91", "77", "95"])]
departements_petite_couronne_no_paris = departements[departements["code"].isin(["92", "93", "94"])]

# departements_idf_no_paris.to_file("../data/raw/departements_idf_no_paris.geojson", driver='GeoJSON')
# departements_petite_couronne_no_paris.to_file("../data/raw/departements_petite_couronne_no_paris.geojson", driver='GeoJSON')
all_districts = pd.concat([districts, departements_petite_couronne_no_paris])


# plot all operations for first day
regulation_day_1_start = regulation_start[regulation_start["day"] == 1]
regulation_day_1_end = regulation_end[regulation_end["day"] == 1]
regulation_day_1_line = regulation_line[regulation_line["day"] == 1]

fig, ax = plt.subplots()
all_districts.plot(ax=ax, alpha=0.5, edgecolor="white")
# plot points and lines
regulation_day_1_start.plot(ax=ax, color = "green")
regulation_day_1_end.plot(ax=ax, color = "red")
regulation_day_1_line.plot(ax=ax, color = "lightblue")
ax.set_axis_off()
ctx.add_basemap(ax)


plt.savefig('../img/regulation_first_night.png')

plt.show()


# velib added - velib taken by district 
all_districts["velib_added"] = all_districts.apply(
    lambda district: (
        (regulation_end.within(district.geometry) * regulation_end["Total"]) - (regulation_start.within(district.geometry) * regulation_start["Total"]) 
    ).sum(),
    axis=1
)

fig, ax = plt.subplots(figsize=(8, 6))
all_districts.plot("velib_added", cmap="PuOr", ax=ax, alpha=0.5, edgecolor="white", legend=True)
ax.set_axis_off()
ctx.add_basemap(ax)
plt.savefig('../img/all_regulation_february.png')
plt.show()

# should be 0, somehow is -12, maybe some stations are not in the polygons
# sum(all_districts["velib_added"])

