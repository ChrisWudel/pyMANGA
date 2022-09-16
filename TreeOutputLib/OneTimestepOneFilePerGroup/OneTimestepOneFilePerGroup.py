#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@date: 2018-Today
@author: jasper.bathmann@ufz.de
"""
from TreeOutputLib.OneTimestepOneFile.OneTimestepOneFile import \
    OneTimestepOneFile
import os


## Output class. This class creates one file per timestep per group at a
#  defined location. A line containing time, position, desired geometric
#  measures and desired parameters is written at every nth timestep.
class OneTimestepOneFilePerGroup(OneTimestepOneFile):
    ## Writes output to predefined folder
    #  For each timestep a file is created throughout the simulation.
    #  This function is only able to work, if the output directory exists and
    #  is empty at the beginning of the model run
    def writeOutput(self, tree_groups, time):
        self._output_counter = (self._output_counter %
                                self.output_each_nth_timestep)
        it_is_output_time = True
        if self.output_times is not None:
            it_is_output_time = (time in self.output_times)
        if self._output_counter == 0 and it_is_output_time:
            delimiter = "\t"
            for group_name, tree_group in tree_groups.items():
                filename = (group_name + "_t_%012.1f" % (time) + ".csv")
                file = open(os.path.join(self.output_dir, filename), "w")
                string = ""
                string += 'tree' + delimiter + 'time' + delimiter + 'x' +  \
                          delimiter + 'y'
                string = OneTimestepOneFile.addSelectedHeadings(
                    self, string, delimiter)
                string += "\n"
                file.write(string)
                for tree in tree_group.getTrees():
                    growth_information = tree.getGrowthConceptInformation()
                    string = ""
                    string += (group_name + "_" + "%09.0d" % (tree.getId()) +
                               delimiter + str(time) + delimiter +
                               str(tree.x) + delimiter + str(tree.y))
                    string = OneTimestepOneFile.addSelectedOutputs(
                        self, tree, string, delimiter, growth_information)
                    string += "\n"
                    file.write(string)
                    for growth_output in self.growth_outputs:
                        del (growth_information[growth_output])
                file.close()
        self._output_counter += 1
