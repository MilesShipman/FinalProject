import cv2
import pygame
import threading
import datetime
import sys
import os
import cv2
import time
import numpy as np
from Button import PygButton


cv2.ocl.setUseOpenCL(False)

#Break these classes into Python Files for cleanness.

class Camera():
    def __init__(self):
        self.capture = cv2.VideoCapture(0)
        #self.capture.set(cv2.CAP_PROP_AUTOFOCUS, 0) #Turn off I need a well lit enviroment
        self.running = True
        self.frame = None
        self.ready = False
        self.autoFocus = True
        self.autoPrevious = self.capture.get(cv2.CAP_PROP_AUTOFOCUS)
        self.autoExposure = True
        self.exposurePrevious = self.capture.get(cv2.CAP_PROP_AUTO_EXPOSURE)

    def start(self):
        print("Start Thread")
        self.thread = threading.Thread(target=self.update, args=()).start()
        print("Thread Started\n")

    def update(self):
        while(self.capture.isOpened and self.running):
            ret, frame = self.capture.read()
            self.frame = frame
            self.ready = True
            #cv2.imshow("Frame",frame)

    def changeFocus(self):
        if self.autoFocus == True:
            print("Turn off AutoFocus")
            self.autoFocus == False
            self.capture.set(cv2.CAP_PROP_AUTOFOCUS, 0)
        else:
            print("Turn On AutoFocus")
            self.autoFocus == True
            self.capture.set(cv2.CAP_PROP_AUTOFOCUS, self.autoPrevious)

    def changeExposure(self):
        if self.autoExposure == True:
            print("Turn off AutoExposure")
            self.autoExposure = False
            self.capture.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0)
        else:
            print("Turn On AutoExposure")
            self.autoExposure = True
            self.capture.set(cv2.CAP_PROP_AUTO_EXPOSURE, self.exposurePrevious)


    def isReady(self):
        return self.ready

    def read(self):
        return self.frame

    def stop(self):
        self.running = False



