# -*- coding: utf-8 -*-
import os
import math
import json
import pylake
import warnings
from pyrsktools import RSK
import numpy as np
import pandas as pd
from scipy.interpolate import griddata
from datetime import datetime, timedelta, timezone
from general.functions import GenericInstrument, json_converter
from functions import get_bathymetry, temperature_gradient_check, nan_helper


class TemperatureChainGeneral(GenericInstrument):
    def __init__(self, *args, **kwargs):
        super(TemperatureChainGeneral, self).__init__(*args, **kwargs)

        self.dimensions = {
            'depth': {'dim_name': 'depth', 'dim_size': None},
            'time': {'dim_name': 'time', 'dim_size': None}
        }
        self.variables = {
            'time': {'var_name': 'time', 'dim': ('time',), 'unit': 'seconds since 1970-01-01 00:00:00',
                     'long_name': 'time'},
            'depth': {'var_name': 'depth', 'dim': ('depth',), 'unit': 'm', 'long_name': 'depth'},
            'temp': {'var_name': 'temp', 'dim': ('depth', 'time',), 'unit': 'degC', 'long_name': 'temperature'},
        }

    def gradient_check(self, gradients):
        self.log.info("Performing additional gradient check on temperature data.", indent=2)
        self.data["temp_qual"] = temperature_gradient_check(self.data["depth"], self.data["temp"],
                                                            self.data["temp_qual"],
                                                            time_epilimnion_grad_threshold=gradients["time_epilimnion_grad_threshold"],
                                                            time_hypolimnion_grad_threshold=gradients["time_hypolimnion_grad_threshold"],
                                                            depth_grad_threshold=gradients["depth_grad_threshold"],
                                                            perc_good=gradients["perc_good"])

    def decimate_data(self, mins):
        self.log.info("Decimating data to {}min periods.".format(mins), indent=2)
        time_min = np.amin(self.data["time"])
        time_max = math.ceil(np.amax(self.data["time"]) / (mins * 60)) * mins * 60
        num_steps = math.floor((time_max - time_min) / (mins * 60)) + 1
        decimated_time = np.zeros(num_steps)
        decimated_temp = np.zeros([len(self.data["temp"]), num_steps])

        for x in range(num_steps):
            dt1 = time_max - (x * mins * 60)
            dt2 = time_max - ((x + 1) * mins * 60)
            decimated_time_index = np.where(np.logical_and(self.data["time"] >= dt2, self.data["time"] <= dt1))[0]
            decimated_time[num_steps - 1 - x] = dt1
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=RuntimeWarning)
                decimated_temp[:, num_steps - 1 - x] = np.nanmean(self.data["temp"][:, decimated_time_index], axis=1)

        self.data["time"] = decimated_time
        self.data["temp"] = decimated_temp

        variables = list(self.variables.keys())
        for variable in variables:
            if "_qual" in variable:
                del self.variables[variable]

    def interpolate_data(self, param, method="cubic"):
        self.log.info("Interpolating data", indent=2)
        self.data["interp_" + param] = np.copy(self.data[param])
        mask = np.isnan(self.data["interp_" + param])
        self.data["interp_" + param][mask] = 1
        self.data["interp_" + param][~mask] = 0
        self.variables["interp_" + param] = {'var_name': "interp_" + param, 'dim': self.variables[param]["dim"],
                                             'unit': '0 = real data, 1 = interpolated data',
                                             'long_name': "Interpolate " + self.variables[param]["long_name"], }

        if np.all(np.isnan(self.data[param])):
            self.log.warning("Data is all NAN", indent=3)
            return

        if np.array(self.data[param]).shape[1] == 1:
            self.log.info("Interpolating gaps in 1D array for {}".format(param), indent=3)
            y = np.array(self.data[param])[:, 0]
            nans, x = nan_helper(y)
            y[nans] = np.interp(x(nans), x(~nans), y[~nans])
            y = np.array([y]).T
            self.data[param] = y
        else:
            self.log.info("Interpolating gaps in 2D array for {}".format(param), indent=3)
            xx, yy = np.meshgrid(np.arange(0, len(self.data["time"]), 1), self.data["depth"])
            array = np.ma.masked_invalid(self.data["temp"])
            x1 = xx[~array.mask]
            y1 = yy[~array.mask]
            self.data[param] = griddata((x1, y1), array[~array.mask], (xx, yy), method=method)

    def compute_physical_quantities(self, bathymetry_file="notes/bathymetry.csv"):
        self.log.info("Computing physical quantities for dataset", indent=2)
        new_variables = ['mixed_layer_depth', 'thermocline_depth', 'schmidt_stability', 'heat_content']
        new_units = ['m', 'm', 'kg m-2', 'J']

        for variable, unit in zip(new_variables, new_units):
            self.variables[variable] = {'var_name': variable, 'dim': ('time',), 'unit': unit, 'long_name': variable}

        bathymetry_depth, bathymetry_area = get_bathymetry(bathymetry_file, self.data['depth'])

        #hTH, _ = pylake.thermocline(self.data['temp'], self.data['depth'])
        hML = pylake.mixed_layer(self.data['temp'], self.data['depth'], threshold=1)
        schmidt_stability = pylake.schmidt_stability(self.data['temp'], self.data['depth'], bthA=bathymetry_area,
                                                     bthD=bathymetry_depth, sal=0.2, g=9.81)
        heat_content = pylake.heat_content(self.data['temp'], bthA=bathymetry_area, bthD=bathymetry_depth,
                                           depth=self.data['depth'], s=0.2)

        epi_depth,hypo_depth = pylake.metalimnion(self.data['temp'], self.data['depth'], slope=0.5, slope_calc='relative', seasonal=True, mixed_cutoff=1, smooth=True, s=0.2)
        result = np.empty(len(epi_depth))

        # Compute thermocline depth from epilimnion and hypolimnion depths
        for i in range(len(epi_depth)):
            epi_temp = np.interp(epi_depth[i],self.data['depth'],self.data['temp'][:,i])
            hypo_temp = np.interp(hypo_depth[i],self.data['depth'],self.data['temp'][:,i])
            meta_temp = (epi_temp + hypo_temp)/2
            meta_depth = np.interp(-meta_temp,-self.data['temp'][:,i],self.data['depth'])
            result[i] = meta_depth

        self.data['thermocline_depth'] = result
        self.data["mixed_layer_depth"] = hML
        self.data["schmidt_stability"] = schmidt_stability
        self.data["heat_content"] = heat_content

    def surface_and_bottom_values(self):
        self.variables['surfacetemp'] = {'var_name': 'surfacetemp', 'dim': ('time',), 'unit': 'degC',
                                         'long_name': 'surface temperature'}
        self.variables['bottomtemp'] = {'var_name': 'bottomtemp', 'dim': ('time',), 'unit': 'degC',
                                        'long_name': 'bottom temperature'}
        self.data["surfacetemp"] = self.data['temp'][0, :]
        self.data['bottomtemp'] = self.data['temp'][-2, :]


