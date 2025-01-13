import cv2
import math
import queue
import sys
import numpy as np
from segmentQueue import averageTracker
from scipy.optimize import fsolve

from matplotlib import pyplot as plt

def bluescreenfilter(frame:np,variables):
    for x in range(0,frame.shape[0]):
        for y in range(0,frame.shape[1]):
            if (frame[x][y][0] > variables['threashold']):
                frame[x][y] = np.array([0,0,0])
    return frame

def isolateColorByDominent(frame:np,variables):
    otherColors = [0,1,2]
    del otherColors[variables['color']]

    for x in range(0,frame.shape[0]):
        for y in range(0,frame.shape[1]):
            if not (isEmpty(frame[x][y])):
                for val in otherColors:
                    selectedColor = frame[x][y][variables['color']]
                    currentColor = frame[x][y][val]
                    pogpogpogpog = int(selectedColor) - int(currentColor)
                    isDifferent = pogpogpogpog < variables['differenceMargin']

                    if (isDifferent or frame[x][y][variables['color']] < variables['threashold'] ):
                        frame[x][y] = np.array([0,0,0])
    
    return frame

def rotate_point(x, y, angle_degrees, frame:np):
    c_x, c_y = int(frame.shape[0]/2), int(frame.shape[1]/2)
    x0, y0 = x - c_x, y - c_y
    theta = math.radians(angle_degrees)
    x_prime = x0 * math.cos(theta) - y0 * math.sin(theta)
    y_prime = x0 * math.sin(theta) + y0 * math.cos(theta)
    x_new, y_new = x_prime + c_x, y_prime + c_y
    return math.floor(x_new), math.floor(y_new)

def computeDistance(origin, dest):
    x1, y1 = origin
    x2, y2 = dest
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def computeAngle(origin, dest):
    x1, y1 = origin
    x2, y2 = dest
    angle_radians = math.atan2(y2 - y1, x2 - x1)
    return math.degrees(angle_radians)

def performRotation(frame,variables):
    if not ('anchor' in variables):
        anchor = (int(frame.shape[0]/2),int(frame.shape[1]/2))
    else:
        anchor = variables['anchor']

    rotation_matrix = cv2.getRotationMatrix2D(anchor, variables['degree'], 1)
    frame = cv2.warpAffine(frame, rotation_matrix, (frame.shape[1], frame.shape[0]))
    return frame

def resize(frame,variables):
    newX = math.floor(variables['size'][0])
    newY = math.floor(variables['size'][1])

    return cv2.resize(frame,(newX,newY))

def transform(frame: np.array, variables):
    aspect_ratio = frame.shape[0] / frame.shape[1]
    newFrameY = int(computeDistance(variables['newOrign'], variables['newDest']))

    size = {'size':(int(newFrameY * aspect_ratio),newFrameY)}
    frame = resize(frame,size)

    angle = computeAngle(variables['newOrign'], variables['newDest'])
    frame = performRotation(frame,{'degree':angle})

    anchor = rotate_point(frame.shape[0]-1,int(frame.shape[1]/2),angle,frame)
    overlaySettings = {'overlayPos':anchor,'canvasPos':(variables['newDest'][0],variables['newDest'][1]),'canvas':variables['canvas']}

    return overlay(frame,overlaySettings)

def find_linear_equation(point1, point2):
    x1, y1 = point1
    x2, y2 = point2
    m = (y2 - y1) / (x2 - x1)
    c = y1 - m * x1
    return m, c

def find_new_point(m, c, x2, y2, z):
    def equation(x3):
        y3 = m * x3 + c
        return np.sqrt((x3 - x2)**2 + (y3 - y2)**2) - z
    
    initial_guess = x2 + z if m >= 0 else x2 - z

    x3_solution = fsolve(equation, initial_guess)
    
    y3_solution = m * x3_solution + c
    
    return (math.floor(x3_solution[0]), math.floor(y3_solution[0]))

