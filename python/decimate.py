from array import array
from datetime import timedelta

# modified from http://t-filter.engineerjs.com/
/*

FIR filter designed with
 http://t-filter.appspot.com

sampling frequency: 800 Hz

* 0 Hz - 180 Hz
  gain = 1
  desired ripple = 5 dB
  actual ripple = 4.073676780356335 dB

* 200 Hz - 400 Hz
  gain = 0
  desired attenuation = -40 dB
  actual attenuation = -40.20750266764615 dB

*/

class FIR:
    def __init__(self):
        self.filterTaps=array('d', [
          0.018417300875864944,
          0.02436769267167705,
          -0.0014977285615569997,
          -0.04575041840008282,
          -0.05821920587884289,
          -0.022347048206624358,
          0.011722092825865237,
          -0.0020910915383823407,
          -0.03181736475168622,
          -0.017767345679765484,
          0.023204676384514258,
          0.018891324688008106,
          -0.03004571907712454,
          -0.03492579962638612,
          0.029329838295632498,
          0.05431529870189004,
          -0.03197270376243652,
          -0.10097573477697484,
          0.0322339057932065,
          0.31626869164196386,
          0.46702488937212033,
          0.31626869164196386,
          0.0322339057932065,
          -0.10097573477697484,
          -0.03197270376243652,
          0.05431529870189004,
          0.029329838295632498,
          -0.03492579962638612,
          -0.03004571907712454,
          0.018891324688008106,
          0.023204676384514258,
          -0.017767345679765484,
          -0.03181736475168622,
          -0.0020910915383823407,
          0.011722092825865237,
          -0.022347048206624358,
          -0.05821920587884289,
          -0.04575041840008282,
          -0.0014977285615569997,
          0.02436769267167705,
          0.018417300875864944
        ])

        self.tapLen = len(self.filterTaps)
        self.history=array('d', [0]*self.tapLen)
        self.currIdx=0

    def calcDelay(self, sps):
        return timedelta(seconds=self.tapLen/2/sps)

    def pushPop(self, val):
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
        return int(round(acc))

#
# void SampleFilter_init(SampleFilter* f) {
#   int i;
#   for(i = 0; i < SAMPLEFILTER_TAP_NUM; ++i)
#     f->history[i] = 0;
#   f->last_index = 0;
# }
#
# void SampleFilter_put(SampleFilter* f, double input) {
#   f->history[f->last_index++] = input;
#   if(f->last_index == SAMPLEFILTER_TAP_NUM)
#     f->last_index = 0;
# }
#
# double SampleFilter_get(SampleFilter* f) {
#   double acc = 0;
#   int index = f->last_index, i;
#   for(i = 0; i < SAMPLEFILTER_TAP_NUM; ++i) {
#     index = index != 0 ? index-1 : SAMPLEFILTER_TAP_NUM-1;
#     acc += f->history[index] * filter_taps[i];
#   };
#   return acc;
# }
