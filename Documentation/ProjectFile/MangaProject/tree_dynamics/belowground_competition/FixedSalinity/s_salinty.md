

There are two ways to indicate the salinity of the bottom water: Either two values, each for the location defined via max_x and min_x (option 1), or a time series with values for these (option 2).

Option 1:<br>
salinity in kg/kg. e.g. 35 ppt corresponds to 0.035. Two values (max and min) need to be specified.<br>
Example:<br>
<salinity> 0.005 0.095 </salinity><br>
<br>
Option 2:<br>
Path to file containing salinity in kg/kg. e.g. 35 ppt corresponds to 0.035. Two values (max and min) need to be specified for each timestep you want to define the salinity. For timestep there is no value the salinity will be linearly interpolated.
The input file has to be a csv file with semicolon as seperator. There must be three values in each line: The time and the two values for the salinity. The first row is seen as a header and therefore ignored.<br>
<br>
Example:<br>
<salinity> test/SmallTests/inputFiles/salinity_A.csv </salinity><br>
Example file structure:<br>
t_step;salinity_1;salinity_2<br>
0;0.010;0.020<br>
1000000;0.011;0.021<br>
2000000;0.012;0.022<br>
