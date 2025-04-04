# -*- coding: utf-8 -*-
import os
import sys
import yaml
import json
import time
import argparse
import requests
from instruments import TemperatureChainV0, TemperatureChainV1, TemperatureChainV2, TemperatureChainV3
from general.functions import logger, files_in_directory
from functions import retrieve_new_files, merge_files

def main(server=False, logs=False, remove_api_data=False):
    repo = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if logs:
        log = logger(os.path.join(repo, "logs/thermisterchain"))
    else:
        log = logger()
    log.initialise("Processing LéXPLORE thermister chain data")
    directories = {f: os.path.join(repo, "data", f) for f in ["Level0", "Level1", "Level2", "failed"]}
    for directory in directories:
        os.makedirs(directories[directory], exist_ok=True)
    edited_files = []

    log.begin_stage("Collecting inputs")
    if server:
        log.info("Processing files from sftp server")
        directories["Level0"] = os.path.join(directories["Level0"], "v3")
        if not os.path.exists(os.path.join(repo, "creds.json")):
            raise ValueError("Credential file required to retrieve live data from the fstp server.")
        with open(os.path.join(repo, "creds.json"), 'r') as f:
            creds = json.load(f)
        new_files = retrieve_new_files(directories["failed"],
                                       creds, server_location="data/Temperature_chain",
                                       filetype=".dat", remove=remove_api_data, overwrite=True)
        files = merge_files(directories["Level0"], new_files)
        edited_files = edited_files + files
    else:
        files = files_in_directory(directories["Level0"])
        files.sort()
        log.info("Reprocessing complete dataset from {}".format(directories["Level0"]))
    log.end_stage()

    log.begin_stage("Processing data...")
    gradients = False
    interpolate = False
    for file in files:
        if "/v0/0-18m_depth" in file:
            version = "v0"
            sensor = TemperatureChainV0(log=log)
        elif "v1" in file:
            version = "v1"
            sensor = TemperatureChainV1(log=log)
        elif "v2" in file or "Temperature_chain_V2.0" in file:
            version = "v2"
            sensor = TemperatureChainV2(log=log)
        elif "v3" in file or "Temperature_chain_V3.0" in file:
            version = "v3"
            sensor = TemperatureChainV3(log=log)
        else:
            continue

        if sensor.read_data(file):
            sensor.quality_assurance(file_path=os.path.join(repo, "notes/quality_assurance.json"),
                                     maintenance_file=os.path.join(repo, "notes/events.csv"))
            if gradients:
                sensor.gradient_check(gradients)
            edited_files.extend(sensor.export(directories["Level1"], "L1_LexploreTemperatureChain_" + version, output_period="weekly"))
            sensor.mask_data()
            sensor.decimate_data(10)
            if interpolate:
                sensor.interpolate_data("temp")
            sensor.surface_and_bottom_values()
            sensor.compute_physical_quantities(bathymetry_file=os.path.join(repo, "notes/bathymetry.csv"))
            edited_files.extend(sensor.export(directories["Level2"], "L2_LexploreTemperatureChain_" + version, output_period="monthly"))
    log.end_stage()

    return edited_files

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--server', '-s', help="Collect and process new files from FTP server", action='store_true')
    parser.add_argument('--logs', '-l', help="Write logs to file", action='store_true')
    args = vars(parser.parse_args())
    main(server=args["server"], logs=args["logs"])