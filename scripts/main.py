# -*- coding: utf-8 -*-
import os
import sys
import yaml
from instruments import TemperatureChainV0, TemperatureChainV1, TemperatureChainV2, TemperatureChainGeneral
from general.functions import logger, maintenance, files_in_directory
from functions import pre_process

log = logger("scripts/logs/temperature")
log.initialise("Processing LéXPLORE thermistor chain data")

log.begin_stage("Collecting inputs")
with open("scripts/input_python.yaml", "r") as f:
    directories = yaml.load(f, Loader=yaml.FullLoader)

for directory in directories.values():
    if not os.path.exists(directory):
        os.makedirs(directory)

if len(sys.argv) == 1:
    live = False
    files = files_in_directory(directories["Level0"])
    files.sort()
    log.info("Reprocessing complete dataset from {}".format(directories["Level0"]))
elif len(sys.argv) == 2:
    live = True
    files = [str(sys.argv[1]).replace('\\', '/')]
    log.info("Live processing file {}".format(files[0]))

log.end_stage()

log.begin_stage("Processing data to L1")
for file in files:
    if "/v0/0-18m_depth" in file:
        continue
        version = "v0"
        gradients = False
        interpolate = False
        sensor = TemperatureChainV0(log=log)
    elif "/v1/" in file:
        continue
        version = "v1"
        gradients = {
            "time_epilimnion_grad_threshold": 1.5,
            "time_hypolimnion_grad_threshold": 0.4,
            "depth_grad_threshold": 1,
            "perc_good": 0.5
        }
        interpolate = True
        sensor = TemperatureChainV1(log=log)
    elif "/v2/" in file:
        continue
        version = "v2"
        gradients = {
            "time_epilimnion_grad_threshold": 1.5,
            "time_hypolimnion_grad_threshold": 0.4,
            "depth_grad_threshold": 1,
            "perc_good": 0.5
        }
        interpolate = False
        sensor = TemperatureChainV2(log=log)
    else:
        continue

    if live:
        file = pre_process(file, directories["Level0"], directories["Process"])

    if sensor.read_data(file):
        sensor.quality_assurance(file_path="notes/quality_assurance.json")
        if gradients:
            sensor.gradient_check(gradients)
        sensor.export(directories["Level1"], "L1_LexploreTemperatureChain_" + version, output_period="weekly")
        sensor.mask_data()
        sensor.decimate_data(10)
        if interpolate:
            sensor.interpolate_data("temp")
        sensor.surface_and_bottom_values()
        sensor.compute_physical_quantities(bathymetry_file="notes/bathymetry.csv")
        sensor.export(directories["Level2"], "L2_LexploreTemperatureChain_" + version, output_period="monthly")
log.end_stage()


log.begin_stage("Applying Temperature chain Maintenance Periods")
effected_files = maintenance(directories["Level1"], file="notes/events.csv", datalakes=[])
for file in effected_files:
    version = file.split("_")[-3]
    sensor = TemperatureChainGeneral(log=log)
    sensor.read_netcdf_data(file)
    sensor.mask_data()
    sensor.decimate_data(10)
    if version == "v1":
        sensor.interpolate_data("temp")
    sensor.surface_and_bottom_values()
    sensor.compute_physical_quantities(bathymetry_file="notes/bathymetry.csv")
    sensor.export(directories["Level2"], "L2_LexploreTemperatureChain_" + version, output_period="monthly", overwrite=True)
log.end_stage()

