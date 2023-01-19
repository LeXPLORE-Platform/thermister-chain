# -*- coding: utf-8 -*-
import os
import ftplib
import numpy as np
import pandas as pd
from shutil import move
from datetime import datetime
from general.functions import logger


def nan_helper(y):
    return np.isnan(y), lambda z: z.nonzero()[0]


def get_bathymetry(file, depth):
    df_bath = pd.read_csv(file, header=0)
    df_bath["Isobath Area"] = df_bath["Isobath Area (m2)"].astype("float")
    df_bath["Depth"] = df_bath["Depth (m)"].astype("float")
    area = np.interp(depth, df_bath["Depth"], df_bath["Isobath Area"])
    return depth, area


def pre_process(infile, version, level0, process):
    for row in open(infile, "r"):
        local = os.path.join(level0, version, "LeXPLORE_EAST_TempChain_" + row[1:11] + ".dat")
        temp = process + "LeXPLORE_EAST_TempChain_" + row[1:11] + ".dat"
        if os.path.isfile(local):
            os.rename(local, temp)
        if os.path.isfile(temp):
            read = open(temp, "r")
            if row in read.readlines():
                read.close()
            else:
                read.close()
                append = open(temp, "a")
                append.write(row)
                append.close()
        else:
            new = open(temp, "w")
            new.write(row)
            new.close()
    os.remove(infile)
    os.rename(temp, local)

    return local


def temperature_gradient_check(depth_vec, df, df_qual, time_epilimnion_grad_threshold=1.5,
                               time_hypolimnion_grad_threshold=0.4, depth_grad_threshold=1, perc_good=0.2):
    dfplot = df.copy()
    dfqual = df_qual.copy()
    ndepth = dfplot.shape[0]

    for depth in range(0, 30):
        vec = np.copy(dfplot[depth, :])
        vec_qual = np.copy(dfqual[depth, :])
        vec_index = np.array(range(0, len(vec)))

        ind = np.where(vec_qual == 1)[0]
        vec_index = np.delete(vec_index, ind)
        vec = np.copy(dfplot[depth, :])[vec_index]
        vec_qual = np.zeros(len(vec))

        if len(vec) > 0:
            qthreshold_inf = np.quantile(vec, 0.50) - np.quantile(vec, 0.01)
            qthreshold_sup = np.quantile(vec, 0.99) - np.quantile(vec, 0.50)

            if qthreshold_sup > 0.5 or qthreshold_inf > 0.5:
                quant_mat = []
                for q in range(100):
                    quant_mat.append(np.quantile(vec, q / 100))

                vecdiff = np.diff(quant_mat)
                val = np.where(vecdiff >= time_epilimnion_grad_threshold)[0] + 1

                if len(val) > 0:
                    quant_remove = max(val)
                    indremove = np.where(vec <= np.quantile(vec, quant_remove / 100))
                else:
                    indremove = []

                if len(indremove) > 0:
                    indremove = np.unique(indremove)
                    vec_index = np.delete(vec_index, indremove)

                    dfqual[depth, :] = 1
                    dfqual[depth, vec_index] = 0

    for depth in range(31, ndepth):
        vec = np.copy(dfplot[depth, :])
        vec_qual = np.copy(dfqual[depth, :])
        vec_index = np.array(range(0, len(vec)))

        ind = np.where(vec_qual == 1)[0]
        vec_index = np.delete(vec_index, ind)
        vec = np.copy(dfplot[depth, :])[vec_index]
        vec_qual = np.zeros(len(vec))

        if len(vec) > 0:
            qthreshold_inf = np.quantile(vec, 0.50) - np.quantile(vec, 0.01)
            qthreshold_sup = np.quantile(vec, 0.99) - np.quantile(vec, 0.50)

            if qthreshold_sup > 0.5 or qthreshold_inf > 0.5:
                quant_mat = []
                for q in range(100):
                    quant_mat.append(np.quantile(vec, q / 100))

                vecdiff = np.diff(quant_mat)
                val = np.where(vecdiff >= time_hypolimnion_grad_threshold)[0] + 1

                if len(val) > 0:
                    quant_remove = max(val)
                    indremove = np.where(vec <= np.quantile(vec, quant_remove / 100))
                else:
                    indremove = []

                if len(indremove) > 0:
                    indremove = np.unique(indremove)
                    vec_index = np.delete(vec_index, indremove)

                    dfqual[depth, :] = 1
                    dfqual[depth, vec_index] = 0

    ntime = dfplot.shape[1]

    for time in range(0, ntime):
        vec = np.copy(dfplot[:, time])
        vec_depth = np.copy(depth_vec)
        vec_qual = np.copy(dfqual[:, time])
        vec_index = np.array(range(0, len(vec)))

        ind = np.where(vec_qual == 1)[0]
        vec_index = np.delete(vec_index, ind)
        vec = np.copy(dfplot[:, time])[vec_index]
        vec_depth = np.copy(depth_vec)[vec_index]
        vec_qual = np.zeros(len(vec))

        tempdiff = np.diff(vec)
        depthdiff = np.diff(vec_depth)
        vec_diff = tempdiff / depthdiff

        indremove_vertical = np.where(vec_diff > depth_grad_threshold)[0]

        if len(indremove_vertical) > 0:
            for layer in range(0,len(indremove_vertical)):
                if vec[indremove_vertical[layer] +1] > vec[indremove_vertical[layer]]:
                    indremove_vertical = np.unique(indremove_vertical)
                else:
                    indremove_vertical = np.unique(indremove_vertical)+1

            vec_index = np.delete(vec_index, indremove_vertical)

            dfqual[:, time] = 1
            dfqual[vec_index, time] = 0

    for depth in range(0, ndepth):
        if np.quantile(dfqual[depth,:], round(1-perc_good,1))==1:
            dfqual[depth,:] = np.ones(ntime)

    return dfqual
