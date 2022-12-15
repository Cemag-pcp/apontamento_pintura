import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import streamlit as st
from gspread_formatting import *
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
import time
from PIL import Image
from datetime import date
import datetime

#Base gerador de ordem de producao

# Connect to Google Sheets

scope = ['https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive"]

credentials = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
client = gspread.authorize(credentials)
sa = gspread.service_account('service_account.json')

# ======================================= #

st.markdown("<h1 style='text-align: center; font-size:60px; color: White'>Apontamento de produção</h1>", unsafe_allow_html=True)

with st.sidebar:
    image = Image.open('logo-cemagL.png')
    st.image(image, width=300)
    
name_sheet = 'Base gerador de ordem de producao'
worksheet = 'Pintura'
sh = sa.open(name_sheet)
wks = sh.worksheet(worksheet)
list1 = wks.get_all_records()
table = pd.DataFrame(list1)
table = table.drop_duplicates()

lista_unicos = table[['DATA DA CARGA']].drop_duplicates()[1:]

name_sheet1 = 'Base ordens de produçao finalizada'
worksheet1 = 'geral'
sh1 = sa.open(name_sheet1)
wks1 = sh1.worksheet(worksheet1)
list2 = wks1.get_all_records()
table1 = pd.DataFrame(list2)
table1 = table1.drop_duplicates()

n_op = '20/12/2022'

n_op = st.sidebar.selectbox('Selecione o código da ordem:', lista_unicos)

def consultar(n_op,sh,wks):
            
    filter_ = table.loc[(table['DATA DA CARGA'] == n_op)]        
    
    filter_['qt. produzida'] = 0
            
    filter_ = filter_.reset_index(drop=True)

    if len(table1.loc[(table1['DATA DA CARGA'] == n_op)]) != 0:
        
        tab2 = table1.loc[(table1['DATA DA CARGA'] == n_op)]        

        qt_total = tab2[['CODIGO','QT PROD.']].groupby(['CODIGO']).sum().reset_index()

        table_geral = pd.merge(filter_,qt_total, how = 'inner', on = 'CODIGO' )
        table_geral = table_geral.rename(columns={'QT PROD.':'QT APONTADA'}) 
        table_geral = table_geral[['CODIGO', 'DESCRICAO', 'QT_ITENS','COR', 'qt. produzida', 'QT APONTADA']]
    else:
        table_geral = filter_[['CODIGO', 'DESCRICAO', 'QT_ITENS', 'COR', 'qt. produzida']]
        table_geral['QT APONTADA'] = 0
                
    gb = GridOptionsBuilder.from_dataframe(table_geral)
    gb.configure_column('qt. produzida', editable=True)
    grid_options = gb.build()
    grid_response = AgGrid(table_geral, gridOptions=grid_options,
                           height=400,
                           width='100%',
                           data_return_mode='AS_INPUT',
                           update_model='MODEL_CHANGE\D', 
                           fit_columns_on_grid_load=True)
    
    filter_new = grid_response['data']
    
    filter_new['DATA DA CARGA'] = n_op

    if st.button("Salvar"):  
          
        filter_new = filter_new.replace({'qt. produzida':{'':0}})
        filter_new = filter_new.drop(columns={'QT APONTADA'})
        filter_new['qt. produzida'] = filter_new['qt. produzida'].astype(int)
        filter_new = filter_new.values.tolist()
        sh1.values_append(worksheet1, {'valueInputOption': 'RAW'}, {'values': filter_new})
    
if n_op != '':
    consultar(n_op,sh,wks)