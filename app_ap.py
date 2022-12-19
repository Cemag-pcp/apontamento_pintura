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

st.markdown("<h1 style='text-align: center; font-size:60px; color: Black'>Apontamento de produção</h1>", unsafe_allow_html=True)

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
    
    #lista_unicos = table[['DATA DA CARGA']].drop_duplicates()[1:]
    
    name_sheet1 = 'Base ordens de produçao finalizada'
    worksheet1 = 'geral'
    sh1 = sa.open(name_sheet1)
    wks1 = sh1.worksheet(worksheet1)
    list2 = wks1.get_all_records()
    table1 = pd.DataFrame(list2)
    
    #n_op = '23/12/2022'
    
    #n_op = st.sidebar.selectbox('Selecione o código da ordem:', lista_unicos)
    
    return sh1, n_op, table1, table#, lista_unicos

def consultar(n_op,table1,table):
        
    filter_ = table.loc[(table['DATA DA CARGA'] == n_op)]        
    
    filter_['QT. PRODUZIDA'] = 0
            
    filter_ = filter_.reset_index(drop=True)

    if len(table1.loc[(table1['DATA DA CARGA'] == n_op)]) != 0:
        
        tab2 = table1.loc[(table1['DATA DA CARGA'] == n_op)]   
        tab2 = tab2.rename(columns={'QT PLAN.':'QT_ITENS'})
        
        filter_ = filter_.rename(columns={'DESCRICAO':'PEÇA'})
        filter_['QT. PRODUZIDA'] = 0
        filter_ = filter_[['CODIGO', 'PEÇA', 'QT_ITENS', 'COR', 'QT. PRODUZIDA', 'DATA DA CARGA']]

        df3 = tab2[['CODIGO','CAMBÃO']]        
        df3 = (df3[df3['CAMBÃO'] != ''])
        df3 = pd.merge(filter_,df3, on=['CODIGO'], how='left').drop_duplicates(subset=['CODIGO'])
                
        qt_total = tab2[['CODIGO','QT APONT.']].groupby(['CODIGO']).sum().reset_index()        
        qt_total.drop(qt_total[qt_total['QT APONT.'] == 0].index, inplace=True)
        
        df3 = pd.merge(df3, qt_total, on=['CODIGO'], how='left')
        
        df3 = df3.replace(np.nan,0)
            
        #df3 = df3.drop(['QT. PRODUZIDA', 'QT APONT.'], axis=1)
        #table_geral = pd.merge(df3, qt_total, how = 'inner', on = 'CODIGO' )
        #table_geral['QT. PRODUZIDA'] = 0
        table_geral = df3
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

    grid_response = AgGrid(table_geral,
                           gridOptions=grid_options,
                           height=400,
                           width='100%',
                           data_return_mode='AS_INPUT',
                           update_mode='MANUAL',
                           try_to_convert_back_to_original_types = False,
                           fit_columns_on_grid_load = True,
                           theme='streamlit',
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

with st.sidebar:

    with st.form("my_form"):
        
        n_op = st.date_input('Selecione a data da carga')
        n_op = n_op.strftime('%d/%m/%Y')
        columns = st.columns((2, 1, 2))
        button_pressed = columns[1].form_submit_button('Ok')

if n_op != '':
    sh1, n_op, table1, table = load_datas()
    consultar(n_op,table1,table)
