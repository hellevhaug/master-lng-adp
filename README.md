# LNG-ADP - Optimization of the ADP in LNG transport
Repository for TIØ4905 - Managerial Economics and Operations Research, Master thesis,
Norwegian University of Technology and Science
----------------------------------------------------------------------------------------

### Sanna Baug Warholm, Sigrid Hallem Solum and Helle Villmones Haug 
This repository contains the code for the RHH algorithm outlined in our master's thesis conducted at NTNU during the spring of 2023. The RHH is adopted to solve the LNG Annual Delivery Program with Speed Optimization and Multiple Loading ports (LNG-ADP-SO-MLP) described in the thesis. The thesis contains a study of relevant literature, descriptions of the problem and algorithm implementation and a computational study outlining results. A mathematical formulation of the problem is also provided. The pdf of the thesis is provided in the 'thesis' pdf-file.

### commercial solver
The code for the arc-flow model presented in Chapter 5 is found in the folder ”commercial solver”. Code for reading data from is located at ”commercial solver/readData”, and includes reading data for contracts, ports, vessels, spot and other relevant sets. Code for initializing arcs, constraints and the Gurobi model is located at ”commercial solver/runModel/”, in addition to files for running the model. Files for initialzing the greedy construction heuristic described in Section 6.4 is also located in this folder. Gurobi logfiles is located at ”commercial solver/logFiles”, and model output files is saved in the ”commercial solver/jsonFiles” folder. Different constants set before running the model are specified in the file ”commercial solver/supportFiles/constants.py”.

### RHH
The code structure for the Rolling Horizon Heuristic is identical to the commercial solver folder structure described above. The main difference in located in the ”RHH/runModel” folder, where the files for both initialization and running is implemented for the RHH instead. Particulary, the implementation of the different compontents of the Rolling Horizon Heuristic is located in the files ”RHH/runModel/runModel.py” and ”RHH/runModel/initModelRHH.py”.

### Structure 

🧐 analysis: Different functions for analyzing test instances and solutions

🏹 arcs: Folder for saving arcs

📚 jsonFiles: Model output files with json-format

ℹ️ logFiles: Gurobi logfiles for different test instances

👓 readData: Files for reading in the test data

🏃‍♀️ runModel: Files for running the model with different settings, described at the top of the page for each file.


----------------------------------------------------------------------------------------

Feel free to contact us on hellevha@stud.ntnu.no if you have any questions.
