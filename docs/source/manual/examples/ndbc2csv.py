"""Convert NDBC standard meteorological text files to the observation
format used by the CoSMoS web viewer.

Download the historical data files for your buoys from
https://www.ndbc.noaa.gov/ (e.g. 42060h2022.txt) and put them in ``raw_path``.
For each buoy, all files starting with the buoy id are combined into
``waves.<id>.observed.csv.js`` in ``obs_path``.
"""

import glob
import os

import pandas as pd

stations = ["41043", "41044", "42059", "42060"]

# Folder with the downloaded NDBC text files
raw_path = r"c:\work\cosmos\ndbc_downloads"
# <run_folder>\observations\<observations_path>\waves
obs_path = r"c:\work\cosmos\run_folder\observations\hurricane_fiona\waves"

os.makedirs(obs_path, exist_ok=True)

for station in stations:
    frames = []
    for file_name in sorted(glob.glob(os.path.join(raw_path, station + "*.txt"))):
        # First line holds the column names, second line the units
        df = pd.read_csv(file_name, sep=r"\s+", header=0, skiprows=[1])
        date = pd.to_datetime(
            {
                "year": df["#YY"],
                "month": df["MM"],
                "day": df["DD"],
                "hour": df["hh"],
                "minute": df["mm"],
            }
        )
        out = pd.DataFrame({"date": date, "hs": df["WVHT"], "tp": df["DPD"]})
        # 99 means missing wave height
        frames.append(out[out["hs"] < 99.0])

    if not frames:
        print(f"No files found for station {station}")
        continue

    data = pd.concat(frames).sort_values("date")
    csv = data.to_csv(
        date_format="%Y-%m-%dT%H:%M:%S",
        float_format="%.3f",
        header=False,
        index=False,
        lineterminator="\n",
    )

    file_name = os.path.join(obs_path, f"waves.{station}.observed.csv.js")
    with open(file_name, "w") as f:
        f.write("var csv_obs = `date_time,hm0,tp\n")
        f.write(csv)
        f.write("`;")
    print(f"Written {file_name}")