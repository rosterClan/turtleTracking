import cv2
import filters as filter
from artifact import artifact
import numpy as np
import random
import copy
import queue
import math
from straws import straws
from healthbar import healthBar
from matplotlib import pyplot as plt
import sys
import matplotlib.pyplot as plt

class character:
    def __init__(self,characterArtifact,body,leftArm,rightArm,leftLeg,rightLeg,cacheDir,floorLevel=285,health=100) -> None:
        self.characterArtifact:artifact = characterArtifact
        self.trackingPointsIsolated = artifact("redPoints",self.characterArtifact,cacheDir,        
                                  [
                                    (filter.isolateColorByDominent,{'color':2,'threashold':170,'differenceMargin':60}),
                                  ])
        
        self.body:artifact = body
        self.bodyMask: artifact = artifact('bodyMask',self.body.getVideoDir(),cacheDir,[(filter.createMask,{})])

        self.armAssets = {
            'leftArm':leftArm,
            'rightArm':rightArm,
            'leftLeg':leftLeg,
            'rightLeg':rightLeg
        }

        self.boundingBox = None
        self.previousFrame = None

        self.ouch = False
        self.stats = 0
        self.power = 2
        self.health = health

        self.healthBar = healthBar(self.health,self.health,(10,50,3))

        self.floorLevel = floorLevel
        self.previousBlobFrame = None
        self.keyBlobsCanvas = None
        self.previousAssociations = None
        self.originalCanvas = None
        sys.setrecursionlimit(10000)

    def getFrame(self,framenum):
        try:
            frame = cv2.convertScaleAbs(filter.createMask(self.trackingPointsIsolated.returnFrame(framenum, False), {}))
            self.originalCanvas = frame

            #filter.showImage(frame)

            kernel = np.ones((10, 10), np.uint8)
            frame = cv2.dilate(frame, kernel, iterations=1)
            kernel = np.ones((5, 5), np.uint8)
            frame = cv2.erode(frame, kernel, iterations=1)
            
            #filter.showImage(frame)

            workingFrame = np.copy(frame)
            height, width = workingFrame.shape[:2]
            mask = np.zeros((height + 2, width + 2), np.uint8)
            new_val = (255, 255, 255)
            _, workingFrame, _, _ = cv2.floodFill(workingFrame, mask, (0,0), new_val)
            workingFrame = cv2.bitwise_not(workingFrame)
            frame = cv2.add(frame, workingFrame)

            #filter.showImage(frame)

            self.keyBlobsCanvas = np.copy(frame)

            frame = self.applyRigging(frame)
            if (filter.isEmptyCanvas(frame,{})):
                raise Exception("Empty character frame error")
            self.boundingBox = filter.getBoundingBox(frame,{})
            self.previousFrame = frame
        except Exception as e:
            print(e)
            frame = self.previousFrame
        return frame

    def applyRigging(self,frame):
        emptyFrame = np.zeros(frame.shape)
        middle,limbs = self.associateBlobs(frame)
        
        for key, limb in limbs.items():
            if not limb == middle:
                ajustedPoints = filter.ajustPoints([middle['x'],middle['y']],[limb['x'],limb['y']])
                limb['x'] = ajustedPoints[0]
                limb['y'] = ajustedPoints[1]

                transformation = {
                    'newOrign':(limb['x'],limb['y']),
                    'newDest':(middle['x'],middle['y']),
                    'canvas':emptyFrame
                    }
                
                emptyFrame = self.armAssets[key].returnFrame(0,False,[(filter.transform,transformation)])
        
        pointOneLeft = min(limbs['leftLeg']['x'],limbs['rightLeg']['x'])
        
        if pointOneLeft == limbs['leftLeg']['x']:
            pointOne = limbs['leftLeg']
            pointTwo = limbs['rightLeg']
        else:
            pointOne = limbs['rightLeg']
            pointTwo = limbs['leftLeg']

        delta_y = pointTwo['y'] - pointOne['y']
        delta_x = pointTwo['x'] - pointOne['x']
        angle_radians = np.arctan2(delta_y, delta_x)
        angle_degrees = np.degrees(angle_radians)
        
        if delta_y > 0:
            angle_to_horizontal = -(angle_degrees - 90)
        else:
            angle_to_horizontal = -(angle_degrees + 90)

        midpoint = (math.floor((pointOne['y'] + pointTwo['y']) / 2),math.floor((pointOne['x'] + pointTwo['x']) / 2))
        emptyFrame = self.body.returnFrame(0,False,[
                (filter.applyMask,{'mask':self.bodyMask}),
                (filter.overlay,{'overlayPos':None,'canvasPos':(middle['x'],middle['y']),'canvas':emptyFrame})
            ]
        )

        emptyFrame = filter.overlay(self.healthBar.generateHelathBarFrame(),{'overlayPos':None,'canvasPos':(middle['x']-55,middle['y']),'canvas':emptyFrame})
        emptyFrame = filter.performRotation(emptyFrame,{'anchor':midpoint,'degree':angle_to_horizontal})
        emptyFrame = filter.moveYaxis(emptyFrame,midpoint,self.floorLevel)
        
        if (self.ouch):
            self.ouch = False
            emptyFrame = filter.takeDamage(emptyFrame,{})
        #filter.showImage(emptyFrame)
        return emptyFrame

    def associateBlobs(self,frame): 
        drawingBlobs = {}
        middleBlob,drawingBlobs = self.findBlobs(frame)

        associations = {
            'leftArm':None,
            'rightArm':None,
            'leftLeg':None,
            'rightLeg':None
        }

        for blob in drawingBlobs:
            if blob['x'] < middleBlob['x']:
                if (associations['leftArm'] == None):
                    associations['leftArm'] = blob
                elif (associations['leftArm']['y'] > blob['y']):
                    associations['rightArm'] = associations['leftArm']
                    associations['leftArm'] = blob
                elif (associations['rightArm'] == None):
                    associations['rightArm'] = blob
            elif (blob['x'] > middleBlob['x']):
                if (associations['leftLeg'] == None):
                    associations['leftLeg'] = blob
                elif (associations['leftLeg']['y'] > blob['y']):
                    associations['rightLeg'] = associations['leftLeg']
                    associations['leftLeg'] = blob
                elif (associations['rightLeg'] == None):
                    associations['rightLeg'] = blob

        for key,item in associations.items():
            if (item == None):
                if (key in ["rightLeg","leftLeg"]):
                    for subKey,subItem in associations.items():
                        if (subKey in ["rightLeg","leftLeg"]) and (not subItem == None):
                            height, width = self.keyBlobsCanvas.shape[:2]
                            mask = np.zeros((height + 2, width + 2), np.uint8)
                            _, self.keyBlobsCanvas, _, _ = cv2.floodFill(self.keyBlobsCanvas, np.zeros((height + 2, width + 2), np.uint8), (subItem['y'],subItem['x']), (0, 255, 0))
                            _, self.keyBlobsCanvas, _, _ = cv2.floodFill(self.keyBlobsCanvas, np.zeros((height + 2, width + 2), np.uint8), (0,0), (255, 255, 255))
                            self.keyBlobsCanvas = cv2.bitwise_not(self.keyBlobsCanvas)
                            _, self.keyBlobsCanvas, _, _ = cv2.floodFill(self.keyBlobsCanvas, np.zeros((height + 2, width + 2), np.uint8), (subItem['y'],subItem['x']), (255, 255, 255))

                    legPoints = self.guessLegs(self.keyBlobsCanvas)

                    if legPoints[0]['x'] < legPoints[1]['x']:
                        associations['leftLeg'] = legPoints[0]
                        associations['rightLeg'] = legPoints[1]
                    else:
                        associations['leftLeg'] = legPoints[1]
                        associations['rightLeg'] = legPoints[0]
                else:
                    raise Exception("Invalid Blobs")
                
        self.previousAssociations = associations
                
        return (middleBlob,associations)


    def findBlobs(self,frame):
        keyPoints = sorted(list(self.collectGroups(frame).values()), key=lambda x: x['len'], reverse=True)[:10]

        polygonCenterPoints = self.centerByPolygon(frame,keyPoints)
        genericCenterPoints = self.findSubsetAverage(keyPoints)

        genericCenterPointsAnalysed = 0
        polygonCenterPointsAnalysed = 0
        for point in keyPoints:
            if not (point == genericCenterPoints):
                genericCenterPointsAnalysed += filter.computeDistance((point['x'],point['y']),(genericCenterPoints['x'],genericCenterPoints['y']))
            if not (point['x'] == polygonCenterPoints['x'] and point['y'] == polygonCenterPoints['y']):
                polygonCenterPointsAnalysed += filter.computeDistance((point['x'],point['y']),(polygonCenterPoints['x'],polygonCenterPoints['y']))

        if genericCenterPointsAnalysed < polygonCenterPointsAnalysed:
            #filter.showImage(frame)
            #height, width = frame.shape[:2]
            #_,frame, _, _ = cv2.floodFill(frame, np.zeros((height + 2, width + 2), np.uint8), (genericCenterPoints['y'],genericCenterPoints['x']), (0, 0, 0))
            #filter.showImage(frame)
            keyPoints.remove(genericCenterPoints)
            return genericCenterPoints,keyPoints
        else:
            for point in keyPoints:
                if point['x'] == polygonCenterPoints['x'] and point['y'] == polygonCenterPoints['y']:
                    #filter.showImage(frame)
                    #height, width = frame.shape[:2]
                    #_,frame, _, _ = cv2.floodFill(frame, np.zeros((height + 2, width + 2), np.uint8), (polygonCenterPoints['y'],polygonCenterPoints['x']), (0, 0, 0))
                    #filter.showImage(frame)
                    keyPoints.remove(point)
                    break
            return polygonCenterPoints,keyPoints
    
    def guessLegs(self,frame):
        searchFrame = np.copy(frame)
        searchFrame = cv2.bitwise_and(searchFrame,self.originalCanvas)

        radius,pointOne = filter.find_largest_sphere(searchFrame)
        searchFrame = cv2.circle(searchFrame, pointOne, int(radius), (0, 255, 0), 2)
        height, width = searchFrame.shape[:2]
        _,searchFrame, _, _ = cv2.floodFill(searchFrame, np.zeros((height + 2, width + 2), np.uint8), pointOne, (0, 255, 0))
        _,searchFrame, _, _ = cv2.floodFill(searchFrame, np.zeros((height + 2, width + 2), np.uint8), pointOne, (0, 0, 0))
        #filter.showImage(searchFrame)

        radius,pointTwo = filter.find_largest_sphere(searchFrame)
        searchFrame = cv2.circle(searchFrame, pointTwo, int(radius), (0, 255, 0), 2)
        #filter.showImage(searchFrame)
        height, width = searchFrame.shape[:2]
        _,searchFrame, _, _ = cv2.floodFill(searchFrame, np.zeros((height + 2, width + 2), np.uint8), pointTwo, (0, 255, 0))
        _,searchFrame, _, _ = cv2.floodFill(searchFrame, np.zeros((height + 2, width + 2), np.uint8), pointTwo, (0, 0, 0))
        #filter.showImage(searchFrame)

        dist = filter.computeDistance(pointOne,pointTwo)
        if (dist < 30):
            pointOne = list(pointOne)
            pointTwo = list(pointTwo)

            differrence = 30 - dist
            difference = math.ceil(differrence/2)+7

            if (pointTwo[1] < pointOne[1]):
                temp = pointOne
                pointOne = pointTwo
                pointTwo = temp
            pointOne[1] -= difference
            pointTwo[1] += difference
        dist = filter.computeDistance(pointOne,pointTwo)

        print(filter.computeDistance(pointOne,pointTwo))

        return [{'x':pointOne[1],'y':pointOne[0]},{'x':pointTwo[1],'y':pointTwo[0]}]


    
    def collectGroups(self,frame):
        self.groups = {}
        keyPoints = {}
        self.groupNumber = 0

        for x in range(0,frame.shape[0]):
            for y in range(0,frame.shape[1]):
                if (not (filter.isEmpty(frame[x][y]))) and (not ((x,y) in self.groups)):
                    xValues,yValues = self.assignGroup(frame,x,y)
                    keyPoints[self.groupNumber] = {'len':len(xValues),'x':int(sum(xValues)/len(xValues)),'y':int(sum(yValues)/len(yValues))}
                    self.groupNumber += 1

        return keyPoints

    def assignGroup(self,frame,x,y):
        xValues = []
        yValues = []

        if (not (filter.isEmpty(frame[x][y]))) and (not ((x,y) in self.groups)):
            self.groups[(x,y)] = self.groupNumber
            xValues.append(x)
            yValues.append(y)
            for subX in range(x-1,x+2):
                for subY in range(y-1,y+2):
                    tempX,tempY = self.assignGroup(frame,subX,subY)
                    xValues.extend(tempX)
                    yValues.extend(tempY)

        return xValues,yValues
    
    def visualseColors(self,frame):
        colorDisc = {}
        for key, value in self.groups.items():
            if not value in colorDisc:
                colorDisc[value] = np.array([random.randint(1,255),random.randint(1,255),random.randint(1,255)])
            frame[key[0]][key[1]] = colorDisc[value]
        plt.imshow(frame, interpolation='nearest')
        plt.show()
    
    def collision(self,obj):
        objBounds:{} = obj.getBoundingJson()
        if (not objBounds == None) and (not self.boundingBox == None):
            bbox1_p1, bbox1_p2 = objBounds['pointOne'], objBounds['pointTwo']
            bbox2_p1, bbox2_p2 = self.boundingBox['pointOne'], self.boundingBox['pointTwo']

            x_overlap = (bbox1_p1[0] <= bbox2_p2[0]) and (bbox1_p2[0] >= bbox2_p1[0])
            y_overlap = (bbox1_p1[1] <= bbox2_p2[1]) and (bbox1_p2[1] >= bbox2_p1[1])

            potentialHit = x_overlap and y_overlap
            objFrame:np = obj.getCurrentImage()
            isFrame = type(objFrame) is np.ndarray

            if (potentialHit and (isFrame)):
                totalPixels = 0
                for x in range(objBounds['pointOne'][0],objBounds['pointTwo'][0]):
                    for y in range(objBounds['pointOne'][1],objBounds['pointTwo'][1]):
                        if not (filter.isEmpty(self.previousFrame[x][y])):
                            totalPixels += 1
                if (totalPixels > 200):
                    if (type(obj) is straws):
                        self.enactCollision(obj.getAttack())
                        self.ouch = True
                        obj.enactCollision(self.power)
                    else:
                        obj.enactCollision(self.power)
                        if (obj.isDead()):
                            self.stats += 1         
            else:
                return False
            
    def enactCollision(self,damage):
        self.health -= damage
        self.healthBar.takeDamge(damage)
            
    def getCharacterScore(self):
        return self.stats
    
    def isDead(self):
        return self.health <= 0
    
    def removeBlob(self,x,y,frame):
        workingFrame = np.copy(frame)
        height, width = workingFrame.shape[:2]
        mask = np.zeros((height + 2, width + 2), np.uint8)
        new_val = (0, 0, 0)
        _, workingFrame, _, _ = cv2.floodFill(workingFrame, mask, (x,y), new_val)
        
        return workingFrame
    
    ##### Finding centers #####
    def centerByPolygon(self,frame,keyPoints):
        drawingBlobs = []
        pointCanvas = np.zeros(frame.shape)

        for x in range(0,len(keyPoints)):
            pointCanvas[keyPoints[x]['x']][keyPoints[x]['y']] = np.array([255,255,255])
            drawingBlobs.append([keyPoints[x]['y'],keyPoints[x]['x']])

        canvas = np.zeros(frame.shape)

        for x in range(0,len(drawingBlobs)):
            tempPoints = list(drawingBlobs)
            tempPoints.pop(x)
            points = np.array([tempPoints], dtype=np.int32)
            canvas = cv2.fillPoly(canvas, points, (255, 255, 255))

        kernel = np.ones((5, 5), np.uint8)
        eroded_image = cv2.erode(canvas, kernel, iterations=1)
        middleIsolated = cv2.bitwise_and(eroded_image,pointCanvas)

        middlePoints = []
        for x in range(0,middleIsolated.shape[0]):
            for y in range(0,middleIsolated.shape[1]):
                if not filter.isEmpty(middleIsolated[x][y]):
                    middlePoints.append([x,y])

        sumX = 0
        sumY = 0
        for point in middlePoints:
            sumX += point[0]
            sumY += point[1]
        
        try:
            averageX = math.floor(sumX/len(middlePoints))
            averageY = math.floor(sumY/len(middlePoints))
        except:
            averageX = sys.maxsize
            averageY = sys.maxsize

        return {'x':averageX,'y':averageY}
    
    def findSubsetAverage(self,keyPoints):
        sumX = 0
        sumY = 0

        for point in keyPoints:
            sumX += point['x']
            sumY += point['y']

        averageX = math.floor(sumX/len(keyPoints))
        averageY = math.floor(sumY/len(keyPoints))

        total = averageX + averageY
        best = sys.maxsize
        bestPoint = None
        for point in keyPoints:
            subTotal = point['x'] + point['y']
            difference = max(total,subTotal)-min(total,subTotal)
            if (difference < best):
                best = difference
                bestPoint = point

        return bestPoint