class TemperatureChainV0(TemperatureChainGeneral):
    def __init__(self, *args, **kwargs):
        super(TemperatureChainV0, self).__init__(*args, **kwargs)
        self.general_attributes = {
            "institution": "EPFL",
            "source": "LéXPLORE Thermistor Chain v0",
            "references": "LéXPLORE commun instruments sebastien.lavanchy@epfl.ch",
            "history": "See history on Renku",
            "conventions": "CF 1.7",
            "comment": "Data from the Thermistor Chain on LéXPLORE Platform in Lake Geneva",
            "title": "LéXPLORE Thermistor Chain v0"
        }

    def read_data(self, file):
        self.log.info("Reading data from {}".format(file), 1)
        try:
            depths = [18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2.5, 2, 1.5, 1.25, 1, 0.75, 0.5,
                      0.25, 90, 87, 84, 81, 78, 75, 72, 69, 66, 63, 60, 57, 54, 51, 48, 45, 42, 39, 36, 33, 30, 27, 24,
                      21]

            self.log.info("Locating partner file", 2)

            folder = os.path.join(os.path.dirname(file), "..", "21-90m_depth")
            for f in os.listdir(folder):
                if file.split("_")[-2] in f:
                    deep_file = os.path.join(folder, f)

            shallow_chain = RSK(file)
            shallow_chain.open()
            shallow_chain.readdata()
            s_data = shallow_chain.data
            shallow_chain.close()

            dfs = pd.DataFrame(s_data)
            dfs = dfs.resample('60s', on='timestamp').median()

            deep_chain = RSK(deep_file)
            deep_chain.open()
            deep_chain.readdata()
            d_data = deep_chain.data
            deep_chain.close()

            dfd = pd.DataFrame(d_data)
            dfd = dfd.resample('60s', on='timestamp').median()

            df = dfs.join(dfd, how="outer", lsuffix="_s", rsuffix="_d")

            df.columns = depths
            df = df.reindex(sorted(df.columns), axis=1)

            self.data["time"] = df.index.to_numpy(dtype='datetime64[ns]').astype('float64') // 10**9
            self.data["depth"] = np.array(df.columns)
            self.data["temp"] = np.array(df.T.to_numpy())
        except Exception as e:
            self.log.info("Failed to read data from {}".format(file), indent=1)
            raise e
        return True


