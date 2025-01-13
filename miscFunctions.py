import numpy as np
import cv2
import math
from statistics import mean
import sys
import os

def writeFramesFromVideo(extractDir,videoDir):
    frameNum = 0
    video = cv2.VideoCapture(videoDir)
    while True:
        ret,frame = video.read()
        if not ret:
            break
        cv2.imwrite(extractDir+"/frame"+str(frameNum)+".jpg",frame)
        frameNum = frameNum + 1
    video.release()
    return frameNum

def writeSingleFrame(dir,frame,num=0):
    try:
        cv2.imwrite(dir+"/frame"+str(num)+".jpg",frame)
    except Exception as e:
        print(e)

def readFrames(baseDirectory,frameNum):
    videoDirectory = baseDirectory + "/frame"+str(frameNum)+".jpg"
    if (os.path.isfile(videoDirectory)):
        image = cv2.imread(videoDirectory)
        return np.array(image)
    else:
        raise Exception("File doesn't exist")

def calculate_ssd(arr1, arr2):
    return np.sum((arr1 - arr2) ** 2)

def segmentFrame(videoFrame,step=5):
    segmentedFrames = []
    numRows = videoFrame.shape[0]
    numCols = videoFrame.shape[1]

    for x in range(0,numRows,step):

        blockRow = []
        for y in range(0,numCols,step):
            row = []
            for xRow in range(x,x+step):
                column = []
                for yCol in range(y,y+step):
                    try:
                        column.append(videoFrame[xRow][yCol])
                    except:
                        column.append(np.array([0,0,0]))
                row.append(np.array(column))
            blockRow.append(np.array(row))

        segmentedFrames.append(np.array(blockRow))
    return np.array(segmentedFrames)

def unsegmentFrame(videoFrame,blockSize,shapeX,shapeY):
    unsegmentedFrame = []

    for x in range(0,shapeX):
        row = []
        for y in range(0,shapeY):
            try:
                blockX = int((x/blockSize)//1)
                blockY = int((y/blockSize)//1)

                innerBlockX = x-(blockSize*math.floor(x/blockSize))
                innerBlockY = y-(blockSize*math.floor(y/blockSize))

                pixel = videoFrame[blockX][blockY][innerBlockX][innerBlockY]

                row.append(pixel)
            except:
                continue
        row = np.array(row)
        if row.shape[0] > 0:
            unsegmentedFrame.append(np.array(row))
    
    return np.array(unsegmentedFrame)

def sliceNeighbours(frame,width,xIndx,yIndx):
    neighbours = []
    dimension = math.ceil(width/2)
    for x in range(xIndx-dimension,xIndx+dimension+1):
        row = []
        for y in range(yIndx-dimension,yIndx+dimension+1):

            if (x < 0 or y < 0 or x > frame.shape[0]-1 or y > frame.shape[1]-1):
                row.append(np.array([None]))
            else:
                row.append(frame[x][y])

        neighbours.append((row))
    return (neighbours)

def searchElement(element,neighbours,width):
    bestX = 0 
    bestY = 0
    bestScore = sys.maxsize
    width = math.ceil(width/2)

    for x in range(0,len(neighbours)):
        for y in range(0,len(neighbours)):
            if not (neighbours[x][y].any() == None):
                score = calculate_ssd(element,neighbours[x][y])
                if score < bestScore:
                    bestScore = score
                    bestX = x-width
                    bestY = y-width

    return [bestX,bestY,bestScore]

def percentageBlue(element):
    redGreen = 0
    blue = 0
    for x in range(0,element.shape[0]):
        for y in range(0, element.shape[1]):
            blue = blue+element[x][y][0]
            redGreen = redGreen + element[x][y][1] + element[x][y][2]
    return blue/(redGreen+blue)

def medianMotion(motionVectors,windowSize):
    filteredVectors = []

    for i in range(0,len(motionVectors),2):
        startIdx = max(0,i-windowSize//2)
        endIdx = min(len(motionVectors),i + windowSize // 2 + 1)
        window = motionVectors[startIdx:endIdx]

        xValues = [vector[2]-vector[0] for vector in window]
        yValues = [vector[3]-vector[1] for vector in window]

        median_x = np.median(xValues)
        median_y = np.median(yValues)

        filteredVector = [
            int(motionVectors[i][0]),
            int(motionVectors[i][1]),
            int(motionVectors[i][0] + median_x),
            int(motionVectors[i][1] + median_y)
        ]

        filteredVectors.append(filteredVector)
    
    return filteredVectors

def drawArrows(image,vectors):
    for x in range(0,len(vectors)):
        image = helper_function.arrowdraw(image, vectors[x][0], vectors[x][1], vectors[x][2], vectors[x][3])
    return image

def euclidean_distance(coord1, coord2):
    x1, y1 = coord1
    x2, y2 = coord2
    distance = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
    return distance

def find_nearest(start_x, start_y, radius, coordlist, acceptStr=False):
    init_coord = (start_x,start_y)
    
    startX = start_x - radius
    startY = start_y - radius

    endX = start_x + radius
    endY = start_y + radius

    best_dist = sys.maxsize
    key = (None,None)

    for x in range(startX,endX):
        for y in range(startY,endY):
            coordKey = f'{x}{y}'
            coord = (x,y)

            if (coordKey in coordlist and not coord == init_coord):
                if (isinstance(coordlist[coordKey], str) or acceptStr):
                    continue
                
                dist = euclidean_distance(init_coord,coord)
                if (dist < best_dist):
                    key = coordKey
                    best_dist = dist
    return key

