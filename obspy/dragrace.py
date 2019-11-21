#!/Users/crotwell/opt/miniconda3/envs/obspy/bin/python

import numpy as np
import obspy
import math
import requests
from requests import HTTPError

baseUrlPattern = 'http://www.seis.sc.edu/dragdata/{race}/{datatype}/XX/{sta}/{year}/{dofy}/XX.{sta}.00.{chan}.{year}.{dofy}.{hour}'
resultsPattern = 'http://www.seis.sc.edu/dragdata/{race}/results/allResults.json'

AllChanList = ['HNZ', 'HNY', 'HNX']
FALL2019 = {
  'name': 'Fall2019',
  'starttime': obspy.UTCDateTime('2019-284T00:00:00Z'),
  'endtime': obspy.UTCDateTime('2019-288T00:00:00Z'),
  'staList': ['NR', 'FL', 'FL0', 'FL4G', 'FL60', 'FL330', 'FL660', 'FL1K'],
  'chanList': AllChanList
}
SPRING2019 = {
  'name': 'Spring2019',
  'starttime': obspy.UTCDateTime('2019-115T00:00:00Z'),
  'endtime': obspy.UTCDateTime('2019-119T00:00:00Z'),
  'staList': ['FR', 'NR', 'NL', 'FL'],
  'chanList': AllChanList
}

def getRace(start, duration):
    start = obspy.UTCDateTime(start)
    end = obspy.UTCDateTime(start) + duration
    race = None
    if end > SPRING2019['starttime'] and start < SPRING2019['endtime']:
        race = SPRING2019
    elif end > FALL2019['starttime'] and start < FALL2019['endtime']:
        race = FALL2019
    else:
        raise Error("Can't figure out which race for dates {} - {}".format(start, end))
    return race

def getMseed(start, duration, staList=None, chanList=None):
    return getDataAsMseed('mseed', start, duration, staList=staList, chanList=chanList)

def getMinMax(start, duration, staList=None, chanList=None):
    if chanList is None:
        chanList = ['HNM']
    return getDataAsMseed('minmax', start, duration, staList=staList, chanList=chanList)

def getDataAsMseed(datatype, start, duration, staList=None, chanList=None):
    start = obspy.UTCDateTime(start)
    end = obspy.UTCDateTime(start) + duration
    race = getRace(start, duration)
    print('getDragrace {} {}  {}'.format(race['name'], start, end))
    if staList is None:
        staList = race['staList']
    if chanList is None:
        chanList = race['chanList']
    outStream = None
    for s in staList:
        print("station: {}".format(s))
        for c in chanList:
            print("channel: {}".format(c))
            chanStream = None
            hourStart = obspy.UTCDateTime(start)
            while hourStart < end:
                mseedUrl = baseUrlPattern.format(datatype=datatype, race=race['name'], sta=s, chan=c, year=hourStart.year, dofy=hourStart.julday, hour=hourStart.hour)
                print(mseedUrl)
                try:
                    hourStream = obspy.read(mseedUrl)
                    if hourStream:
#                        hourStream = mergeAtBigGaps(hourStream)
                        hourStream.merge()
                        hourStream = hourStream.trim(start, end)
                        fixMaskedArrayIssue(hourStream)
                        if chanStream:
                            chanStream = chanStream + hourStream
                        else:
                            chanStream = hourStream
                    if chanStream:
                        if outStream:
                            outStream += chanStream
                        else:
                            outStream = chanStream
                except HTTPError as err:
                    print("not found, skipping {}".format(mseedUrl))
                hourStart = hourStart + 3600
    return outStream

def mergeAtBigGaps(st, minGapPercent=1.5):
    # sort
    st.sort(['starttime'])
    allSegs = []
    prev = None
    continSeg = []
    for seg in st:
        if prev is not None:
            sampRate = prev.stats.sampling_rate
            gap = (seg.stats.starttime - prev.stats.endtime)
            if gap * sampRate > minGapPercent:
                allSegs.append(continSeg)
                continSeg = [ seg ]
            else:
                continSeg.append(seg)
        prev = seg
    allSegs.append(continSeg)
    out = obspy.Stream()
    for segList in allSegs:
        contSeg = obspy.Stream(traces=segList)
        mergeViaSampleRate(contSeg)
        out+= contSeg
    return out

def mergeViaSampleRate(st):
    # sort
    st.sort(['starttime'])
    # start time in plot equals 0
    dt = st[0].stats.starttime.timestamp
    et = st[len(st)-1].stats.starttime.timestamp
    npts = 0
    for seg in st:
        npts += seg.stats.npts
    npts -= st[len(st)-1].stats.npts
    roundingSize = 1000
    sampRate = math.floor(roundingSize * npts / (et-dt))/roundingSize
    print("sample rate: {}  npts: {}  time: {}".format(sampRate, npts, (et-dt)))
    for seg in st:
        seg.stats.sampling_rate = sampRate

    # Merge the data together and show plot in a similar way
    st.merge(method=1)
    fixMaskedArrayIssue(st)
    return st

def fixMaskedArrayIssue(st):
    for tr in st:
        if isinstance(tr.data, np.ma.masked_array):
            tr.data = tr.data.filled(fill_value=np.int16(np.mean(tr.data)))
    return st


def getResults(start, duration, racename=None):
    start = obspy.UTCDateTime(start)
    end = obspy.UTCDateTime(start) + duration
    racename = getRace(start, duration)
    req = requests.get(resultsPattern.format(racename))
    allResults = req.json()
    out = []
    for r in allResults:
        r.startTime = obspy.UTCDateTime(r.startTime)
        r.time = obspy.UTCDateTime(r.time)
        r.endTime = obspy.UTCDateTime(r.endTime)
        if r.startTime < end and r.endTime > start:
            out.append(r)
    return out
