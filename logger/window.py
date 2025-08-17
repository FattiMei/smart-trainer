import unittest
import numpy as np


class SlidingWindow:
    def __init__(self, seconds: float):
        self.start_time = None
        self.seconds = seconds

        # e potrebbe anche essere una struttura dati
        # più specializzata
        self.timeq = []
        self.dataq = []

    def push(self, timestamp: float, data):
        if self.start_time is None:
            self.start_time = timestamp

        self.timeq.append(timestamp)
        self.dataq.append(data)

        if len(self.timeq) > 2:
            if timestamp-self.timeq[1] >= self.seconds:
                self.timeq.pop(0)
                self.dataq.pop(0)

        assert(len(self.timeq) == len(self.dataq))

    def clear(self):
        self.start_time = None
        self.timeq.clear()
        self.dataq.clear()

        assert(self.timeq == [])
        assert(self.dataq == [])
        assert(self.start_time == None)


class TestSlidingWindow(unittest.TestCase):
    def test_push_from_empty(self):
        win = SlidingWindow(3.0)
        win.push(0, 1)

        self.assertTrue(win.timeq == [0])
        self.assertTrue(win.dataq == [1])

    def test_push_many_things(self):
        win = SlidingWindow(3.0)

        NSAMPLES = 20
        for t in np.linspace(0,1,num=NSAMPLES):
            win.push(t, 0)

        self.assertTrue(len(win.timeq) == NSAMPLES)


if __name__ == '__main__':
    unittest.main()
