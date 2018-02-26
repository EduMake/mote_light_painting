#!/usr/bin/python
from __future__ import print_function

# File: toplevelminimal.py
try:
	import thread
except:
	from threading import Thread

import os

try:
    import tkinter as tk
    import tkinter.ttk as ttk
except:
    import Tkinter as tk

#s=ttk.Style()
#s.theme_use('clam')


import pygubu
from PIL import Image #PILLOW
import webcolors
import sys
import time
import functools

import logging
import os
import subprocess
import sys
import gtk


import gphoto2 as gp
CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))

simulate = False

if not simulate :
    try:
        from mote import Mote
        mote = Mote()
    except IOError:
        simulate = True

yToStick =[]

def addStick(channel, up=True, length=16, gammacorrect=True):  #from top
    if not simulate :
        mote.configure_channel(channel, length, gammacorrect)
    for i in range(length):
        if up:
            offset = length -1 - i
        else:
            offset = i
        yToStick.append((channel, offset))

addStick(1)
addStick(2)
addStick(3)
addStick(4)



class MyApplication:
    def __init__(self):
        #1: Create a builder
        self.builder = builder = pygubu.Builder()
        self.doQuick = False
        self.timeSlices = 320
        self.motePixelInSceenPixels = 1
        self.graphWidth = self.timeSlices
        self.cameraLag = 3
	self.currentColumn =0


        screen_width = gtk.gdk.screen_width()
        screen_height = gtk.gdk.screen_height()
        


        #2: Load an ui file
        if(screen_width > 500):
            builder.add_from_file(os.path.join(CURRENT_DIR, 'main_repeats.ui'))
            self.motePixelInSceenPixels = 2
        else:
            builder.add_from_file(os.path.join(CURRENT_DIR, 'main_repeats2.ui'))
	        #builder.add_from_file(os.path.join(CURRENT_DIR, 'main_ttk.ui'))
            self.doQuick = True

        #3: Create the toplevel widget.
        self.mainwindow = builder.get_object('mainwindow')

        self.canPreview = builder.get_object('canPreview')

        self.pathFilePath = builder.get_object('pathFilePath')

        self.msgMessage = builder.get_object('msgMessage')

        self.scaDelay = builder.get_object('scaDelay')

        self.scaDuration = builder.get_object('scaDuration')

        self.scaRepeats = builder.get_object('scaRepeats')

        self.cheControlCamera = builder.get_object('cheControlCamera')

        self.chePaintWhite = builder.get_object('chePaintWhite')

        self.builder.tkvariables.__getitem__('intDuration').set(5)

        self.loadImage("images/Spectrum Vertical.png")

        builder.connect_callbacks(self)
        


    def takePhoto(self):
        logging.basicConfig(
            format='%(levelname)s: %(name)s: %(message)s', level=logging.WARNING)
        gp.check_result(gp.use_python_logging())
        camera = gp.check_result(gp.gp_camera_new())
        gp.check_result(gp.gp_camera_init(camera))
        print('Capturing image')
        file_path = gp.check_result(gp.gp_camera_capture(
            camera, gp.GP_CAPTURE_IMAGE))
        print('Camera file path: {0}/{1}'.format(file_path.folder, file_path.name))
        target = os.path.join('~/tmp', file_path.name)
        target = os.path.join(CURRENT_DIR,'..','LightPaintings', file_path.name)
        print('Copying image to', target)
        camera_file = gp.check_result(gp.gp_camera_file_get(
            camera, file_path.folder, file_path.name, gp.GP_FILE_TYPE_NORMAL))
        gp.check_result(gp.gp_file_save(camera_file, target))
        if(self.completeRepeats == self.intRepeats):
            subprocess.call(['xdg-open', target])
        gp.check_result(gp.gp_camera_exit(camera))
        return 0

    def quit(self, event=None):
        self.mainwindow.quit()

    def loadImage(self, filename):
        self.im = Image.open(filename)
        self.rgb_im = self.im.convert('RGB').resize((self.timeSlices, len(yToStick)))
        self.width, self.height = self.rgb_im.size
        self.drawPreview()

    def on_path_changed(self, event=None):
        # Get the path choosed by the user
        filename = self.pathFilePath.cget('path')
        message = "Opened "+filename
        self.showMessage(message)
        self.loadImage(filename)


    def showColumn(self, x):
        if not simulate :
            iPaintWhite = self.builder.tkvariables.__getitem__('iPaintWhite').get()
            for py in range(0, self.height):
                r, g, b = self.rgb_im.getpixel((x, py))
                colour = (r, g, b)
                if colour != (0, 0, 0) and (iPaintWhite or colour != (255, 255, 255)):
                    channel, pixel= yToStick[py]
                    mote.set_pixel(channel, pixel, r, g, b)
            mote.show()
    
    def quickColumn(self, px):
        r, g, b = self.rgb_im.getpixel((px, 1))
        colour = (r, g, b)
        color = str(webcolors.rgb_to_hex(colour))
        self.canPreview.create_rectangle( px, 0, px+1, (len(yToStick) * self.motePixelInSceenPixels), width=0, fill=color)


    def drawColumn(self, px):
        iPaintWhite = self.builder.tkvariables.__getitem__('iPaintWhite').get()
        for py in range(0, len(yToStick)):
            colour = self.rgb_im.getpixel((px, py))
            if colour != (0, 0, 0) and (iPaintWhite or colour != (255, 255, 255)):
                color = str(webcolors.rgb_to_hex(colour))
                self.canPreview.create_rectangle( px, (py * self.motePixelInSceenPixels), px+1, (py * self.motePixelInSceenPixels) + self.motePixelInSceenPixels, width=0, fill=color)

    def drawPreview(self):
        self.canPreview.create_rectangle(0, 0, self.graphWidth, (len(yToStick) * self.motePixelInSceenPixels), fill="black")
        for x in range(0, self.width):
            self.drawColumn(x)
        #print ("Preview complete")

    def onShowEnd(self):
        message = "Show "+str(self.completeRepeats + 1) + "/"+str(self.intRepeats)+" Complete in "+str(time.clock() - self.startTime)+"s"
        self.showMessage(message)
        if not simulate :
            mote.clear()
            mote.show()
        self.completeRepeats += 1
        if(self.completeRepeats < self.intRepeats):
            self.singleShow()

    def startPhoto(self):
        if self.builder.tkvariables.__getitem__('iControlCamera').get() == 1:
            thread.start_new_thread ( self.takePhoto , ())

    def show(self):
        self.canPreview.create_rectangle(0, 0, self.graphWidth, (len(yToStick) * self.motePixelInSceenPixels), fill="#000")
        if simulate:
            message = "Simulating"
        else:
            message = "Show "+str(self.completeRepeats+1)+"/"+str(self.intRepeats)+" started"
        self.showMessage(message)
        duration = float(self.scaDuration.get())
        self.stepTime = int(1000 * duration / float(self.timeSlices))
        self.stepTimeS = duration / float(self.timeSlices)
        #print("self.stepTime", self.stepTime)

        self.currentColumn = self.width-1
        self.startTime = time.clock() 
        self.targetTime = time.clock() + self.stepTimeS
        self.doColumn()

    def doColumn(self):
        thisColumn = self.currentColumn
        if time.clock() < self.targetTime:
            self.timer = self.mainwindow.after(1, self.doColumn)
            return
        
	#print ("doColumn thisColumn", thisColumn, "self.stepTime", self.stepTime)
        self.currentColumn -= 1
        if self.currentColumn  > 0:
            self.targetTime += self.stepTimeS
            self.timer = self.mainwindow.after(1, self.doColumn)
            
        if self.doQuick == True:
            self.quickColumn(thisColumn)
        else:
            self.drawColumn(thisColumn)

        self.showColumn(thisColumn)
        
        if self.currentColumn  == 0:
            self.onShowEnd()

    def showMessage(self, message):
        self.builder.tkvariables.__getitem__('messageText').set(message)

    def on_btnDraw_clicked(self, event=None):
	if self.currentColumn  > 0:
		self.showMessage("Cannot start now, still running")
		return False
        self.intRepeats = int(self.builder.tkvariables.__getitem__('intRepeats').get())
        self.completeRepeats = 0
        self.singleShow()

    def drawCountdown(self):
        delayTime = self.scaDelay.get()
        i = delayTime - self.delayRemaining
        width = self.graphWidth
        if delayTime > 0:
            width = i * self.graphWidth/delayTime

        self.canPreview.create_rectangle(0, 0, width, (len(yToStick) * self.motePixelInSceenPixels), fill="#000")
        message = "Show "+str(self.completeRepeats+1)+"/"+str(self.intRepeats)+" starts in "+str(self.delayRemaining)
        self.canPreview.itemconfigure(self.countdown_id, text=message)
        self.showMessage(message)

        self.delayRemaining -= 1
        if self.delayRemaining > 0:
            self.mainwindow.after(1000, self.drawCountdown)


    def singleShow(self):
        self.canPreview.create_rectangle(0, 0, self.graphWidth, (len(yToStick) * self.motePixelInSceenPixels), fill="#AAA")
        self.countdown_id = self.canPreview.create_text(100, self.graphWidth -100, fill="#F00", text=".....")

        self.delayRemaining = self.scaDelay.get()
        self.drawCountdown()

        '''for i in range(1, delayTime ):
        self.mainwindow.after(i*1000, functools.partial(self.drawCountdown, i, delayTime))
        '''
        delayTime = self.scaDelay.get()
        self.mainwindow.after(delayTime*1000, self.startPhoto)

        lag = 0
        if self.builder.tkvariables.__getitem__('iControlCamera').get() == 1:
            lag = self.cameraLag

        self.mainwindow.after((delayTime + lag) *1000, self.show)

    def run(self):
        self.mainwindow.mainloop()

if __name__ == '__main__':
    app = MyApplication()
    app.run()
