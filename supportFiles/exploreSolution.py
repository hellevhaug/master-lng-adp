import json 

"""
Functions for analyzing a solved model and its optimal variable values 
"""

# example: path = 'jsonFiles/A-1L-60D/A-1L-6U-11F-7V-60D-a/02-20-2023 22:00.json'

def read_solved_model(path):
    file = open(path)
    data = json.load(file)
    
    return data



