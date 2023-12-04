import streamlit as st
import pandas as pd
import matplotlib as plt
import seaborn as sns
import numpy as np
import scipy as sc

df = pd.read_csv('mcdonalds_dataset.csv')

def swap_columns(df, col1, col2):
    col_list = list(df.columns)
    x, y = col_list.index(col1), col_list.index(col2)
    col_list[y], col_list[x] = col_list[x], col_list[y]
    df = df[col_list]
    return df

df = swap_columns(df, 'lat', 'lon')

df.rename(columns = {'lon':'latitude', 'lat':'longitude'}, inplace = True)

st.map(data = df)