class TemperatureChainV1(TemperatureChainGeneral):
    def __init__(self, *args, **kwargs):
        super(TemperatureChainV1, self).__init__(*args, **kwargs)
        self.general_attributes = {
            "institution": "EPFL",
            "source": "LéXPLORE Thermistor Chain v1",
            "references": "LéXPLORE commun instruments sebastien.lavanchy@epfl.ch",
            "history": "See history on Renku",
            "conventions": "CF 1.7",
            "comment": "Data from the Thermistor Chain on LéXPLORE Platform in Lake Geneva",
            "title": "LéXPLORE Thermistor Chain v1"
        }

    def read_data(self, file):
        self.log.info("Reading data from {}".format(file), 1)
        try:
            df = pd.read_csv(file, header=None)

            df.columns = ["Timestamp", "sample number", "battery", "PTU3", 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7,
                          6, 5, 4, 3, 2.5, 2, 1.5, 1.25, 1, 0.75, 0.5, 0.25, 90, 87, 84, 81, 78, 75, 72, 69, 66, 63, 60,
                          57, 54, 51, 48, 45, 42, 39, 36, 33, 30, 27, 24, 21]

            df["Timestamp"] = df["Timestamp"].apply(
                lambda x: datetime.timestamp(datetime.strptime(x, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)))
            df.sort_values(by=['Timestamp'], inplace=True)
            df = df.apply(pd.to_numeric, errors='coerce')

            for column in ["sample number", "battery", "PTU3"]:
                if column in df.columns:
                    df = df.drop([column], axis=1)

            foo = df.isnull().sum(axis=1)
            ind = np.where(foo == (len(df.columns) - 1))[0]
            if len(ind) > 0:
                df = df.drop(df.index[ind])

            self.data["time"] = df["Timestamp"]
            df = df.drop(["Timestamp"], axis=1)
            df = df.reindex(sorted(df.columns), axis=1)
            df = df.reset_index(drop=True)
            self.data["depth"] = df.columns
            self.data["temp"] = df.T.to_numpy()
        except Exception as e:
            self.log.info("Failed to read data from {}".format(file), indent=1)
            raise e
        return True


