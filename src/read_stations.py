import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
import contextily as ctx
from shapely.geometry import Point, LineString
import glob

month_codes = ["02", "06"]
month_names = ["February", "June"]
for i in range(len(month_names)):
    month_name = month_names[i]
    month_code = month_codes[i]
    # doc: ../data/raw/14-Hackathon/02_Historique_remplissage_stations/Descriptif_historique_remplissage_stations.txt
    directory = "../data/raw/14-Hackathon/02_Historique_remplissage_stations/2023_" + month_code
    files = glob.glob(directory + "/*.csv")
    files.sort()
    list_df = [pd.read_csv(file) for file in files]
    for i, df in enumerate(list_df):
        df["day"] = i + 1

    stations = pd.concat(list_df)
    stations["longitude"] = stations["longitude"].str.replace(',', '.').astype(float)
    stations["latitude"] = stations["latitude"].str.replace(',', '.').astype(float)
    stations["velo_disponibles"] = stations["VM disponibles"] + stations["VAE disponibles"]
    # keep only basic info and velo_disponibles
    to_keep = ["Code station", "Nom station", "longitude", "latitude", "velo_disponibles"]

    stations = stations[to_keep]
    to_group = to_keep[0:4]
    stations_time_full = stations.groupby(to_group, as_index=False).apply(lambda x: (x <= 1).sum())
    stations_time_full = stations_time_full.rename(columns = {"velo_disponibles" : "count_minutes_full"})


    # stations_time_full.columns


    geometry_stations_full = gpd.points_from_xy(stations_time_full["longitude"], stations_time_full["latitude"])

    geo_stations_full = gpd.GeoDataFrame(stations_time_full, crs=4326, geometry=geometry_stations_full)
    geo_stations_full = geo_stations_full.to_crs(epsg = 3857)

    districts = gpd.read_file("../data/raw/quartier_paris.geojson").to_crs(epsg=3857)

    # all_districts = pd.concat([districts, departements_petite_couronne_no_paris])

    # geo_stations_full["log_count_minutes_full"] = np.sqrt(geo_stations_full["count_minutes_full"] + 1)
    geo_stations_full["count_minutes_divided"] = geo_stations_full["count_minutes_full"] / 10

    fig, ax = plt.subplots()
    districts.plot(ax=ax, alpha=0.5, edgecolor="white")
    geo_stations_full.plot(
            ax=ax,
            column = "count_minutes_full",
            cmap = "OrRd", legend = True,
            legend_kwds={"label": "Number of minutes full in " + month_name, "orientation": "horizontal"}
    )
    ax.set_axis_off()
    ctx.add_basemap(ax)
    figure = plt.gcf()
    figure.set_size_inches(6, 6)
    plt.savefig('../img/map_station_full_' + month_name + '.png', bbox_inches = "tight")
    # plt.show()
