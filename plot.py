import geopandas as gpd
import matplotlib.pyplot as plt
import plotly.express as px
import pandas as pd


from analysis.plotSolutions import *
from readData.readLocationData import *
from readData.readOtherData import *
from analysis.exploreSolution import *

from datetime import datetime, timedelta
from readData.readContractData import *
from readData.readVesselData import *
from readData.readSpotData import *
from supportFiles.constants import *


"""
File for plotting different stuffz
"""


## Example of how to plot a gant chart ##
group1 = 'A-2L-60D'
datafile1 = 'A-2L-6U-11F-7V-60D-a'
logFile1 = f'jsonFiles/A-2L-60D/A-2L-6U-11F-7V-60D-a/03-22-2023, 20-08.json'
solutionData = read_solved_json_file(logFile1)
#contract_gant_chart(solutionData, group1, datafile1, UNLOADING) #Can plot both loading and unloading
#plot_inventory_levels(solutionData, group1, datafile1)
plot_produced_lng(solutionData, group1, datafile1)