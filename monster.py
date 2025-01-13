import cv2
import filters as filter
from artifact import artifact
import numpy as np
import random
import copy
import math
import queue
from matplotlib import pyplot as plt
from healthbar import healthBar

import matplotlib.pyplot as plt

class monster:
    def __init__(self,body,leftWing,rightWing,position,cacheDir,screenSize) -> None:
        self.body:artifact = artifact('monsterBody',body,cacheDir,[])
        self.leftWing:artifact = artifact('monsterLeftWing',leftWing,cacheDir,[])
        self.rightWing:artifact = artifact('MonsterRightWing',rightWing,cacheDir,[])

        self.leftSidePositive = None
        self.rightSidePositive = None
        self.leftSideNegative = None
        self.rightSideNegative = None

        self.position = list(position)

        self.health = 10
        self.screenSize = screenSize
        self.boundingBox = None

        self.leftWingPos = (150,0)
        self.rightWingPos = (150,250)

        self.speeds = [-12,-11,-10,-9,-8,8,9,10,11,12]
        self.ouch = False

        self.healthBar = healthBar(self.health,self.health,(10,50,3))

        self.previousFrame = None
        self.generateVelocity()

    def setSpeed(self,speed):
        self.velocityX = speed[0]
        self.velocityY = speed[1]

    def getFrame(self,frameNum:int):
        self.position[0] += self.velocityX
        self.position[1] += self.velocityY

        monster = self.assembleCharacter(frameNum)

        emptyCanvas = np.zeros((self.screenSize[0],self.screenSize[1],3))
        emptyCanvas = filter.overlay(monster,{'overlayPos':(0,0),'canvasPos':(self.position[0],self.position[1]),'canvas':emptyCanvas})
        
        self.boundingBox = filter.getBoundingBox(emptyCanvas,{})
        #filter.drawBoundingBox(emptyCanvas,{'boundingBox':self.boundingBox})

        if (self.ouch):
            self.ouch = False
            emptyCanvas = filter.takeDamage(emptyCanvas,{})

        exitTop = self.boundingBox['pointOne'][0] < 0
        exitBottom = self.boundingBox['pointTwo'][0] < 0
        exitLeft = self.boundingBox['pointOne'][1] < 0
        exitRight = self.boundingBox['pointTwo'][1] < 0
        finalStatus = exitTop or exitBottom or exitLeft or exitRight

        if (finalStatus):
            self.health = 0

        self.previousFrame = emptyCanvas
        return emptyCanvas
    
    def getCurrentImage(self):
        return self.previousFrame
    
    def enactCollision(self,damage):
        self.generateVelocity()
        self.health -= damage
        self.healthBar.takeDamge(damage)
        self.ouch = True

    def generateVelocity(self):
        self.velocityX = self.speeds[random.randint(0,len(self.speeds)-1)]
        self.velocityY = self.speeds[random.randint(0,len(self.speeds)-1)]

    def getBoundingJson(self):
        return self.boundingBox

    def isDead(self):
        return self.health <= 0

    def assembleCharacter(self,frameNum:int):
        if (frameNum % 2) == 0:
            degree = 0
        else:
            degree = 40

        monsterEmptyCanvas = np.zeros((250,750,3))
        realitiveEmptyCanvasBodyCenterPos = (math.floor(monsterEmptyCanvas.shape[0]/2),math.floor(monsterEmptyCanvas.shape[1]/2))
        
        monsterEmptyCanvas = self.leftWing.returnFrame(0,False,[
            (filter.performRotation,{'degree':degree}),
            (filter.overlay,{'overlayPos':self.leftWingPos,'canvasPos':(150,90),'canvas':monsterEmptyCanvas})
        ])
        monsterEmptyCanvas = self.rightWing.returnFrame(0,False,[
            (filter.performRotation,{'degree':-degree}),
            (filter.overlay,{'overlayPos':self.rightWingPos,'canvasPos':(150,650),'canvas':monsterEmptyCanvas})
        ])
        monsterEmptyCanvas = self.body.returnFrame(0,False,[
            (filter.overlay,{'overlayPos':None,'canvasPos':(realitiveEmptyCanvasBodyCenterPos[0],realitiveEmptyCanvasBodyCenterPos[1]),'canvas':monsterEmptyCanvas})
        ])
        monsterEmptyCanvas = filter.resize(monsterEmptyCanvas,{'size':(100,40)})

        if (self.velocityY > 0):
            monsterEmptyCanvas = monsterEmptyCanvas[:, ::-1, :]

        monsterEmptyCanvas = self.healthBar.appendHealthBar(monsterEmptyCanvas)
        
        return monsterEmptyCanvas
    