#!/usr/bin/env python3

import serveobspy
import obspy
import dragrace


serveSeis = serveobspy.ServeObsPy('www')
serveSeis.serveData()

start = '2019-04-26T14:10:00'
start = '2019-10-12T14:10:00'
#st = dragrace.getMseed(start, 300, staList=['FL', 'NL'])
st = dragrace.getMseed(start, 300, staList=['FL'], chanList=['HNZ'])

serveSeis.stream=st
serveSeis.title="Hi Dragracers"


filt = obspy.Stream()
for tr in st:
  ftr = tr.copy()
  ftr.detrend()
  ftr.filter('highpass', freq=50)
  filt.append(ftr)

serveSeis.stream=filt
