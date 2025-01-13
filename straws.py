from artifact import artifact
import numpy as np
import filters as filter
import math

class straws:
    def __init__(self,straw,position,masterVideoSize,attack=5,floorLevel=260,health=1,gravity=25) -> None:
        self.attack = attack
        self.floorLevel = floorLevel
        self.position = list(position)
        self.videoSize = masterVideoSize
        self.health = 1
        self.gravity = gravity
        self.strawArtifact = straw
        self.boundingBox = None
        self.previousFrame = None

    def getFrame(self,frameNum):
        if (self.position[0] < self.floorLevel):
            self.position[0] += self.gravity
            if (self.position[0] + self.gravity > self.floorLevel) or (self.position[0] > self.floorLevel):
                self.position[0] = self.floorLevel

        canvas = np.zeros(self.videoSize)
        frame = self.strawArtifact.returnFrame(0)

        frame = filter.resize(frame,{'size':(40,40)})
        canvas = filter.overlay(frame,{'overlayPos':None,'canvasPos':(self.position),'canvas':canvas})

        self.boundingBox = filter.getBoundingBox(canvas,{})
        self.previousFrame = canvas

        return canvas
    
    def isDead(self):
        return self.health <= 0
    
    def getBoundingJson(self):
        return self.boundingBox
    
    def getAttack(self):
        return self.attack
    
    def enactCollision(self,damage):
        self.health -= damage

    def getCurrentImage(self):
        return self.previousFrame
