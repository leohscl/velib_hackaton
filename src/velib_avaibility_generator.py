"""
Script to generate images showing all station capacities at given time
"""
import glob
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import geopandas as gpd
import contextily
from datetime import datetime
from pathlib import Path
from typing import Tuple


HACKATHON_DATA_FOLDER = r"C:\Users\icogr\Desktop\Code\HackathonVelib\velib_hackaton\data\raw"
OUTPUT_FOLDER = r"C:\Users\icogr\Desktop\Code\HackathonVelib\velib_hackaton\myown\output"
EPSG_REFERENCE = 3857


def blerp(ymin: float, ymax: float, tmin: float, tmax: float, t: float) -> float:
    """ Bounded linear interpolation """
    if t <= tmin: return ymin
    if t >= tmax: return ymax
    return ymin + t*(ymax-ymin)

def get_rgb_color_from_avaibility(avaibility: float) -> Tuple:
    """ Turn velib avaibility into RGB color """
    # return 4*(avaibility-0.5)**2, 4*avaibility*(1-avaibility), 0  # red if empty/full, green if 50% capacity
    # return 4*(avaibility-0.5)**2, 4*avaibility*(1-avaibility), 0  # black if empty/full, white if 50% capacity
    # return avaibility, avaibility, avaibility  # black and white
    return blerp(0.1, 1, 0.5, 1, avaibility), blerp(0.1, 1, 0, 0.5, avaibility), blerp(0.1, 1, 0.5, 1, avaibility)  # white if empty, black if full, green if 50% capacity

### Get velib and Paris data
files = glob.glob(HACKATHON_DATA_FOLDER + r"\14-Hackathon\02_Historique_remplissage_stations\2023_06\*.csv", recursive=True)
# list_df = [pd.read_csv(files[-1])]
list_df = [pd.read_csv(files[-2])]
# list_df = [pd.read_csv(_file) for _file in files]
stations_history = pd.concat(list_df)
districts = gpd.read_file(HACKATHON_DATA_FOLDER + "\quartier_paris.geojson").to_crs(epsg=EPSG_REFERENCE)

### Format station data
stations_history["latitude"] = stations_history["latitude"].str.replace(',', '.').astype(float)
stations_history["longitude"] = stations_history["longitude"].str.replace(',', '.').astype(float)
stations_history = stations_history.sort_values(by="Date mise à jour", ascending=True).reset_index(drop=True)
stations_geometry = gpd.points_from_xy(stations_history["longitude"], stations_history["latitude"])
geo_stations_history = gpd.GeoDataFrame(
    stations_history, crs=4326, geometry=stations_geometry
)
geo_stations_history = geo_stations_history.to_crs(epsg=EPSG_REFERENCE)


### Get all dates available from station data
reference_dates = geo_stations_history["Date mise à jour"].unique()
# Tweak these to iterate over range of dates
index_start = 0
index_end = len(reference_dates)
step = 1
reference_dates = reference_dates[index_start:index_end:step]



first_geo_stations = geo_stations_history[geo_stations_history["Date mise à jour"] == reference_dates[0]]
previous_geo_stations = first_geo_stations
image_number = index_start
for reference_date in reference_dates:
    # Merge data at current reference date t into previous data at t-1min 
    updated_geo_stations = geo_stations_history[geo_stations_history["Date mise à jour"] == reference_date]
    current_geo_stations = pd.concat([previous_geo_stations, updated_geo_stations]).drop_duplicates()
    
    # Calculate proportion of velib in a station (velib availability)
    mech_velib_nb = current_geo_stations["VM disponibles"]
    elec_velib_nb = current_geo_stations["VAE disponibles"]
    off_mech_velib_nb = current_geo_stations["VM indisponibles"]
    off_elec_velib_nb = current_geo_stations["VAE indisponibles"]
    empty_slots = current_geo_stations["Nombre de diapasons disponibles"]
    sp_mech_velib_nb = current_geo_stations["VM disponibles (Station +)"]
    sp_elec_velib_nb = current_geo_stations["VAE disponibles (Station +)"]
    sp_off_mech_velib_nb = current_geo_stations["VM indisponibles (Station +)"]
    sp_off_elec_velib_nb = current_geo_stations["VAE indisponibles (Station +)"]
    sp_empty_cables = current_geo_stations["Nombre de cables disponibles (Station +)"].fillna(0)
    current_geo_stations["Velib availability"] = (mech_velib_nb + elec_velib_nb + sp_mech_velib_nb + sp_elec_velib_nb)/(mech_velib_nb + elec_velib_nb + off_mech_velib_nb + off_elec_velib_nb + empty_slots + sp_mech_velib_nb + sp_elec_velib_nb + sp_off_mech_velib_nb + sp_off_elec_velib_nb + sp_empty_cables)

    # Draw
    _, ax = plt.subplots()
    ax.set_axis_off()
    districts.plot(ax=ax, alpha=0.5, edgecolor="white")
    try:
        hour = datetime.strptime(reference_date, '%Y/%m/%d %H:%M:%S').strftime("%Hh%M")
    except ValueError:
        hour = "00h00"
    colors = current_geo_stations["Velib availability"].apply(get_rgb_color_from_avaibility)
    # contextily.add_basemap(ax, zoom=2)  # TODO: Doesn't work ?
    current_geo_stations.plot(ax=ax, markersize=2, color=colors, label=f'{hour}')
    ax.set_facecolor("g")
    plt.legend(loc='upper right', markerscale=0, handlelength=0, handletextpad=0, fancybox=True)

    # Generate output
    output_path = Path(OUTPUT_FOLDER, f"image{str(image_number).rjust(4, '0')}.png")
    plt.show()
    # plt.savefig(output_path, dpi=400)
    # plt.close()
    image_number += 1

    # Iterate
    previous_geo_stations = current_geo_stations
    print(hour)

### Ffmpeg command to generate video from all image frames
# ffmpeg -framerate 25 -i "image%04d.png" -c:v libx264 -pix_fmt yuv420p out.mp4
