import cv2
import numpy as np
import os
import miscFunctions as mf
import queue
from artifact import artifact
import filters as filter
from character import character
from scoreBoard import scoreBoard
from straws import straws
import random
from monster import monster
import math

file = os.path.dirname(os.path.abspath(__file__))
assets = os.path.join(file,'assets')

extractDir = os.path.join(file,'monkeyFrames')
videoDir = os.path.join(assets,'monk.mov')
cacheDirectory = os.path.join(file,'cache')
exportFrames = os.path.join(file,'exportFrames')
videoExport = os.path.join(file,'videoExport')

characterTextures = os.path.join(file,'textures')
BodyDir = os.path.join(characterTextures,'body.jpg')
LeftArmDir = os.path.join(characterTextures,'leftArm.jpg')
LeftLegDir = os.path.join(characterTextures,'leftLeg.jpg')
RightArmDir = os.path.join(characterTextures,'rightArm.jpg')
RightLegDir = os.path.join(characterTextures,'rightLeg.jpg')

Body = artifact('body',BodyDir,cacheDirectory,[])
LeftArm = artifact('leftArm',LeftArmDir,cacheDirectory,[])
LeftLeg = artifact('leftLef',LeftLegDir,cacheDirectory,[])
RightArm = artifact('rightArm',RightArmDir,cacheDirectory,[])
RightLeg = artifact('rightLeg',RightLegDir,cacheDirectory,[])

monsterPathDir = os.path.join(file,"MonsterCharacterTextures")
monsterBodyDir = os.path.join(monsterPathDir,"center.jpg")
monsterLeftWingDir = os.path.join(monsterPathDir,"leftWing.jpg")
monsterRightWingDir = os.path.join(monsterPathDir,"rightWing.jpg")

monsterBody = artifact('monsterBody',monsterBodyDir,cacheDirectory,[])
monsterLeftWing = artifact('monsterLeftWing',monsterLeftWingDir,cacheDirectory,[])
monsterRightWing = artifact('monsterRightWing',monsterRightWingDir,cacheDirectory,[])

frameNum = 955
monkeyMask = artifact("mask",videoDir,cacheDirectory,[(filter.increase_brightness,{'brightness':200}),
                                (filter.increaseSaturation,{'saturation':1.8}),
                                (filter.bluescreenfilter,{'threashold':230}),
                                (filter.createMask,{})])

monkey = artifact("maskedVideo",videoDir,cacheDirectory,[(filter.applyMask,{'mask':monkeyMask})])
mainCharacterArtifact = artifact('mainCharacter',character(monkey,Body,LeftArm,RightArm,LeftLeg,RightLeg,cacheDirectory,275,500),cacheDirectory,[])
mainCharacter:character = mainCharacterArtifact.getVideoDir()
#mainCharacter = character(monkey,Body,LeftArm,RightArm,LeftLeg,RightLeg,cacheDirectory,270,500)

#tempExportDir = os.path.join(file,'tempExport')
#for x in range(1,900):
#    frame = mainCharacter.getFrame(57)
#    mf.writeSingleFrame(tempExportDir,frame,57)


MasterVideoSize = (320, 568)

scoreboardAssets = os.path.join(file,'scoreBoard')
oneDir = os.path.join(scoreboardAssets,'1.jpg')
twoDir = os.path.join(scoreboardAssets,'2.jpg')
threeDir = os.path.join(scoreboardAssets,'3.jpg')
fourDir = os.path.join(scoreboardAssets,'4.jpg')
fiveDir = os.path.join(scoreboardAssets,'5.jpg')
sixDir = os.path.join(scoreboardAssets,'6.jpg')
sevenDir = os.path.join(scoreboardAssets,'7.jpg')
eightDir = os.path.join(scoreboardAssets,'8.jpg')
nineDir = os.path.join(scoreboardAssets,'9.jpg')
zeroDir = os.path.join(scoreboardAssets,'0.jpg')
scoreTitle = os.path.join(scoreboardAssets,'scoreTitle.jpg')

characterArtifacts = [
    artifact('zero', zeroDir, cacheDirectory, []),
    artifact('one', oneDir, cacheDirectory, []),
    artifact('two', twoDir, cacheDirectory, []),
    artifact('three', threeDir, cacheDirectory, []),
    artifact('four', fourDir, cacheDirectory, []),
    artifact('five', fiveDir, cacheDirectory, []),
    artifact('six', sixDir, cacheDirectory, []),
    artifact('seven', sevenDir, cacheDirectory, []),
    artifact('eight', eightDir, cacheDirectory, []),
    artifact('nine', nineDir, cacheDirectory, [])
]
scoreTitleArtifact = artifact('scoreTitle', scoreTitle, cacheDirectory, [])
score = scoreBoard(scoreTitleArtifact,characterArtifacts,(MasterVideoSize[0],MasterVideoSize[1],3))
scoreArtifact = artifact('scoreboard',score,cacheDirectory,[])

