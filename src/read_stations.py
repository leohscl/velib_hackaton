import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
import contextily as ctx
from shapely.geometry import Point, LineString
import glob

month_codes = ["02", "06"]
month_names = ["February", "June"]
# doc: ../data/raw/14-Hackathon/02_Historique_remplissage_stations/Descriptif_historique_remplissage_stations.txt
for i_month in range(len(month_names)):
    month_name = month_names[i_month]
    month_code = month_codes[i_month]
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

    def create_geopandas(stations):
        # keep only basic info and velo_disponibles
        to_keep = ["Code station", "Nom station", "longitude", "latitude", "velo_disponibles"]
        stations_minimal = stations[to_keep]
        to_group = to_keep[0:4]
        stations_time_full = stations_minimal.groupby(to_group, as_index=False).apply(lambda x: (x <= 1).sum())
        stations_time_full = stations_time_full.rename(columns = {"velo_disponibles" : "count_minutes_full"})
        geometry_stations_full = gpd.points_from_xy(stations_time_full["longitude"], stations_time_full["latitude"])
        geo_stations_full = gpd.GeoDataFrame(stations_time_full, crs=4326, geometry=geometry_stations_full)
        geo_stations_full = geo_stations_full.to_crs(epsg = 3857)
        return geo_stations_full

    geo_stations_full = create_geopandas(stations)
    districts = gpd.read_file("../data/raw/quartier_paris.geojson").to_crs(epsg=3857)
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
    plt.savefig('../img/stations_full/map_station_full_' + month_name + '.png', bbox_inches = "tight")

    ## filtering on weekdays morning

    # Some stations not have minutes in timestamp
    # eg: stations.iloc[3625]
    stations_correct_timestamp = stations[stations['Date mise à jour'].apply(lambda x: x.count(':') == 2)]
    stations_correct_timestamp['date_formatted'] = pd.to_datetime(stations_correct_timestamp['Date mise à jour'])
    stations_correct_timestamp['dayofweek'] = stations_correct_timestamp.date_formatted.dt.dayofweek
    # restrict to weekdays morning
    stations_weekdays = stations_correct_timestamp[stations_correct_timestamp['dayofweek'].isin(range(5))]

    times_start = ["00", "07", "11", "14", "17", "20"]
    times_end = ["07", "11", "14", "17", "20", "24"]
    for index_time in range(len(times_start)):
        time_start = times_start[index_time]
        time_end = times_end[index_time]
        start_int = int(time_start)
        end_int = int(time_end)
        if start_int < end_int:
            stations_weekday_time_slot = stations_weekdays[stations_weekdays.date_formatted.dt.strftime('%H:%M:%S').between(time_start + ':00:00',time_end + ':00:00')]
        else:
            stations_weekday_time_slot_end_night = stations_weekdays[stations_weekdays.date_formatted.dt.strftime('%H:%M:%S').between(time_start + ':00:00','24' + ':00:00')]
            stations_weekday_time_slot_early_morning = stations_weekdays[stations_weekdays.date_formatted.dt.strftime('%H:%M:%S').between('00' + ':00:00', time_end + ':00:00')]
            stations_weekday_time_slot = pd.concat([stations_weekday_time_slot_end_night])
        geo_time_slot_full = create_geopandas(stations_weekday_time_slot)
        districts = gpd.read_file("../data/raw/quartier_paris.geojson").to_crs(epsg=3857)
        fig, ax = plt.subplots()
        districts.plot(ax=ax, alpha=0.5, edgecolor="white")
        label_legend = "Number of minutes full in " + month_name + "\n between " + time_start + "h and " + time_end + "h"
        geo_time_slot_full.plot(
                ax=ax,
                column = "count_minutes_full",
                cmap = "OrRd", legend = True,
                legend_kwds={"label": label_legend, "orientation": "horizontal"}
        )
        ax.set_axis_off()
        ctx.add_basemap(ax)
        figure = plt.gcf()
        figure.set_size_inches(6, 6)
        file_out = '../img/stations_full/map_station_full_' + month_name + '_between' + time_start + '_and_' + time_end + '.png'
        plt.savefig(file_out, bbox_inches = "tight")
        # plt.show()

