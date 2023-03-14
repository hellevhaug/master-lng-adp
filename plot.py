import geopandas as gpd
import matplotlib.pyplot as plt
import plotly.express as px
import pandas as pd


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



def gant_chart(data):

    #Må hente startdate for planning horizon for df skal ta inn DATO
    df = pd.DataFrame([])

    des_contract_ids = read_des_contracts() #Lag liste med alle des_contracts
    


    x_dict = get_x_vars(data) #sjekke hva som skal puttes inn her
    g_dict = get_g_vars(data)
    z_dict = get_z_vars(data)

    for (v,i,t,j,t_), value in x_dict.items():
        if round(value, 0) == 1 and j in des_contract_ids: #Hente ut des_contract_ids
            t_date = 0
            df.append(dict(Contract=j, Start=t_-1, Finish=t_))

    for (i,t,j), value in g_dict.items(): #Hente data fra charter-operational-time
        if round(value, 0) != 0: 
            df.append(dict(Contract=j, Start=t-1, Finish=t))
        

    for (f,t_), value in z_dict.items(): 
        if round(value, 0) != 0:
            df.append(dict(Contract=j, Start=t_-1, Finish=t_))


    fig = px.timeline(df, x_start="Start", x_end="Finish", y="Contract")
    fig.update_yaxes(autorange="reversed") # otherwise tasks are listed from the bottom up
    fig.show()


    return 0

# Oppskrift på gantt chart: 
'''
import plotly.express as px
import pandas as pd

df = pd.DataFrame([
    dict(Task="Job A", Start='2009-01-01', Finish='2009-02-28'),
    dict(Task="Job B", Start='2009-03-05', Finish='2009-04-15'),
    dict(Task="Job C", Start='2009-02-20', Finish='2009-05-30')
])

fig = px.timeline(df, x_start="Start", x_end="Finish", y="Task")
fig.update_yaxes(autorange="reversed") # otherwise tasks are listed from the bottom up
fig.show()
'''