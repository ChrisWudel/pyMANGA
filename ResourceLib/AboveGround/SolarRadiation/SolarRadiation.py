#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@date: 2024-January
@author: github.com/rbnmj/
"""
import numpy as np
from scipy.optimize import curve_fit
from ResourceLib import ResourceModel


class SolarRadiation(ResourceModel):
    def __init__(self, args):
        """
        Above-ground resource concept.
        Solar radiation model based on Allen et al. 1998.
        Requires daily minimum and maximum temperature, latitude and day of the year.
        Args:
            args (lxml.etree._Element): Module specifications from project file tags
        """
        case = args.find("type").text
        self.getInputParameters(args)
        try:
            self._albedo
        except:
            # defaul albedo assumes green vegetation (Allen et al, 1998)
            self._albedo = 0.23
        try:
            self._altitude
        except:
            # default altitude assumes sea level
            self._altitude = 0
        self._doy = 1
        self.calculateNetRadiation()

    def calculateNetRadiation(self):
        """
        Calculates net radiation for each month and fits a sine curve to the data.
        Sine parameters are then used to estimate net radiation over the course of the year.
        Variation is drawn from a normal distribution. 
        Normal distribution mean is either taken from user input or based on the standard deviation of the net radiation estimate.
        Default noise takes into account a more stable moving average for summer months based on Barr et al. 2014.
        Final net radiation is clipped at 0 to avoid negative net radiation and at the clear sky maximum net radiation.
        """
        # calculate monthly radiation
        self.monthly_net_rad = []
        self.doy15 = [15, 46, 74, 105, 135, 166, 196,
                      227, 258, 288, 319, 349]  # 15th of each month
        for doy in self.doy15:
            # solar declination
            d = 0.409*np.sin((2*np.pi/365)*doy-1.39)
            # sunset hour angle
            # if >= 1, 24hrs of daylight, if <= -1, 24hrs of darkness (see pyeto docs)
            w_s_temp = -np.tan(self._latitude)*np.tan(d)
            w_s = np.arccos(min(max(w_s_temp, -1), 1))
            # inverse relative distance Earth-Sun based on doy
            ird = 1 + (0.033*np.cos((2*np.pi/365)*doy))
            # extraterrestrial radiation
            solarconstant = 0.0820  # MJ m-2 min-1
            r_a_temp1 = ((24*60)/np.pi)
            r_a_temp2 = w_s * np.sin(self._latitude) * np.sin(d)
            r_a_temp3 = np.cos(self._latitude) * np.cos(d) * np.sin(w_s)
            r_a = r_a_temp1 * solarconstant * ird * (r_a_temp2 + r_a_temp3)
            # incoming solar radiation
            r_s = (0.7*r_a)-4  # assuming island #(0.25 + (0.5 * N))*R_a
            # net shortwave radiation
            r_ns = (1-self._albedo)*r_s
            # actual vapor pressure (substract 2 deg C from tmin in arid/semi arid areas)
            e_a = 0.611 * np.exp((17.27 * self._tmin) / (self._tmin + 237.3))
            # clear sky radiation
            r_so = (0.00002 * self._altitude + 0.75)*r_a
            # net longwave radiation
            boltzmann = 0.000000004903 # Stefan Boltzmann constant [MJ K-4 m-2 day-1]
            r_nl = boltzmann*(((self._tmax)**4+(self._tmin)**4)/2) * \
                (0.34-(0.14*np.sqrt(e_a)))*(1.35*(r_s/r_so)-0.35)
            # daily net radiation
            r_n = r_ns - r_nl
            self.monthly_net_rad.append(r_n)

        # fit sine curve to monthly net radiation
        # popt is an array of optimal values for the sine parameters so that sum of squared residuals is minimized e.g. best fit
        # popt contains amplitude, frequency, phase_shift and vertical_shift to pass to sineFunction
        popt = curve_fit(self.sineFunction, self.doy15,
                         self.monthly_net_rad)[0]
        self.sinus_params = popt

        self.net_rad_365 = self.sineFunction(
            np.arange(1, 366), *self.sinus_params)
        self.net_rad_max = max(self.net_rad_365)

        # add noise
        try:
            # user input noise
            self._noise
            noise = np.random.normal(
                scale=self._noise, size=self.net_rad_365.shape)
            self.net_rad_365_noise = self.net_rad_365 + noise
            self.net_rad_365_clipped = np.clip(
                self.net_rad_365_noise, 0, self.net_rad_365)
        # use standard deviation std as default
        except:
            # default noise
            noise = np.random.normal(
                scale=0.5*np.std(self.net_rad_365), size=self.net_rad_365.shape)
            self.net_rad_365_noise = self.net_rad_365 + noise
            # moving average is nearly constant for summer months (Barr et al 2014)
            # add higher noise for summer months
            noise2 = np.random.normal(
                scale=5*np.std(self.net_rad_365[104:250]), size=self.net_rad_365[104:250].shape)
            self.net_rad_365_noise[104:250] -= + noise2
            # clip noise
            # noise can only add "negative noise" as net radiation is calculated from a theoretical clear sky maximum
            # net radiation can not be negative so we clip the noise at 0
            self.net_rad_365_clipped = np.clip(
                self.net_rad_365_noise, 0, self.net_rad_365)

        # final net radiation
        self.net_rad_year = self.net_rad_365_clipped

    def sineFunction(self, t, amplitude, frequency, phase_shift, vertical_shift):
        """
        Basic sine function skeleton to fit to the monthly net radiation.
        """
        return amplitude * np.sin(2 * np.pi * frequency * t + phase_shift) + vertical_shift

    def getInputParameters(self, args):
        tags = {
            "prj_file": args,
            "required": ["type", "latitude", "tmin", "tmax"],
            "optional": ["albedo", "altitude", "noise"]
        }
        super().getInputParameters(**tags)
        if -np.pi/2 <= self.latitude <= np.pi/2:
            self._latitude = self.latitude
            print(
                "If latitude input ranges from -pi/2 to pi/2 pyMANGA assumes radians.")
        else:
            self._latitude = np.deg2rad(self.latitude)
        self._tmin = self.tmin
        self._tmax = self.tmax
        try:
            self._albedo = self.albedo
        except:
            pass
        try:
            self._altitude = self.altitude
        except:
            pass
        try:
            self._noise = self.noise
        except:
            pass

    def calculateAbovegroundResources(self):
        """ 
        Accesses net radiation for current day and scales it between 0 and 1
        to make it accessible for the resource model.
        """
        # pull radiation for current day
        self.net_rad = self.net_rad_year[self._doy-1]

        # scale net radiation between 0 and 1
        self.net_rad_scale = self.net_rad / self.net_rad_max
        self.aboveground_resources = self.net_rad_scale

    def prepareNextTimeStep(self, t_ini, t_end):
        self.radiation = []
        self.t_ini = t_ini
        self.t_end = t_end
        if self._doy < 365:
            self._doy += 1
        else:
            self._doy = 1
        self.no_plants = 0

    def addPlant(self, plant):
        # Count the number of plants in the system
        self.no_plants += 1