def ajustPoints(middle,dest,minLength=90):
    point = list(dest)
    if (computeDistance(middle,point) < minLength):
        m,c = find_linear_equation(middle,point)

        best = minLength - computeDistance(middle,point)
        increaseX = True
        shutDown = False
        
        while True:
            if increaseX:
                point[0] += 1
            else:
                point[0] -= 1
            point[1] = m*point[0] + c
            potentialBest = minLength - computeDistance(middle,point)
            
            if potentialBest < best and potentialBest > 0:
                best = potentialBest
                shutDown = True
            else:
                increaseX = False
                if (shutDown):
                    break
                point = list(dest)
                shutDown = True
                

    return (math.floor(point[0]),math.floor(point[1]))

def overlay(overlay:np,variables):
    if variables['overlayPos'] == None:
        variables['overlayPos'] = (int(overlay.shape[0]/2),int(overlay.shape[1]/2))
    if variables['canvasPos'] == None:
        variables['canvasPos'] = (int(variables['canvas'].shape[0]/2),int(variables['canvas'].shape[1]/2))

    xFollowingAnchor = overlay.shape[0] - int(variables['overlayPos'][0])
    xPreceedingAnchor = overlay.shape[0] - xFollowingAnchor
    
    yFollowingAnchor = overlay.shape[1] - int(variables['overlayPos'][1])
    yPreceedingAnchor = overlay.shape[1] - yFollowingAnchor

    dummyX = 0
    for x in range(variables['canvasPos'][0]-xPreceedingAnchor,variables['canvasPos'][0]+xFollowingAnchor):
        dummyY = 0
        for y in range(variables['canvasPos'][1]-yPreceedingAnchor,variables['canvasPos'][1]+yFollowingAnchor):
            if not (isEmpty(overlay[dummyX][dummyY])):
                try:
                    if ((0 < x < variables['canvas'].shape[0]) and (0 < y < variables['canvas'].shape[1])):
                        variables['canvas'][x][y] = overlay[dummyX][dummyY]
                except:
                    continue
            dummyY += 1
        dummyX += 1
    return variables['canvas']

def placeMarker(canvas:np,x,y,size):
    for subX in range(x-size,x+size+1):
        for subY in range(y-size,y+size+1):
            canvas[subX][subY] = np.array([0,0,255])
    return canvas