class Motion:
    def __init__(self):
        self.lastFrame = None
        self.frame = None
        self.camera = Camera()
        self.camera.start()
        self.ready = False
        self.run = True
        self.effects = False
        self.comparison = None
        self.effect = 1
        self.totalEffect = 4
        self.first = False
        #cv2.ocl.setUseOpenCL(False)
        self.fgbg = cv2.createBackgroundSubtractorMOG2(detectShadows=True)

    def start(self):
        print("Start Thread")
        self.thread = threading.Thread(target=self.update, args=()).start()

    def update(self):
        while (self.camera.isReady() == False):
            test = 0
        self.ready = True
        wait = 5
        current  = None
        self.first = True
        fgbg = cv2.createBackgroundSubtractorMOG2()
        while(self.run):
            if(self.effects):
                if(self.effect == 1):
                    self.motionTrackOrig()
                elif(self.effect == 2):
                    self.motionTrackBlack()
                elif(self.effect == 3):
                    self.motionTrackBG()
                elif(self.effect == 4):
                    self.motionTrackOutline()
                 # #mask#masked_data#diff#masked_data #cv2.cvtColor(frame,cv2.COLOR_GRAY2RGB)
            else: #Just pass the image as is
                self.first = True
                frame = self.camera.read()
                #print(wait)
                if wait > 0:
                    wait = wait - 1
                else:
                    #print("recolor")
                    frame = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
                frame = np.rot90(frame)
                #frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.frame = frame

    def motionTrackOutline(self):
        orig = np.rot90(self.camera.read())

        if self.first == True:
            self.first = False
            self.base = self.comparison
            self.current = np.zeros_like(orig)
        black = np.zeros_like(orig)
        frame = cv2.cvtColor(orig, cv2.COLOR_BGR2GRAY)  # I flip the frame so I have to use this
        diff = frame
        diff = cv2.absdiff(cv2.cvtColor(self.base, cv2.COLOR_BGR2GRAY), diff)  # self.comparison, diff)
        ret, mask = cv2.threshold(diff, 20, 255, cv2.THRESH_BINARY)
        mask_inv = cv2.bitwise_not(mask)
        img1_bg = cv2.bitwise_and(black, black, mask=mask_inv)
        img2_fg = cv2.bitwise_and(orig, orig, mask=mask)
        person = cv2.add(img1_bg, img2_fg)

        edges = cv2.Canny(person, 180, 200)
        ret, mask = cv2.threshold(edges, 20, 255, cv2.THRESH_BINARY)
        img1_bg = cv2.bitwise_and(self.current, self.current, mask=mask_inv)
        img2_fg = cv2.bitwise_and(orig, orig, mask=mask)
        self.current = cv2.add(img1_bg, img2_fg)
        self.frame = cv2.cvtColor(self.current, cv2.COLOR_BGR2RGB)



    def motionTrackBG(self):
        #Use the BackgroundSubtractor built in with opencv
        print("BackgroundSubtractor")
        print(cv2.ocl.setUseOpenCL(False))
        orig = np.rot90(self.camera.read())

        if self.first == True:
            self.first = False
            self.base = self.comparison
            self.current = np.zeros_like(orig)

        fgmask = self.fgbg.apply(orig)
        ret, mask = cv2.threshold(fgmask, 20, 255, cv2.THRESH_BINARY)
        mask_inv = cv2.bitwise_not(mask)
        img1_bg = cv2.bitwise_and(self.current, self.current, mask=mask_inv)
        img2_fg = cv2.bitwise_and(orig, orig, mask=mask)
        self.current = cv2.add(img1_bg, img2_fg)
        self.frame = cv2.cvtColor(self.current, cv2.COLOR_BGR2RGB)

    def motionTrackBlack(self):
        #print("MOTIONBLACK")
        orig= np.rot90(self.camera.read())

        if self.first == True:
            self.first = False
            self.base = self.comparison
            self.current = np.zeros_like(orig)

        frame = cv2.cvtColor(orig, cv2.COLOR_BGR2GRAY)  # I flip the frame so I have to use this
        diff = frame
        diff = cv2.absdiff(cv2.cvtColor(self.base, cv2.COLOR_BGR2GRAY), diff)  # self.comparison, diff)
        ret, mask = cv2.threshold(diff, 20, 255, cv2.THRESH_BINARY)
        mask_inv = cv2.bitwise_not(mask)
        img1_bg = cv2.bitwise_and(self.current, self.current, mask=mask_inv)
        img2_fg = cv2.bitwise_and(orig, orig, mask=mask)
        self.current = cv2.add(img1_bg, img2_fg)
        self.frame = cv2.cvtColor(self.current, cv2.COLOR_BGR2RGB)

    def motionTrackOrig(self):
        orig = np.rot90(self.camera.read())

        if (self.first == True):
            self.base = self.comparison
            self.current = self.comparison
            self.first = False

        frame = cv2.cvtColor(orig, cv2.COLOR_BGR2GRAY)  # I flip the frame so I have to use this
        diff = frame
        # diff = cv2.GaussianBlur(frame, (21, 21), 0)
        diff = cv2.absdiff(cv2.cvtColor(self.current, cv2.COLOR_BGR2GRAY), diff)  # self.comparison, diff)
        ret, mask = cv2.threshold(diff, 20, 255, cv2.THRESH_BINARY)
        mask_inv = cv2.bitwise_not(mask)
        img1_bg = cv2.bitwise_and(self.base, self.base, mask=mask_inv)
        img2_fg = cv2.bitwise_and(orig, orig, mask=mask)
        self.base = cv2.add(img1_bg, img2_fg)
        # mask = np.uint8(diff)
        # masked_data = cv2.add(frame, frame, mask=mask)
        self.frame = cv2.cvtColor(self.base, cv2.COLOR_BGR2RGB)


    def stop(self):
        self.run = False
        self.camera.stop()

    def nextEffect(self):
        print("Next Effect")
        if(self.effect != self.totalEffect):
            self.effect += 1
            self.first = True

    def previousEffect(self):
        print("Previous Effect")
        if(self.effect != 0):
            self.effect -= 1
            self.first = True

    def effectOn(self, capture):
        self.comparison = capture
        self.effects = True

    def effectOff(self):
        self.effects = False

    def read(self):
        return self.frame

    def isReady(self):
        return self.ready



