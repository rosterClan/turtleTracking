import numpy as np
import math
import filters as filter
from artifact import artifact

class scoreBoard:
    def __init__(self,title:artifact,characters:list[artifact],globalFrameSize) -> None:
        self.title = title
        self.characters = characters
        self.score = 0
        self.globalFrameSize = globalFrameSize

        self.charUnitSize = self.characters[0].returnFrame(0).shape
        self.titleUnitSize = self.title.returnFrame(0).shape

    def setScore(self,score):
        self.score = score

    def getFrame(self,frameNum:int):
        scoreChar = str(self.score)
        scoreCharLength = len(scoreChar)

        width = max(self.charUnitSize[1]*scoreCharLength,self.titleUnitSize[1])
        height = self.charUnitSize[0]*2

        canvas = np.zeros((height,width,self.charUnitSize[2]))
        canvas = filter.overlay(self.title.returnFrame(0),{'overlayPos':(0,0),'canvasPos':(0,0),'canvas':canvas})

        index = 0
        for num in scoreChar:
            scoreArtifact = self.characters[int(num)]
            canvas = filter.overlay(scoreArtifact.returnFrame(0),{'overlayPos':(0,0),'canvasPos':(math.floor(height/2),index),'canvas':canvas})
            index += self.charUnitSize[0]

        canvas = filter.resize(canvas,{'size':(canvas.shape[0]/3,canvas.shape[1]/3)})
        masterCanvas = np.zeros(self.globalFrameSize)
        
        masterCanvas = filter.overlay(canvas,{'overlayPos':None,'canvasPos':(100,150),'canvas':masterCanvas})
        masterCanvas = filter.performRotation(masterCanvas,{'degree':10})
        
        mask = filter.createMask(masterCanvas,{})
        masterCanvas = filter.applyMask(masterCanvas,{'mask':mask})

        return masterCanvas