class TemperatureChainV2(TemperatureChainGeneral):
    def __init__(self, *args, **kwargs):
        super(TemperatureChainV2, self).__init__(*args, **kwargs)
        self.general_attributes = {
            "institution": "EPFL",
            "source": "LéXPLORE Thermistor Chain v2",
            "references": "LéXPLORE commun instruments sebastien.lavanchy@epfl.ch",
            "history": "See history on Renku",
            "conventions": "CF 1.7",
            "comment": "Data from the Thermistor Chain on LéXPLORE Platform in Lake Geneva",
            "title": "LéXPLORE Thermistor Chain v2"
        }

    def read_data(self, file):
        self.log.info("Reading data from {}".format(file), 1)
        try:
            df = pd.read_csv(file, header=None)

            df.columns = ["Timestamp", "sample number", "battery", "PTU3", 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13,
                          12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0.25, 93, 90, 87, 84, 81, 78, 75, 72, 69, 66, 63, 60,
                          57, 54, 51, 48, 45, 42, 39, 36, 33, 30, 27, 24]
            df["Timestamp"] = df["Timestamp"].apply(
                lambda x: datetime.timestamp(datetime.strptime(x, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)))
            df.sort_values(by=['Timestamp'], inplace=True)
            df = df.apply(pd.to_numeric, errors='coerce')

            for column in ["sample number", "battery", "PTU3"]:
                if column in df.columns:
                    df = df.drop([column], axis=1)

            foo = df.isnull().sum(axis=1)
            ind = np.where(foo == (len(df.columns) - 1))[0]
            if len(ind) > 0:
                df = df.drop(df.index[ind])

            if len(df["Timestamp"]) == 0:
                self.log.info("No valid data found in {}".format(file), indent=1)
                return False

            self.data["time"] = df["Timestamp"]
            df = df.drop(["Timestamp"], axis=1)
            df = df.reindex(sorted(df.columns), axis=1)
            df = df.reset_index(drop=True)
            self.data["depth"] = df.columns
            self.data["temp"] = df.T.to_numpy()
        except Exception as e:
            self.log.info("Failed to read data from {}".format(file), indent=1)
            raise e
        return True


class TemperatureChainV3(TemperatureChainGeneral):
    def __init__(self, *args, **kwargs):
        super(TemperatureChainV3, self).__init__(*args, **kwargs)
        self.general_attributes = {
            "institution": "EPFL",
            "source": "LéXPLORE Thermistor Chain v3",
            "references": "LéXPLORE commun instruments guillaume.cunillera@epfl.ch",
            "history": "See history on Renku",
            "conventions": "CF 1.7",
            "comment": "Data from the Thermistor Chain on LéXPLORE Platform in Lake Geneva",
            "title": "LéXPLORE Thermistor Chain v3"
        }

    def read_data(self, file):
        self.log.info("Reading data from {}".format(file), 1)
        try:
            df = pd.read_csv(file, header=None)

            df.columns = ["Timestamp", "sample number", 0.25, 1, 2, 4, 6, 8, 10, 12, 14, 16, 18, 21, 24, 27, 30, 35, 40,
                          45, 50, 55, 60, 65, 70, 75, 80, 85, 90]
            df["Timestamp"] = df["Timestamp"].apply(
                lambda x: datetime.timestamp(datetime.strptime(x, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)))
            df.sort_values(by=['Timestamp'], inplace=True)
            df = df.apply(pd.to_numeric, errors='coerce')

            for column in ["sample number", "battery", "PTU3"]:
                if column in df.columns:
                    df = df.drop([column], axis=1)

            foo = df.isnull().sum(axis=1)
            ind = np.where(foo == (len(df.columns) - 1))[0]
            if len(ind) > 0:
                df = df.drop(df.index[ind])

            if len(df["Timestamp"]) == 0:
                self.log.info("No valid data found in {}".format(file), indent=1)
                return False

            if len(df["Timestamp"]) == 1:
                self.log.info("Only one timestep, skipping until more data available", indent=1)
                return False

            self.data["time"] = df["Timestamp"]
            df = df.drop(["Timestamp"], axis=1)
            df = df.reindex(sorted(df.columns), axis=1)
            df = df.reset_index(drop=True)
            self.data["depth"] = df.columns
            self.data["temp"] = df.T.to_numpy()
        except Exception as e:
            self.log.info("Failed to read data from {}".format(file), indent=1)
            raise e
        return True
