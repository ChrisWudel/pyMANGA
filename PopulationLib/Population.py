#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@date: 2018-Today
@author: jasper.bathmann@ufz.de
"""

from PopulationLib import PlantGroup


class Population:

    def __init__(self, args):
        self.plant_groups = {}
        self.plants = []
        for arg in args.iter("group"):
            self.addPlantGroup(arg)

    def addPlantGroup(self, args):
        plant_group = PlantGroup(xml_args=args)
        self.plant_groups[plant_group.group_name] = plant_group

    def getPlantGroups(self):
        return self.plant_groups

    def getPlantGroup(self, name):
        return self.plant_groups[name]

    def getUngroupedPlants(self):
        return self.plants

    def getPlants(self):
        all_plants = []
        for name, group in self.plant_groups.items():
            for plant in group.getPlants():
                all_plants.append(plant)
        all_plants.append(self.plants)
        return all_plants

    def getNumberOfPlants(self):
        n_plants = 0
        for name, group in self.plant_groups.items():
            n_plants += group.getNumberOfPlants()
        n_plants += len(self.plants)
        return n_plants
