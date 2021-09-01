#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@date: 2021-Today
@author: marie-christin.wimmler@tu-dresden.de
"""

## This is an example file for an OGS boundary condition using MANGA external
# Directories and file names need to be updated

import OpenGeoSys
import sys
import numpy as np
import vtk as vtk

sys.path.append("/Users/admin/Documents/GRIN/git_repos/")
import pyMANGA


# approx. of MANGA time step size in days
manga_timestep_days = 1  # 10

# initialize MANGA model
xml_dir = "/Users/admin/Documents/GRIN/git_repos/pyMANGA/" \
          "test/SmallTests/Test_Setups_small/"
xml_file = "ExternalOGS.xml"  # AllSimple

model = pyMANGA.Model(xml_dir + xml_file)
model.createExternalTimeStepper()

# OGS stuff
seaward_salinity = 0.035
# read source mesh
source_mesh = '/Users/admin/Documents/GRIN/git_repos/pyMANGA' \
              '/test/LargeTests/Test_Setups_large/external_setup' \
              '/source_domain.vtu'


class CellInformation:
    def __init__(self, source_mesh):
        meshReader = vtk.vtkXMLUnstructuredGridReader()
        meshReader.SetFileName(source_mesh)
        meshReader.Update()
        self.grid = meshReader.GetOutput()
        self.cell_finder = vtk.vtkCellLocator()
        self.cell_finder.SetDataSet(self.grid)
        self.cell_finder.LazyEvaluationOn()
        cells = self.grid.GetCellData()
        self.volumes = cells.GetArray("Volume")
        self.number_of_cells = meshReader.GetNumberOfCells()

    def getCellId(self, x, y, z):
        cell_id = self.cell_finder.FindCell([x, y, z])
        return cell_id

    def getCellNo(self):
        return self.number_of_cells


class FluxToTrees(OpenGeoSys.SourceTerm):
    def getFlux(self, t, coords, primary_vars):
        global tree_contributions
        global i
        global t_before
        # OGS stuff - call per time step and cell
        salinity = primary_vars[1]
        cell_id = cell_information.getCellId(coords[0], coords[1], coords[2])
        calls[cell_id] += 1
        cumsum_salinity[cell_id] += salinity

        # MANGA stuff - ones each time step
        # calculation in last call of las cell
        no_cells = cell_information.getCellNo()

        if cell_id == no_cells - 1 and calls[no_cells - 1] == np.max(calls[0]):
            # update MANGA-BC only if time increased
            # if t > t_before:
            # update MANGA-BC only after a certain time
            time_diff = t - t_before
            if time_diff >= manga_timestep_days * 3600 * 24:
                print(">> MANGA step: " + str(i) + ", t: " +
                      str(np.round(t / 3600 / 24, 1)) +
                      ", max. S: " + str(np.round(np.max(
                      cumsum_salinity / calls) * 1000, 1)))
                model.setBelowgroundInformation(
                    cumsum_salinity=cumsum_salinity,
                    calls_per_cell=calls)
                model.propagateModel(t)
                tree_contributions = model.getBelowgroundInformation()
                t_before = t
                i += 1

        positive_flux = tree_contributions[cell_id]
        Jac = [0.0, 0.0]

        return -positive_flux, Jac


# counter to monitor number of MANGA executions
i = 1
# time of last time step
t_before = 0

# define global variables/ cell information
cell_information = CellInformation(source_mesh)
no_cells = cell_information.getCellNo()
cumsum_salinity = np.zeros(no_cells) + seaward_salinity
calls = np.zeros(no_cells) + 1
tree_contributions = np.zeros(no_cells)

# instantiate source term object referenced in OpenGeoSys' prj file
flux_to_trees = FluxToTrees()
