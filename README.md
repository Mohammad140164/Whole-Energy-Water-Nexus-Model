# Whole-Energy-Water-Nexus-Model

---
📌 Overview

This repository contains all computational materials developed for the research project:

"Beyond Facility-Level Metrics: A Whole-System Energy–Water Nexus Analysis of Data Centre Integration in Great Britain’s Net-Zero Transition"

The repository provides:

Mathematical modelling framework
Input datasets
Scenario-based analysis results
Supporting materials for reproducing the study outcomes

The project investigates the integration of data centres within the UK energy transition while considering the interdependencies between energy systems, water resources, and climate impacts.

---
📂 Repository Structure

The repository is organised as follows:

.
├── Code/
│   └── Rolling Horizon with water.py
│
├── Input Data/
│   └── Cooling.xlsx and Input UK 5 year.xlsx
│
├── Results/
│   └── Results for all investigated scenarios
│
└── README.md

---
💻 Model Execution


The main model file is:

Rolling Horizon with water.py

To execute the model:

Place the required files from the Input Data folder in the same directory as the code.
Configure solver settings if required.
Run the Python script.

The model will generate outputs corresponding to the defined energy–water transition scenarios.

For the PUE/WUE calculations, based on the region and corresponding climate zone, please run the ML model/code for estimating PUE and WUE.

We acknowledge the following research, on which our methodology builds:

N. Lei and E. Masanet, “Climate- and technology-specific PUE and WUE estimations for U.S. data centers using a hybrid statistical and thermodynamics-based approach,” *Resources, Conservation and Recycling*, vol. 182, 2022, 106323. https://doi.org/10.1016/j.resconrec.2022.106323.



---
📊 Results

The complete results for all investigated scenarios are provided in Results Folder under different scenarios 

---
📬 Support

The authors provide guidance and technical support regarding:

Model execution
Input data preparation
Solver configuration
Troubleshooting

For technical enquiries, please contact the project authors.


---
👥 Authors

Mohammad Hemmati
📧 m.hemmati@ucl.ac.uk

Vassilis M. Charitopoulos
📧 v.charitopoulos@ucl.ac.uk
