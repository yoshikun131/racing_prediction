#!/usr/bin/env python3
# -*- coding: utf-8 -*-
## Class: calc. winning probability of each hourse 
import numpy as np
from scipy.stats import norm
eps = 1.0
class  Calcprob:
    def __new__(self,mean,std,H,vmin,vmax):
        mean *= 10
        std *= 10
        vmin *=10
        vmax *=10
        ## Define Common info.
        prob=np.zeros(H)
        for h in range(H):
            for t in range(vmin,vmax,1):
                K=1.0
                for h2 in range(H):
                    if h2 != h:
                        if std[h2] > 0.0:
                            K*=norm.cdf(x=t, loc=mean[h2], scale=std[h2])
                if std[h] > 0.0:
                    prob[h]+=K*norm.pdf(x=t, loc=mean[h], scale=std[h])
        return prob