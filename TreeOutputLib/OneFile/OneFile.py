#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@date: 2021-Today
@author: marie-christin.wimmler@tu-dresden.de
"""
import os
from TreeOutputLib.TreeOutput import TreeOutput


## Output class. This class creates one file for the whole simulation,
# i.e. each time step and tree is included.
# A line contains time, tree, position, desired geometric measures
# and parameters for every nth time step.
class OneFile(TreeOutput):

    def __init__(self, args):
        super().__init__(args)

        # Check if csv file exists in directory
        # If not, create file
        files_in_folder = os.listdir(self.output_dir)
        self.delimiter = "\t"
        self.filename = "Population.csv"
        file = open(os.path.join(self.output_dir, self.filename), "a")

        string = ""
        if self.filename not in files_in_folder:
            string += 'tree' + self.delimiter + 'time' + self.delimiter + 'x' + \
                      self.delimiter + 'y'
            string = self.addSelectedHeadings(string, self.delimiter)

            string += "\n"
            file.write(string)
        file.close()

    def outputContent(self, tree_groups, time, **kwargs):
        if not kwargs["group_died"]:
            file = open(os.path.join(self.output_dir, self.filename), "a")
        else:
            file = open(os.path.join(self.output_dir, 'Population_group_died.csv'), "a")

        string = ""
        for group_name, tree_group in tree_groups.items():
            for tree in tree_group.getTrees():
                growth_information = tree.getGrowthConceptInformation()
                string += (group_name + "_" + "%09.0d" % (tree.getId()) +
                           self.delimiter + str(time) + self.delimiter +
                           str(tree.x) + self.delimiter + str(tree.y))
                string = self.addSelectedOutputs(tree, string, self.delimiter,
                                                 growth_information)
                string += "\n"
                for growth_output in self.growth_outputs:
                    del (growth_information[growth_output])
        file.write(string)
        file.close()
