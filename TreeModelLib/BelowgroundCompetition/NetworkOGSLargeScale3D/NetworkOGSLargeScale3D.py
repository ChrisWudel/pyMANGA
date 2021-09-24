#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@date: 2021-Today
@author: marie-christin.wimmler@tu-dresden.de
"""

import numpy as np
import os
from os import path

from TreeModelLib.BelowgroundCompetition.SimpleNetwork import SimpleNetwork
from TreeModelLib.BelowgroundCompetition.OGSLargeScale3D import OGSLargeScale3D


class NetworkOGSLargeScale3D(SimpleNetwork, OGSLargeScale3D):

    ## OGS integration and network approach (root grafting) for below-ground
    # competition concept. This case is using OGSLargeScale3D and
    # SimpleNetwork as parent classes.
    # @param args: Please see input file tag documentation for details
    # @date: 2021 - Today
    def __init__(self, args):
        OGSLargeScale3D.__init__(self, args)
        SimpleNetwork.getInputParameters(self, args)

    ## This functions prepares the tree variables for the
    # NetworkOGSLargeScale3D concept.\n
    #  @param t_ini - initial time for next time step \n
    #  @param t_end - end time for next time step
    def prepareNextTimeStep(self, t_ini, t_end):
        ## Load both prepartNextTimeStep methods
        # The only parameters occurring in both are t_ini and t_end and as
        # the ones from OGS are needed, OGS needs to be loaded after network
        SimpleNetwork.prepareNextTimeStep(self, t_ini, t_end)
        OGSLargeScale3D.prepareNextTimeStep(self, t_ini, t_end)

        # Initialize new variables for this concept
        self._tree_contribution = []
        self._contributions = np.zeros_like(self._volumes)
        self._tree_cell_volume = []

        self._psi_osmo = []

    ## Before being able to calculate the resources, all tree enteties need
    #  to be added with their current implementation for the next time step.
    #  Here, in the OGS case, each tree is represented by a contribution to
    #  python source terms in OGS. To this end, their resource uptake is
    #  saved in numpy arrays.
    #  @param tree
    def addTree(self, tree):
        # SimpleNetwork stuff
        SimpleNetwork.addTree(self, tree)

        # OGS stuff
        x, y = tree.getPosition()
        affected_cells = self._cell_information.getCellIDsAtXY(x, y)
        self._tree_cell_ids.append(affected_cells)
        v = OGSLargeScale3D.getVolume(self, affected_cells)
        self._tree_cell_volume.append(v)

    ## This function creates an array with values of osmotic potential based
    # on values saved in network attributes (this is the osmotic potential
    # calculated at the end of the last time step). If a new tree with osmotic
    # potential = 0 is recruited, the initial value is approximated by
    # averaging the osmotic potential below the other trees. Note: this might
    # lead to inaccurate starting values if (i) the time step length of MANGA
    # is very large and (ii) if trees are recruited and no or not many trees
    # exist.
    def addPsiOsmo(self):
        psi_osmo = self.network['psi_osmo']
        # Case: self.network['psi_osmo'] is empty
        if psi_osmo:
            self._psi_osmo.append(np.array(psi_osmo))
        # Case: self.network['psi_osmo'] is not empty
        else:
            mean_of_others = np.mean(self._psi_osmo)
            # Case: there are no other trees with osmotic potential yet
            if np.isnan(mean_of_others):
                self._psi_osmo.append(0)
            # Case: starting value for this tree is the average osmotic
            # potential of existing trees
            else:
                self._psi_osmo.append(mean_of_others)

    ## This function updates and returns BelowgroundResources in the current
    #  time step. For each tree a reduction factor is calculated which is
    #  defined as: resource uptake at zero salinity and without resource
    #  sharing (root grafting)/ actual resource uptake.
    def calculateBelowgroundResources(self):
        ## SimpleNetwork stuff - calculate amount of water absorbed from
        # soil column
        # Convert psi_osmo to np array in order to use in
        # calculateBGresourcesTree()
        self._psi_osmo = np.array(self._psi_osmo)
        SimpleNetwork.groupFormation(self)
        SimpleNetwork.rootGraftFormation(self)
        SimpleNetwork.calculateBGresourcesTree(self)

        # Map water absorbed as contribution to respective cells
        # Convert water_abs from m³/time step to kg/s
        self._tree_contribution = self._water_absorb * 1000 / self.time

        for cell_ids, volume, contribution in zip(self._tree_cell_ids,
                                                  self._tree_cell_volume,
                                                  self._tree_contribution):
            for cell_id in cell_ids:
                # a trees contribution to each cell in the grid is added a
                # source rate (kg per volume per s)
                self._contributions[cell_id] += contribution * (1 / volume)

        ## OGS stuff
        # Copy scripts, write bc inputs, run OGS
        OGSLargeScale3D.copyPythonScript(self)
        np.save(path.join(self._ogs_project_folder, "complete_contributions.npy"),
                self._contributions)
        self.runOGSandWriteFiles()

        # Calculate bg factor
        # Get cell salinity array from external files
        OGSLargeScale3D.getCellSalinity(self)
        # Calculate salinity below each tree
        OGSLargeScale3D.calculateTreeSalinity(self)

        self.belowground_resources = self.getBGfactor()


        # Update network parameters
        SimpleNetwork.updateNetworkParametersForGrowthAndDeath(self)

        # OGS stuff - update ogs parameters
        self.renameParameters()

    ## This function returns the directory of the python_source file in the
    # directory of the concept if no external source file is provided.
    def getSourceDir(self):
        # ToDo: @JB: this is exactly the same function as in super() - how
        #  can we avoid this but also get the directory of the concept
        return path.join(path.dirname(path.abspath(__file__)),
                          "python_source.py")