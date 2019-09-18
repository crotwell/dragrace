# Writing a test case

import unittest
from math import *




from peakACC import *




class TestVmag(unittest.TestCase):
    #
    # def test_upper(self):
    #     self.assertEqual('foo'.upper(), 'FOO')
    #
    # def test_isupper(self):
    #     self.assertTrue('FOO'.isupper())
    #     self.assertFalse('Foo'.isupper())
#Magnitude_ThreeC_TimeSeries_jake
    def test_maxacc(self):
        maxComp = 1
        x = [0,0,maxComp,0]
        y = [0,0,maxComp,0]
        z = [0+4096,0+4096,maxComp+4096,0+4096]
        theta = 0  #90 maxacc = sqrt(2)
        alpha = 0
        station = "FL"
        start_time = 12
        end_time = 13
        ans = peakAccelerationCalculation(x,y,z,theta,alpha,station,start_time,end_time)

        #print(f"maxacc {ans['maxacc']} sqrt {sqrt(3*maxComp)/4096})
        self.assertEqual(ans['maxacc'], sqrt(3*maxComp)/4096) #test .maxacc is equal to ...
        self.assertEqual(ans['station'], station) #test .maxacc is equal to ...
        self.assertEqual(ans['maxVmag'], sqrt(3*maxComp))

    def test_3C(self):
        maxComp = 1.0
        x = [0,0,maxComp]
        y = [0,0,maxComp]
        z = [0,0,maxComp]

        ans = Magnitude_ThreeC_TimeSeries_jake(x,y,z)

        self.assertEqual(ans[0],0)
        self.assertEqual(ans[1],0)
        self.assertEqual(ans[2],sqrt(3*maxComp)) #checks out
        self.assertEqual(max(x),maxComp)



    #
    # def test_station(self):
    #     k = peakAccelerationCalculation.station()
    #     self.assertEqual(k,'FL')
    #
    # def test_start_time(self):
    #     k = peakAccelerationCalculation.start_time()
    #     self.assertEqual(k,12)
    #
    # def test_end_time(self):
    #     k = peakAccelerationCalculation.end_time()
    #     self.assertEqual(k,13)
    #
    # def test_maxVmag(self):
    #     k = peakAccelerationCalculation.maxVmag()
    #     self.assertEqual(k,sqrt(3)/4096)
    #
    # def test_maxIndex(self):
    #     k = peakAccelerationCalculation.maxIndex()
    #     self.assertEqual(k,2)
    #
    # def test_maxIndex(self):
    #     k = peakAccelerationCalculation.vmagPair()
    #     self.assertEqual(k,(2,sqrt(3)/4096))
    #     # check that s.split fails when the separator is not a string
    #     # with self.assertRaises(TypeError):
    #     #     s.split(2)

if __name__ == '__main__':
    unittest.main()
