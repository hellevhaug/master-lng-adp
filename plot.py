import geopandas as gpd
import matplotlib.pyplot as plt

from analysis.plotSolutions import *
from readData.readLocationData import *
from readData.readOtherData import *
from analysis.exploreSolution import *

"""
File for plotting different stuffz
"""

def plot_ports(df):
    countries = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
    countries = countries.drop(159) # Antartica
    fig, ax = plt.subplots(figsize=(8,6))

    countries.plot(color="lightgrey",ax=ax)

    df.plot(x="longitude", y="latitude", kind="scatter", 
            c="red", colormap="YlOrRd", 
            title="All loading- and unloading ports", 
            ax=ax)

    plt.show()


def plot_vessel_routes(group, filename, solutionPIT):
    df = get_coordinates_dataframe()

    return 0


def plot_inventory_storage():

    return 0


def plot_full_solution(group, filename, solutionPIT):

    data = read_data_file(group, filename)
    

    return 0

"""
countries = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
for index, row in countries.iterrows():
    print(index, row['name'])
countries = countries.drop(23)
"""

df = get_coordinates_dataframe()
plot_ports(df)

### Gantt Chart ###

import plotly.express as px
import pandas as pd


def gant_chart(datafile, variablesAsDict):

    df = pd.DataFrame([])

    for x in x-dict: #kommer an på formatet Helle lager
        if round(x.value, 0) == 1 and x.contract in descontractInDatafile:
            df.append(dict(Contract=x[j], Start=x[t_]-1, Finish=x[t_]))

    for g in g-dict: 
        if round(g.value, 0) != 0: 
            df.append(dict(Contract=g[j], Start=g[t_]-1, Finish=g[t_]))
        

    for z in z-dict: 
        if round(z.value, 0) != 0:
            df.append(dict(Contract=z[j], Start=z[t_]-1, Finish=z[t_]))


    fig = px.timeline(df, x_start="Start", x_end="Finish", y="Contract")
    fig.update_yaxes(autorange="reversed") # otherwise tasks are listed from the bottom up
    fig.show()


    return 0

