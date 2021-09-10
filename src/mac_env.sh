#!/bin/bash

# Virtual environment 
conda env list
conda activate tfm

# Libraries needed
conda install selenium
conda install beautifulsoup4
conda install lxml
pip install pandas
pip install tqdm
pip install whois
pip install builtwith
conda install -c conda-forge geckodriver
pip install wget
