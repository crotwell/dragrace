from array import array
from datetime import timedelta
import math

# Calculate using QregonDSP with:
#
#       EquirippleLowpass
#
#      N: 40 => 81 OmegaP: 0.45 Wp: 1 OmegsS: 0.5 Ws: 1
# http://www.seis.sc.edu/dragrace/www/firDesign/firDesign.html

class FIR:
    def __init__(self):
        self.filterTaps=array('d', [
            -0.0002095501549774781,
            0.005981106776744127,
            0.000511004647705704,
            -0.0025987043045461178,
            -0.0009158515022136271,
            0.003023756667971611,
            0.001635189400985837,
            -0.0033725600223988295,
            -0.002546686679124832,
            0.0036034397780895233,
            0.003657830413430929,
            -0.0036607440561056137,
            -0.004963773302733898,
            0.00348414434120059,
            0.006453620735555887,
            -0.00300728902220726,
            -0.00810567382723093,
            0.002157387090846896,
            0.009891565889120102,
            -0.0008516339585185051,
            -0.011775528080761433,
            -0.0010035234736278653,
            0.013711502775549889,
            0.003526905318722129,
            -0.015649188309907913,
            -0.006877588108181953,
            0.0175322275608778,
            0.011299733072519302,
            -0.019307520240545273,
            -0.01720271073281765,
            0.020923787727952003,
            0.025351202115416527,
            -0.022322865203022957,
            -0.03741733729839325,
            0.02346331998705864,
            0.057759419083595276,
            -0.02430727332830429,
            -0.10250212252140045,
            0.024824345484375954,
            0.31709831953048706,
            0.47499901056289673,
            0.31709831953048706,
            0.024824347347021103,
            -0.10250212252140045,
            -0.02430727332830429,
            0.057759419083595276,
            0.02346331812441349,
            -0.03741733729839325,
            -0.022322868928313255,
            0.025351211428642273,
            0.020923787727952003,
            -0.01720271445810795,
            -0.019307520240545273,
            0.011299723759293556,
            0.01753222942352295,
            -0.006877586245536804,
            -0.01564919576048851,
            0.0035269169602543116,
            0.013711502775549889,
            -0.001003523706458509,
            -0.011775528080761433,
            -0.0008516290690749884,
            0.009891564957797527,
            0.002157393144443631,
            -0.008105669170618057,
            -0.0030072841327637434,
            0.006453621666878462,
            0.003484148997813463,
            -0.004963770508766174,
            -0.0036607428919523954,
            0.0036578297149389982,
            0.0036034274380654097,
            -0.002546686679124832,
            -0.0033725686371326447,
            0.0016351882368326187,
            0.0030237510800361633,
            -0.0009158484172075987,
            -0.0025987059343606234,
            0.0005110036581754684,
            0.005981103051453829,
            -0.00020955075160600245])

        self.tapLen = len(self.filterTaps)
        self.history=None
        self.currIdx=0

    def calcUnitySum(self):
        acc = 0
        for i in range(self.tapLen):
            acc += self.filterTaps[i]
        return acc

    def calcDelay(self, sps):
        return timedelta(seconds=(self.tapLen-1)/2/sps)

    def push(self, val):
        """pushes a value onto the history stack but does
           not calc output value. Useful when decimating
           for values that will be tossed anyway
        """
        # first time through init history to all be the first value
        # this helps when the input signal has a DC offset as initialize
        # to zero gives a spike in values until the filter charges
        if self.history is None:
            self.history=array('d', [val]*self.tapLen)
        self.history[self.currIdx] = float(val)
        self.currIdx += 1
        if self.currIdx == self.tapLen:
            self.currIdx = 0

    def pushPop(self, val, gain=1.0):
        """pushes a value onto the history stack and pops
        the next value processed by the FIR filter.
        """
        self.push(val)
        acc = 0.0
        idx = self.currIdx
        for i in range(self.tapLen):
            idx = self.tapLen-1 if idx == 0 else idx-1
            acc += self.history[idx] * self.filterTaps[i]
        return int(round(acc*gain))


class DecimateTwo:
    def __init__(self):
        self.FIR = FIR()
        self.tickTock = True

    def process(self, dataArray):
        out = []
        for v in dataArray:
            if self.tickTock:
                # keep this output
                out.append(self.FIR.pushPop(v))
            else:
                # toss this output
                self.FIR.push(v)
            self.tickTock = not self.tickTock
        return out

if __name__ == "__main__":
    # execute only if run as a script
    fir = FIR()
    d2 = DecimateTwo()
    outData = []
    inData = []
    gain = 1.0+(1.0-fir.calcUnitySum())
    gain=1.0
    for i in range(400):
        val = int(round(10000*math.sin(2*math.pi*i/20)))
        inData.append(val)
        outData.append(fir.pushPop(val, gain))
    delay = int((fir.tapLen-1)/2)
    for i in range(len(outData)-delay):
        print(" {:d}  push: {:d}   pop: {:d}".format(i, inData[i], outData[i+delay]))

    print("delay: {}".format(delay))
    print("unity sum: {}".format(fir.calcUnitySum()))
