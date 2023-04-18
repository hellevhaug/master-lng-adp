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
spotGroup = 'spotTests'
spotDataFile = 'N-1L-10U-6F-23V-60D'
spotLogFile = f'jsonFiles/spotTests/N-1L-10U-6F-23V-60D/04-17-2023, 15-36.json'

solutionData = read_solved_json_file(spotLogFile)
contract_gant_chart(solutionData, spotGroup, spotDataFile, UNLOADING) #Can plot both loading and unloading
plot_inventory_levels(solutionData, spotGroup, spotDataFile)
plot_produced_lng(solutionData, spotGroup, spotDataFile)