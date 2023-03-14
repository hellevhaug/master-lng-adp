import numpy as np
import pandas as pd
import matplotlib.pyplot as plt 


"""
File defining helper-functions for plotting different aspects of a solution
"""

def get_coordinates_dataframe():
    path = 'supportFiles/coordinates.csv'
    df = pd.read_csv(path, delimiter=',')
    df = df.set_index(['ID'])
    return df


def reformat_coordinates_dataframe(df):
    longitude = {}
    latitude = {}
    for index, row in df.iterrows(): 
        latitude[row['ID']] = row['Latitude']
        longitude[row['ID']] = row['Longitude']
    return longitude, latitude