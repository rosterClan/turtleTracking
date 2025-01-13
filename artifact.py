import miscFunctions as mf
import os
import shutil
import cv2

class artifact:
    def __init__(self,name,videoDir,cacheDir,filters:[]) -> None:
        self.name = name
        self.filters:[] = filters
        self.videoDir = videoDir

        self.cache = os.path.join(cacheDir,f'{self.name}_cache')
        if (not os.path.isdir(self.cache)):
            os.mkdir(self.cache)

        if not (type(videoDir) is artifact) and (type(videoDir) is str):
            self.artifactFramesDir = os.path.join(os.path.dirname(videoDir),self.name) 

            if (not os.path.isdir(self.artifactFramesDir)):
                os.mkdir(self.artifactFramesDir)
                if (self.videoDir.split('.')[1] == 'jpg'):
                    shutil.copyfile(self.videoDir,os.path.join(self.artifactFramesDir,'frame0.jpg'))
                elif (self.videoDir.split('.')[1] == 'mov'):
                    self.framenum = mf.writeFramesFromVideo(self.artifactFramesDir,self.videoDir)
            else: 
                count = 0
                for path in os.listdir(self.artifactFramesDir):
                    if os.path.isfile(os.path.join(self.artifactFramesDir, path)):
                        count += 1
                self.framenum = count

            self.currFrame = 0
        self.videoSize = self.returnFrame(0).shape

    def returnFrame(self,frameNum, cache=True, filters=None):
        if (filters == None):
            filters = self.filters

        if (cache):
            try:
                print(f'{self.name} is attempting to return cache for {frameNum}')
                return mf.readFrames(self.cache,frameNum)
            except:
                print('No file in cache. Produceing a render')
        
        if (type(self.videoDir) is artifact):
            frame = self.videoDir.returnFrame(frameNum,cache)
        elif not (type(self.videoDir) is str):
            frame = self.videoDir.getFrame(frameNum)
        else:
            frame = mf.readFrames(self.artifactFramesDir,frameNum)

        for x in range(0,len(filters)):
            print(f'{self.name} is rendering a filter for {frameNum}')
            paramters = filters[x][1]
            paramters['frame'] = frameNum
            paramters['cache'] = cache
            frame = filters[x][0](frame,paramters)

        mf.writeSingleFrame(self.cache,frame,frameNum)
        return frame
    
    def getMaxFrames(self):
        return self.framenum
    
    def getVideoSize(self):
        return self.videoSize
    
    def getVideoDir(self):
        return (self.videoDir)
    
