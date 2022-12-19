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
import numpy as np

#Base gerador de ordem de producao

# Connect to Google Sheets
# ======================================= #

st.markdown("<h1 style='text-align: center; font-size:60px; color: White'>Apontamento de produção</h1>", unsafe_allow_html=True)

with st.sidebar:
    image = Image.open('logo-cemagL.png')
    st.image(image, width=300)

def load_datas():

    scope = ['https://www.googleapis.com/auth/spreadsheets',
             "https://www.googleapis.com/auth/drive"]
    
    credentials = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
    client = gspread.authorize(credentials)
    sa = gspread.service_account('service_account.json')    

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
    
    #n_op = '22/12/2022'
    
    n_op = st.sidebar.selectbox('Selecione o código da ordem:', lista_unicos)
    
    return sh1, n_op, table1, table, lista_unicos

def consultar(n_op,table1,table):
        
    filter_ = table.loc[(table['DATA DA CARGA'] == n_op)]        
    
    filter_['qt. produzida'] = 0
            
    filter_ = filter_.reset_index(drop=True)

    if len(table1.loc[(table1['DATA DA CARGA'] == n_op)]) != 0:
        
        tab2 = table1.loc[(table1['DATA DA CARGA'] == n_op)]   
        tab2 = tab2.rename(columns={'QT PLAN.':'QT_ITENS'})
        
        filter_ = filter_.rename(columns={'DESCRICAO':'PEÇA'})
        filter_['QT PROD.'] = 0
        filter_['CAMBÃO'] = ''
        filter_ = filter_[['CODIGO', 'PEÇA', 'QT_ITENS', 'COR', 'QT PROD.','CAMBÃO', 'DATA DA CARGA']]
        
        df3 = pd.concat([filter_, tab2])
        df3 = df3.replace(np.nan, 0)
        
        qt_total = df3[['CODIGO','QT APONT.']].groupby(['CODIGO']).sum().reset_index()        

        df3 = df3.drop_duplicates(subset=['CODIGO'], keep='last')
        
        df3 = df3.drop(['QT PROD.', 'QT APONT.'], axis=1)
        table_geral = pd.merge(df3, qt_total, how = 'inner', on = 'CODIGO' )
        table_geral['QT. PRODUZIDA'] = 0
        table_geral = table_geral[['CODIGO', 'PEÇA', 'QT_ITENS','COR','QT. PRODUZIDA','QT APONT.', 'CAMBÃO']]
        
    else:
        
        table_geral = filter_[['CODIGO', 'DESCRICAO', 'QT_ITENS', 'COR', 'QT. PRODUZIDA']]
        table_geral['QT APONT.'] = 0
        table_geral['CAMBÃO'] = ''
    
    gb = GridOptionsBuilder.from_dataframe(table_geral)
    gb.configure_default_column(min_column_width=30)
    gb.configure_column('QT. PRODUZIDA', editable=True)
    gb.configure_column('CAMBÃO', editable=True)
    grid_options = gb.build()
    #grid_options['columnDefs'][0]['checkboxSelection']=True
    gb.configure_grid_options(pre_selected_rows=[])

    grid_response = AgGrid(table_geral,
                           gridOptions=grid_options,
                           height=400,
                           width='100%',
                           data_return_mode='AS_INPUT',
                           fit_columns_on_grid_load = True
                           )    
    filter_new = grid_response['data']    
    
    salvar = st.button("Salvar")
    filter_new['DATA DA CARGA'] = n_op
    
    if salvar:  
        
        filter_new = filter_new.replace({'QT. PRODUZIDA':{'':0}})
        filter_new = filter_new.drop(columns={'QT APONT.'})
        filter_new['QT. PRODUZIDA'] = filter_new['QT. PRODUZIDA'].astype(int)
        filter_new = filter_new.loc[(filter_new['QT. PRODUZIDA'] > 0)]
        filter_new = filter_new.values.tolist()
        sh1.values_append('geral', {'valueInputOption': 'RAW'}, {'values': filter_new})

    return filter_new

sh1, n_op, table1, table, lista_unicos = load_datas()

if n_op != '':
    consultar(n_op,table1,table)