def showImage(frame):
    if frame.dtype == np.float64:
        norm_img = cv2.normalize(frame, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
        frame_8bit = np.uint8(norm_img)
    else:
        frame_8bit = frame

    img_rgb = cv2.cvtColor(frame_8bit, cv2.COLOR_BGR2RGB)

    plt.imshow(img_rgb)
    plt.show()

def increaseSaturation(image, variables):
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    hsv[:,:,1] = np.clip(hsv[:,:,1] * variables['saturation'], 0, 255)
    saturated_img = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
    return saturated_img

def average_colors(image,variables):
    averaged_image = np.zeros(image.shape)

    qeue:averageTracker = averageTracker(10)
    for x in range(0,image.shape[0]):
        for y in range(0,image.shape[1]):
            qeue.addPixels(image[x][y])
            if (qeue.getAverage()):
                averaged_image[x][y] = qeue.getOutput()
                
    return averaged_image

def increase_brightness(image,variables):
    hsv = cv2.cvtColor(image,cv2.COLOR_BGR2HSV)
    h,s,v = cv2.split(hsv)

    lim = 255 - variables['brightness']
    v[v>lim] = 255
    v[v <= lim] += variables['brightness']

    final_hsv = cv2.merge((h,s,v))
    image = cv2.cvtColor(final_hsv, cv2.COLOR_HSV2BGR)

    return image

def createMask(image, variables):
    mask = np.zeros(image.shape)
    for x in range(0,image.shape[0]):
        for y in range(0,image.shape[1]):
            if sum(image[x][y]) > 100:
                mask[x][y] = np.array([255,255,255])
    return mask

def applyMask(image: np.ndarray, variables: dict) -> np.ndarray:
    combinedImage = np.copy(image)

    if not (type(variables['mask']) is np.ndarray):
        mask = variables['mask'].returnFrame(variables['frame'], variables['cache'])
    else:
        mask = variables['mask']

    for x in range(0,mask.shape[0]):
        for y in range(0, mask.shape[1]):
            if isEmpty(mask[x][y]):
                combinedImage[x][y] = np.array([0,0,0])

    return combinedImage

def getBoundingBox(frame:np,variables):

    lowestX = 1000000000000
    highestX = -lowestX
    lowestY = lowestX
    highestY = highestX

    for x in range(0,frame.shape[0]):
        for y in range(0,frame.shape[1]):
            if not (isEmpty(frame[x][y])):
                if x > highestX:
                    highestX = x
                if x < lowestX:
                    lowestX = x
                if y > highestY:
                    highestY = y
                if y < lowestY:
                    lowestY = y

    return {'pointOne':(lowestX,lowestY),'pointTwo':(highestX,highestY)} 

def drawBoundingBox(frame:np,variables):
    boundingBox = variables['boundingBox']

    pointOne = boundingBox['pointOne'] #smaller then pointTwo
    pointTwo = boundingBox['pointTwo']

    for x in range(pointOne[0],pointTwo[0]):
        frame[x][pointOne[1]] = np.array([255,255,255])
        frame[x][pointTwo[1]] = np.array([255,255,255])

    for y in range(pointOne[1],pointTwo[1]):
        frame[pointOne[0]][y] = np.array([255,255,255])
        frame[pointTwo[0]][y] = np.array([255,255,255])

    return frame

def isEmpty(pixels: np.ndarray):
    try:
        return pixels[0] == pixels[1] == pixels[2] == 0
    except:
        return False

def normalizedIsEmpty(pixel:np):
    total = pixel[0] + pixel[1] + pixel[2]
    return total < 5

def takeDamage(frame:np,variables):
    for x in range(0,frame.shape[0]):
        for y in range(0, frame.shape[1]):
            if not (isEmpty(frame[x][y])):
                frame[x][y] = np.array([frame[x][y][0],frame[x][y][1],230])

    return frame

def fillColors(frame:np,variables):
    pointOne = variables['pointOne']
    pointTwo = variables['pointTwo']
    color = variables['color']

    for x in range(pointOne[0],pointTwo[0]):
        for y in range(pointOne[1],pointTwo[1]):
            if -1 < x < frame.shape[0]:
                if -1 < y < frame.shape[1]:
                    frame[x][y] = color
    
    return frame

def isEmptyCanvas(frame:np,variables):
    for x in range(0,frame.shape[0]):
        for y in range(0,frame.shape[1]):
            if sum(frame[x][y]) > 50:
                return False
    return True 

def moveYaxis(frame, point, target_y):
    delta_y = target_y - point[1]
    M = np.float32([[1, 0, 0], [0, 1, delta_y]])
    shifted_img = cv2.warpAffine(frame, M, (frame.shape[1], frame.shape[0]))

    if delta_y > 0:
        shifted_img[:delta_y] = (0, 0, 0)  # Fill with black if shifting down
    else:
        shifted_img[delta_y:] = (0, 0, 0)  # Fill with black if shifting up
    return shifted_img

def convert_binary_mask(frame):
    binaryMask = np.zeros((frame.shape[0],frame.shape[1],1))
    for x in range(0,frame.shape[0]):
        for y in range(0,frame.shape[1]):
            if not (isEmpty(frame[x][y])):
                binaryMask[x][y] = 1
    return binaryMask

def find_largest_sphere(mask):
    circles = queue.PriorityQueue()
    for x in range(0,mask.shape[0]):
        for y in range(0,mask.shape[1]):
            if not (isEmpty(mask[x][y])):
                radius = fitCircle(mask,x,y)
                if (radius > 0):
                    circles.put((-radius,(x,y)))

    largestCircle = circles.get()
    return (-largestCircle[0],(largestCircle[1][1],largestCircle[1][0]))

def fitCircle(frame:np,x,y):
    radius = 1
    while True:
        compareFrame = np.copy(frame)
        circleFrame = np.copy(frame)
        #showImage(compareFrame)
        circleFrame = cv2.circle(circleFrame, (y,x), int(radius), (255, 255, 255), 2)
        #showImage(circleFrame)
        outputFrame:np = cv2.bitwise_xor(compareFrame, circleFrame)
        #showImage(outputFrame)
        all_zeros = np.all(outputFrame == [0, 0, 0])
        if not (all_zeros):
            break
        radius += 1
    return radius