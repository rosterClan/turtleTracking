import numpy as np
import collections

class averageTracker:
    def __init__(self,size) -> None:
        self.red = 0
        self.green = 0
        self.blue = 0
        self.count = 0
        self.size = size

        self.output = []

        self.queue = collections.deque()

    def addPixels(self,pixel:np):
        self.red += pixel[2]
        self.green += pixel[1]
        self.blue += pixel[0]
        self.count += 1
        self.queue.append(pixel)

        if self.count > self.size:
            removePixel = self.queue.popleft()
            self.red -= removePixel[2]
            self.green -= removePixel[1]
            self.blue -= removePixel[0]
            self.count -= 1

    def getOutput(self):
        return self.output

    def getAverage(self):
        if self.count >= self.size:
            self.output = np.array([min(int(self.blue/self.count),255),min(int(self.green/self.count),255),min(int(self.red/self.count),255)])
            return True
        else:
            return False