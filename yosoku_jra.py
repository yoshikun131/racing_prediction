# 予測タソ beta

import numpy as np
import pandas as pd
import requests, bs4
import calcprob as p
from tqdm import tqdm
import os
import traceback
#from datetime import datetime
from datetime import timedelta
#Configs
vmin = 0
vmax = 30
base_time= pd.to_datetime('00:00.0',format='%M:%S.%f')
url_head = 'https://www.keibalab.jp/db/race/'
window = 50
#Field Id
Sapporo = ['01','札幌']
Hakodate = ['02','函館']
Fukushima = ['03','福島']
Niigata = ['04','新潟']
Tokyo  = ['05','東京']
Nakayama  = ['06','中山']
Cyukyo  = ['07','中京']
Kyoto  = ['08','京都']
Hannshinn  = ['09','阪神']
Kokura  = ['10','小倉']
R = 12
F = 10 # Number of field
date = '20181110' #Race day 
#Convert
date_conv = pd.to_datetime(date,format='%Y/%m/%d')
date_th = date_conv - timedelta(days=365)
new_dir_path = './' + date
os.makedirs(new_dir_path, exist_ok=True)
header = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"
        }
for f in tqdm(range(F)):
    #FieldName
    if f==0:
        Field = Sapporo
    elif f==1:
        Field = Hakodate
    elif f==2:
        Field = Fukushima
    elif f==3:
        Field = Niigata
    elif f==4:
        Field = Tokyo
    elif f==5:
        Field = Nakayama
    elif f==6:
        Field = Cyukyo
    elif f==7:
        Field = Kyoto
    elif f==8:
        Field = Hannshinn
    elif f==9:
        Field = Kokura
    
    #mean=np.zeros((12,20))
    mean=-1*np.ones((12,20))
    std=np.zeros((12,20))
    prob =-1*np.ones((12,20))
    for r in range(R):
        try:
            if r < 9:
                racenum ='0' + str(r+1)
            else:
                racenum = str(r+1)
            url0 = url_head + date + Field[0] + racenum + '/syutsuba.html'
            res = requests.get(url0)
            res.raise_for_status()
            soup = bs4.BeautifulSoup(res.text, "html.parser")
            elems = soup.select('ul[class="classCourseSyokin clearfix"] li')
            # Get Each Info.
            place = Field[1]#elems[3].getText().rstrip("競馬")
            dist = elems[1].getText()#.rstrip("(外)")
            dist = dist[0:5]
            #dist = dist.rstrip("(内)")
            dist = dist.rstrip("m")
            #コース数値化
            flag=0
            if dist.find("ダ")!=-1:
                dist = dist.lstrip("ダ")
                flag=1
            elif dist.find("芝")!=-1:
                dist = dist.lstrip("芝")
            dist = int(dist)
            if dist >950:
                elems2 = soup.select('td[class="tL "] a')
                H =len(elems2)#Number of hourse
                h=0
                for elem2 in elems2:
                    url1=elem2.get('href')
                    url2 = 'https://www.keibalab.jp' + url1
                    req = requests.get(url2, headers=header)
                    dfs = pd.read_html(req.text)
                    if len(dfs) != 2:
                        dfs2 = dfs[2][ ~(dfs[2]['騎手'].isnull())]
                        dfs2['年月日'] = pd.to_datetime(dfs2['年月日'],format='%Y/%m/%d')
                        #dfs2 = dfs2[(dfs2['年月日'] > date_th) & (dfs2['年月日'] < date)]
                        dfs2 = dfs2[(dfs2['年月日'] < date)]
                        #dfs2 = dfs2[(dfs2['場'].str.contains(Field[1]))]
                        
                        if flag==1:
                            dfc2 = dfs2[(dfs2['コース'].str.contains('ダ'))]
                            dfc2['コース'] = dfc2['コース'].str.lstrip("ダ")
                        else:
                            dfc2 = dfs2[(dfs2['コース'].str.contains('芝'))]
                            dfc2['コース'] = dfc2['コース'].str.lstrip("芝")
                        if len(dfc2) > 0:
                            #コース数値化
                            dfc2['コース'] = dfc2['コース'].astype(np.int64)
                            #走行タイムへ処理
                            #dfc2['タイム'][~(dfc2['タイム'].str.contains(':'))]='0:' + dfc2['タイム']
                            dfc2['タイム']= pd.to_datetime(dfc2['タイム'],format='%M:%S.%f') -base_time
                            dfc2['タイム'] = dfc2['タイム'].dt.total_seconds()
                            #dfc calc.
                            dfc = dfc2[((dfc2['コース'] > 950) & (dfc2['コース'] < dist+ window) & (dfc2['コース'] > dist - window))]
                            speed = dfc['コース']/ dfc['タイム']
                            speed[np.isnan(speed)] = 0.0
                            if len(speed) < 5:
                                mean[r][h] = speed.mean()
                                std[r][h] = speed.std()
                            else:
                                mean[r][h] = speed[0:5].mean()
                                std[r][h] = speed[0:5].std()
                    h+=1
                mean[np.isnan(mean)]=0.0
                std[np.isnan(std)]=0.1
                prob[r][0:H] = p.Calcprob(mean[r][0:H],std[r][0:H],H,vmin,vmax)
        except:
            print(traceback.format_exc())
    if np.any(prob!=-1)==1:
        df = pd.DataFrame(prob)
        df.index = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        df.columns = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
        df.to_excel(new_dir_path + '/' +date +  place + 'prob.xlsx', encoding='utf-8')