backgroundImage = os.path.join(assets,'backgroundImage.jpg')
background = artifact('background',backgroundImage,cacheDirectory,[])
tempBackgroundFrame = background.returnFrame(0)

deathImage = os.path.join(assets,'deathImage.jpg')
deathImageArtifact = artifact('deathScreen',deathImage,cacheDirectory,[])

winImage = os.path.join(assets,'winImage.jpg')
winImageArtifact = artifact('winImage',winImage,cacheDirectory,[])

strawAssets = os.path.join(file,'straws')
strawDir = os.path.join(strawAssets,'strawTexture.jpg')

def generateStartConfigMonster():
    leftSpeeds =[-12,-11,-10,-9,-8]
    rightSpeeds =[8,9,10,11,12]
    defaultYSpeeds = [-12,-11,-10,-9,-8,-7,-6,-5,-4,-3,-2,-1,1,2,3,4,5,6,7,8,9,10,11,12]
    
    spawnPoints = [
                    (random.randint(0,MasterVideoSize[0]),-80),
                    (random.randint(0,MasterVideoSize[0]),MasterVideoSize[1]-20)
                ]

    index = random.randint(0,len(spawnPoints)-1)
    spawnPoint = spawnPoints[index]

    if spawnPoint[1] > 0:
        startVelocity = (defaultYSpeeds[random.randint(0,len(defaultYSpeeds)-1)],leftSpeeds[random.randint(0,len(leftSpeeds)-1)])
    else:
        startVelocity = (defaultYSpeeds[random.randint(0,len(defaultYSpeeds)-1)],rightSpeeds[random.randint(0,len(leftSpeeds)-1)])

    return spawnPoint,startVelocity

monsterList = []
strawList = []
renderQueue = []
endFrame = 839

backgroundFrame = deathImageArtifact.returnFrame(0)

for x in range(1,endFrame):
    if (mainCharacter.isDead()):
        backgroundFrame = deathImageArtifact.returnFrame(0)
        mf.writeSingleFrame(exportFrames,backgroundFrame,x)
    elif (endFrame-15 < x):
        backgroundFrame = winImageArtifact.returnFrame(0)
        mf.writeSingleFrame(exportFrames,backgroundFrame,x)
    else:
        backgroundFrame = background.returnFrame(0)
        score.setScore(mainCharacter.getCharacterScore())

        ### render artifacts ###
        renderQueue.append(scoreArtifact)
        renderQueue.append(mainCharacterArtifact)
        renderQueue.extend(strawList)
        renderQueue.extend(monsterList)

        for element in renderQueue:
            backgroundFrame = element.returnFrame(x,False,[(filter.overlay,{'overlayPos':None,'canvasPos':None,'canvas':backgroundFrame})])
        mf.writeSingleFrame(exportFrames,backgroundFrame,x)
        renderQueue.clear()

        ### calculating the straw collision ###
        for strawArtifact in strawList:
            actualStraw:straws = strawArtifact.getVideoDir()
            if (actualStraw.isDead()):
                strawList.remove(strawArtifact)
            mainCharacter.collision(actualStraw)

        ### calculating the monster collision ###
        for monsterArtifact in monsterList:
            actualMonster:monster = monsterArtifact.getVideoDir()
            if (actualMonster.isDead()):
                monsterList.remove(monsterArtifact)
            mainCharacter.collision(actualMonster)

        ### adding new monsters to the environment ###
        while (len(monsterList) < 5):
            startPos,startSpeeds = generateStartConfigMonster()
            newMonster = monster(monsterBody,monsterLeftWing,monsterRightWing,startPos,cacheDirectory,MasterVideoSize)
            newMonster.setSpeed(startSpeeds)
            newMonsterArtifact = artifact('monsterACTUAL',newMonster,cacheDirectory,[])
            monsterList.append(newMonsterArtifact)

        while (len(strawList) < 3):
            strawArtifact = artifact('straw',strawDir,cacheDirectory,[])
            straw = straws(strawArtifact,(0,random.randint(0,MasterVideoSize[1])),(MasterVideoSize[0],MasterVideoSize[1],3))
            strawList.append(artifact('strawArtifact',straw,cacheDirectory,[]))
        

out = cv2.VideoWriter('output_video.avi',cv2.VideoWriter_fourcc(*'DIVX'), 12, (backgroundFrame.shape[1],backgroundFrame.shape[0]))
for x in range(1,endFrame):  
    if (x > 839-50):
        frame = winImageArtifact.returnFrame(0)
    else:
        individualFrameDir = os.path.join(exportFrames, f'frame{x}.jpg')
        frame = cv2.imread(individualFrameDir)
    frame = cv2.putText(frame, 'SID520659025_Asgmt2Opt1', (25, 35), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 5, cv2.LINE_AA) 
    out.write(frame)
out.release()


