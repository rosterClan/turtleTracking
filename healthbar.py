import numpy as np
import miscFunctions as mf
import filters as filter
import math

class healthBar:
    def __init__(self,totalHealth,currentHealth,size=(20,100,3),pixelBorder=2) -> None:
        self.totalHealth:int = totalHealth
        self.currentHealth:int = currentHealth
        self.size = size
        self.boarder = pixelBorder

    def takeDamge(self,damage:int):
        self.currentHealth -= damage

    def appendHealthBar(self,frame:np):
        healthBarCanvas = self.generateHelathBarFrame()

        newShape = list(frame.shape)
        newShape[0] += self.size[0]
        canvas = np.zeros(newShape)

        canvas = filter.overlay(frame,{'overlayPos':(0,0),'canvasPos':(self.size[0],0),'canvas':canvas})
        canvas = filter.overlay(healthBarCanvas,{'overlayPos':(0,0),'canvasPos':(0,math.floor(healthBarCanvas.shape[1]/2)),'canvas':canvas})
        #filter.showImage(canvas)

        return canvas
    
    def generateHelathBarFrame(self):
        healthBarCanvas = np.zeros(self.size)

        pixelWidth = self.size[1] - self.boarder
        percentageHealth = self.currentHealth/self.totalHealth
        fillIn = math.floor((pixelWidth*percentageHealth))

        healthBarCanvas = filter.fillColors(healthBarCanvas,{'pointOne':(0,0),'pointTwo':self.size,'color':np.array([140,140,140])})
        healthBarCanvas = filter.fillColors(healthBarCanvas,{'pointOne':(self.boarder-1,self.boarder-1),'pointTwo':(self.size[0]-self.boarder+1,pixelWidth+1),'color':np.array([40,40,40])})
        healthBarCanvas = filter.fillColors(healthBarCanvas,{'pointOne':(self.boarder,self.boarder),'pointTwo':(self.size[0]-self.boarder,fillIn),'color':np.array([88,88,255])})

        return healthBarCanvas


        