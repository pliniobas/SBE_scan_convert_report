# -*- coding: latin-1 -*-
"""
Created on Tue Apr 24 18:21:25 2018

@author: plinio.silva
"""
 
import pandas as pd
import os
import re
import datetime 
import numpy as np
import sys

try:
    from StringIO import StringIO #em python2
except:
    from io import StringIO #em python3

#%%
curdir = os.getcwd()
cnvs = []
for root, dirs, files in os.walk(".", topdown = False):
    name = [aux for aux in files if '.cnv' in aux]
    for aux in name:
        cnvs.append(os.path.join(root,aux))
        
filename = cnvs[2]
#%%
def cnv_2_csv(filename):
    #%%
    f = open(filename)
    data = f.read()
    f.close()
    
    #iniciando regular expression para achar o nome das colunas. Veja o help "re python" no google
    #repare que os dados retornados sao somente os que estao entre parenteses -->([\w ,.]+)
    temp = re.findall('name [\d]+ = [\w ,./-].+:([\w ,.]+)',data)
    
    #Retirando a data inicial de fundeio
    start_time = re.findall('start_time = (.*)(?= \[)',data)
    start_time = pd.to_datetime(start_time)


        
    
    
    #%%
    #dando uma formatada basica no nome das colunas, tirando as virgulas e os espacos.
    nome_colunas = [aux.replace(',','').strip(' ') for aux in temp] #
    
    #Achando o resto do arquivo depois do *END*, que eh o texto que servirah pra ser transformado em tabela
    #repare o uso do re.DOTALL. Ele faz com que o . de match em qualquer caractere, inclusive no \n (newline)
    texto_para_dataframe = re.findall('[\*END\*]{5}\n(.+)',data,re.DOTALL)
    
    

    # a variavel texto_para_dataframe eh uma lista, porque o re.findall retorna lista. 
    #tirar a unica string de dentro dela para usar no pd.read_csv que pede uma string ou um arquivo
    texto_para_dataframe = texto_para_dataframe[0]
    
    #Para passar esse texto para um dataframe, existem algumas possibilidades...
    #Usando o pd.read_csv(). O pd.read_csv() pede um arquivo. Eh possivel utilizar o StringIO para simular um arquivo
    
    

    f = StringIO(texto_para_dataframe) #f simula um arquivo, como se tivesse sido dado um f = open(filename)
    
    # o sep = '\s+' esta explicado no help do pandas.read_csv() , procurar no google.
    df = pd.read_csv(f,sep = '\s+',index_col = None, header = None )
    df.columns = nome_colunas #
#%%    
    
    # Segundo o site da seabird, essa eh a formula para passar de julianos da SBE para datetime.
    # d = datetime.date(dyear, 1, 1) + datetime.timedelta(yday-1)
    
    dyear = start_time.year[0]
    def sbe_julian_2_datetime(yday,dyear):
        d = datetime.datetime(dyear, 1, 1) + datetime.timedelta(yday-1)  
        return d
        
    try:

        #incluindo uma coluna datetime calculada com base no start_time
        df.index = df['Julian Days'].apply(lambda x:sbe_julian_2_datetime(x,dyear))
        pass
        
    except Exception as e:
        
        print(e)
        print("Nao foi encontrada coluna Julian Days na tabela ou nao foi possievl converter os dados para datetime")
        print("Arquivo %s"%filename)
        
    
    #Gravando o arquivo como csv
    df.to_csv(filename.replace('cnv','csv'),float_format = "%.4f",sep = ',')
    #%%
    return df
#%%
dfs = {}
dfname_back = ''

for filename in cnvs:
    pass
    dfname = filename.split('_')[1][-5:]
    dfname = re.findall("SBE[\d]*",filename)[0] + '_' + dfname
    if dfname == dfname_back:
        dfname = dfname + 'a' 
    print(dfname)
    df = cnv_2_csv(filename)
    dfs.update({dfname:df})
    dfname_back = dfname
    

#%%
# sbe = dfs['SBE37_20783']
# ctd = dfs['SBE19_07424']

def compare(sbe,ctd):
    pass
    
    sbe = sbe[np.logical_and(sbe.index > ctd.index[0],sbe.index < ctd.index[-1])] #split dados pela data CTD
    sbeDepthMean = sbe.Depth.mean() #Profundidade do SBE durante o CTD
    
    dic = dict()
    
    #Acha o indice, na df ctd, do valor mais proximo entre a prof do SBE e CTD
    idx1 = np.abs(ctd.Depth - sbeDepthMean).argmin() 
    dic['ctd_cond'] = ctd.Conductivity.iloc[idx1] #valor da condutividade do CTD na prof mais proxima
    dic['ctd_tem'] = ctd.Temperature.iloc[idx1] 
    dic['ctd_depth'] = ctd.Depth.iloc[idx1]
    temp = ctd[ctd.Conductivity == dic['ctd_cond']] #indice de quando o CTD esteve na mesma prof do SBE
    dic['ctd_date'] = temp.index[0]
    
    def nearest(items, pivot):
        return min(items, key=lambda x: abs(x - pivot))
    try:
        idx2 = nearest(sbe.index,dic['ctd_date'])
        dic['sbe_cond'] = sbe.Conductivity[idx2]
        dic['sbe_tem'] = sbe.Temperature[idx2]
        dic['sbe_depth'] = sbe.Depth[idx2]
        dic['sbe_date'] = idx2
        
        temp = datetime.datetime.today().strftime("%Y-%m-%d %Hh%Mm%Ss")
        f = open('./SBE_scan_report %s.txt'%temp,'a')
        for aux in dic:
            print(aux,dic[aux])   
            f.write(aux)
            f.write('=')
            f.write(str(dic[aux]))
            f.write('\n')
        f.close()
                
        
    except Exception as e:
        print(e)
        print("Datas nao coincidem")

sbekeys = [aux for aux in dfs.keys() if "SBE37" in aux]
ctdkeys = [aux for aux in dfs.keys() if "SBE19" in aux]

for c in ctdkeys:
    for s in sbekeys:
        print("compare %s com %s"%(c,s))
        compare(dfs[s],dfs[c])
        print('----------------------------------------')
        
        
        

