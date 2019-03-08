from array import array
from datetime import timedelta
import math

# Calculate using QregonDSP with:
#
#       EquirippleLowpass
#
#      N: 20 => 41 OmegaP: 0.45 Wp: 1 OmegsS: 0.5 Ws: 0.5
# http://www.seis.sc.edu/dragrace/www/firDesign/firDesign.html

class FIR:
    def __init__(self):
        self.filterTaps=array('d', [
-0.014214813709259033,
-0.02459816262125969,
0.029103312641382217,
-0.0030523138120770454,
-0.012606322765350342,
-0.008064772933721542,
0.016531193628907204,
0.011698857881128788,
-0.0176380705088377,
-0.017764931544661522,
0.019202090799808502,
0.025816356763243675,
-0.02051856741309166,
-0.03777090460062027,
0.02160944975912571,
0.05801019072532654,
-0.022438863292336464,
-0.10264670103788376,
0.02294692024588585,
0.3171583116054535,
0.4768567681312561,
0.3171583116054535,
0.02294692024588585,
-0.10264670103788376,
-0.022438863292336464,
0.058010198175907135,
0.02160945162177086,
-0.03777090460062027,
-0.020518574863672256,
0.025816360488533974,
0.01920209266245365,
-0.01776493340730667,
-0.01763806864619255,
0.01169885229319334,
0.016531191766262054,
-0.008064783178269863,
-0.012606322765350342,
-0.0030523203313350677,
0.02910330705344677,
-0.024598155170679092,
-0.014214811846613884])

        self.tapLen = len(self.filterTaps)
        self.history=array('d', [0]*self.tapLen)
        self.currIdx=0

    def calcUnitySum(self):
        acc = 0
        for i in range(self.tapLen):
            acc += self.filterTaps[i]
        return acc

    def calcDelay(self, sps):
        return timedelta(seconds=(self.tapLen-1)/2/sps)

    def pushPop(self, val, gain=1.0):
        """pushes a value onto the history stack and pops
        the next value processed by the FIR filter.
        """
        self.history[self.currIdx] = float(val)
        self.currIdx += 1
        if self.currIdx == self.tapLen:
            self.currIdx = 0
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
            p = self.FIR.pushPop(v)
            if self.tickTock:
                out.append(p)
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
