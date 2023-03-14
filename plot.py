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

