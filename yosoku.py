# 予測タソ beta

import numpy as np
import pandas as pd
import requests, bs4
import calcprob as p
from tqdm import tqdm
import os
#from datetime import datetime
from datetime import timedelta
#Configs
vmin = 0
vmax = 30
base_time= pd.to_datetime('00:00.0',format='%M:%S.%f')
url_head = 'https://keiba.rakuten.co.jp/race_card/list/RACEID/'
window = 50
#Field Id
Ohi = ['20150305','大井']
R = 12
F = 12 # Number of field
date = '20181116' #Race day 
#Convert
date_conv = pd.to_datetime(date,format='%Y/%m/%d')
date_th = date_conv - timedelta(days=90)
new_dir_path = './' + date
os.makedirs(new_dir_path, exist_ok=True)
Field = Ohi
#mean=np.zeros((12,20))
mean=-1*np.ones((12,20))
std=np.zeros((12,20))
prob =-1*np.ones((12,20))
for r in tqdm(range(R)):
    try:
        if r < 9:
            racenum ='0' + str(r+1)
        else:
            racenum = str(r+1)
        url0 = url_head + date + Field[0] + racenum
        res = requests.get(url0)
        res.raise_for_status()
        soup = bs4.BeautifulSoup(res.text, "html.parser")
        elems = soup.select('#raceInfomation li')
        # Get Each Info.
        place = elems[3].getText().rstrip("競馬")
        dist = elems[5].getText().rstrip("(外)")
        dist = dist.rstrip("(内)")
        dist = dist.replace(",", "").rstrip("m")
        #コース数値化
        flag=0
        if dist.find("ダ")!=-1:
            dist = dist.lstrip("ダ")
            flag=1
        elif dist.find("芝")!=-1:
            dist = dist.lstrip("芝")
        dist = int(dist)
        if dist >950:
            elems2 = soup.select('span[class="mainHorse"] a')
            H =len(elems2)#Number of hourse
            h=0
            for elem2 in elems2:
                url1=elem2.get('href')
                url2 = 'https:' + url1
                dfs = pd.read_html(url2)
                if len(dfs) != 2:
                    dfs2 = dfs[1][ ~(dfs[1]['タイム'].str.contains('-'))]
                    dfs2['日付'] = pd.to_datetime(dfs2['日付'],format='%Y/%m/%d')
                    #dfs2 = dfs2[(dfs2['日付'] > date_th) & (dfs2['日付'] < date)]
                    dfs2 = dfs2[(dfs2['日付'] < date)]
                    dfs2 = dfs2[(dfs2['競馬場'] == Field[1])]
                    if flag==1:
                        dfc2 = dfs2[( ~(dfs2['タイム'].str.contains('-')) & (dfs2['距離'].str.contains('ダ')) )]
                        dfc2['距離'] = dfc2['距離'].str.lstrip("ダ")
                    else:
                        dfc2 = dfs2[( ~(dfs2['タイム'].str.contains('-')) & (dfs2['距離'].str.contains('芝')) )]
                        dfc2['距離'] = dfc2['距離'].str.lstrip("芝")
                    if len(dfc2) > 0:
                        #コース数値化
                        dfc2['距離'] = dfc2['距離'].astype(np.int64)
                        #走行タイムへ処理
                        dfc2['タイム'][~(dfc2['タイム'].str.contains(':'))]='0:' + dfc2['タイム']
                        dfc2['タイム']= pd.to_datetime(dfc2['タイム'],format='%M:%S.%f') -base_time
                        dfc2['タイム'] = dfc2['タイム'].dt.total_seconds()
                        #dfc calc.
                        dfc = dfc2[(~(dfc2['競馬場'].str.contains('Ｊ')) & (dfc2['距離'] > 950) & (dfc2['距離'] < dist+ window) & (dfc2['距離'] > dist - window))]
                        speed = dfc['距離']/ dfc['タイム']
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
        Hai = 1
if np.any(prob!=-1)==1:
    df = pd.DataFrame(prob)
    df.index = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    df.columns = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
    df.to_excel(new_dir_path + '/' +date +  place + 'prob.xlsx', encoding='utf-8')