class Countdown():
    def __init__(self):
        self.countdown = False
        self.startTime = None
        self.position  = 0
        self.font = pygame.font.Font('freesansbold.ttf', 100)
        self.text = None
        self.textrect = None
        self.capture = []
        self.captureSize = 5
        self.captureCount = 0
        self.cap = False


    def start(self):
        self.position = 5
        self.countdown = True
        self.capture = []
        self.captureCount = 0
        self.captureSize = 5
        self.startTime = time.time()
        self.cap = False

    def update(self,motion):
        #check the numbers
        #If at 2 than save 5 image
        newTime = time.time()
        if((self.position <= 2) and (self.captureCount < self.captureSize)):
            #print("Save Picture")
            self.capture.append(cv2.cvtColor(motion.read(),cv2.COLOR_BGR2RGB))#cv2.cvtColor(motion.read(), cv2.COLOR_BGR2GRAY))
            #self.capture.append(cv2.GaussianBlur(cv2.cvtColor(motion.read(), cv2.COLOR_BGR2GRAY), (21, 21), 0))
            self.captureCount += 1
        if((newTime - self.startTime)  > 1.0):
            self.position = self.position - 1
            self.startTime = newTime
            if(self.position == 0):
                self.cap = True


    def draw(self, surfaceObj):
        #print(self.countdown)
        if(self.countdown):
            self.text = self.font.render(str(self.position), True, (255, 0, 0), None)  # (255, 255, 255))
            self.textrect = self.text.get_rect()
            self.textrect.centerx = surfaceObj.get_rect().centerx
            self.textrect.centery = surfaceObj.get_rect().centery
            surfaceObj.blit(self.text, self.textrect)
        return self.countdown

    def isReady(self):
        return self.cap

    def stop(self):
        print("Stopping Countown if in progress")
        self.countdown = False


    def getCaptures(self):
        return self.capture


class Booth():
    def __init__(self):
        self.size = width, height = 640, 480
        self.screen = pygame.display.set_mode(self.size)
        self.running = True
        self.motion = Motion()
        self.motion.start()

        #Set up the Rect
        self.startRect = pygame.Rect(75,420,100,50) #Make Scalable at one point
        self.recRect   = pygame.Rect(265,420,100,50)
        self.stopRect  = pygame.Rect(465,420,100,50)

        #Set up the Buttons
        self.startButton = PygButton(rect=self.startRect,caption="Start")
        self.recButton   = PygButton(rect=self.recRect, caption="Record")
        self.stopButton  = PygButton(rect=self.stopRect, caption="Stop")

        self.stopButton.visible = False
        self.recButton.visible = False

        #Countdown
        self.countdown =Countdown()


    def checkKeys(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                print("Change Effect Forwards")
                self.motion.nextEffect()
            if event.key == pygame.K_LEFT:
                print("Change Effect Backwards")
                self.motion.previousEffect()
            if event.key == pygame.K_UP:
                self.motion.camera.changeFocus()
            if event.key == pygame.K_DOWN:
                self.motion.camera.changeExposure()


    def start(self):

        countdownStart = False
        #Poll till Camera is ready
        print("Loop till Ready")
        while(self.motion.isReady() == False):
            test = 0

        time.sleep(1)
        while(self.running):
            for event in pygame.event.get():
                self.checkKeys(event)
                #Check eact button
                startText = self.startButton.handleEvent(event)
                rectText  = self.recButton.handleEvent(event)
                stopText  = self.stopButton.handleEvent(event)
                 #I want upclip

                if(startText == ['up','click']):
                    self.countdown.start()
                    countdownStart = True
                    self.startButton.visible = False
                    self.stopButton.visible = True

                if(stopText == ['up','click']):
                    self.stopButton.visible = False
                    self.startButton.visible = True
                    self.countdown.stop()
                    #Stop the effects
                    self.motion.effectOff()

                #Exit Button
                if event.type == pygame.QUIT:
                    self.running = False
                    self.motion.stop()
                    print("Quitting")

            #Update things first
            if(countdownStart == True):
                self.countdown.update(self.motion) #Update the countdown
                if(self.countdown.isReady()):
                    print("Start showing the Effect")
                    countdownStart = False
                    self.countdown.stop()
                    print(len(self.countdown.capture))
                    self.motion.effectOn(self.countdown.capture[0])

            frame = self.motion.read() #cv2.cvtColor(self.motion.read(),cv2.COLOR_GRAY2RGB)
            frame = pygame.surfarray.make_surface(frame)
            frame = pygame.transform.scale(frame,(640,480))
            self.screen.blit(frame,(0,0))
            self.startButton.draw(self.screen)
            self.recButton.draw(self.screen)
            self.stopButton.draw(self.screen)
            countdownStart = self.countdown.draw(self.screen)
            pygame.display.flip()


def main():
    print("Hello World")
    pygame.init()
    viewer = Booth()
    viewer.start()
    pygame.quit()
    sys.exit(0)


main()