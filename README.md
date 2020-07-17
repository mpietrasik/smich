# smich

This repository contains the code for the paper "Path Based Hierarchical Clustering on Knowledge Graphs" by Marcin Pietrasik and Marek Reformat.

## Installation

The code for our method uses the Python 3.6.6 standard library, no outside packages are required to be installed. Simply extract the dataset archives in the datasets directory and run `python main.py`

## Runtime Instructions

main.py takes three optional command line arguments:

| Parameter                 | Default       | Description   |	
| :------------------------ |:-------------:| :-------------|
| -d --dataset 	      |	dbpedia50000  | name of dataset in datasets directory on which subsumption axioms are generated
| -a --alpha          | 0.7           | value of alpha, the decay hyperparameter
| -m --metrics             | False         | boolean value indicating whether or not to calculate f1 metrics