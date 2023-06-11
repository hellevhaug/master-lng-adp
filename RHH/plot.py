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
group1 = 'N-1L-B'
datafile1 = 'N-1L-13U-10F-23V-120D'
logFile1 = f'jsonFiles/N-1L-B/N-1L-13U-10F-23V-120D/varprodplot.json'
#spotGroup = 'spotTests'
#spotDataFile = 'N-1L-10U-6F-23V-60D'
#spotLogFile = f'jsonFiles/spotTests/N-1L-10U-6F-23V-60D/05-19-2023, 19-53.json'

solutionData = read_solved_json_file(logFile1)
#contract_gant_chart(solutionData, group1, datafile1, UNLOADING) #Can plot both loading and unloading
plot_inventory_levels(solutionData, group1, datafile1)
plot_produced_lng(solutionData, group1, datafile1)