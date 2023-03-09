#!/bin/python3

# Rocksat-X 2021 flightsim version Aug/2020

import atexit
import RPi.GPIO as GPIO
import subprocess
import time
import sys

#--------------------------------------------Program Setup-------------------------------------------------------#

# Time variables initialization
st = time.perf_counter()

# Set pin mode
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Define Flag GPIO pins
launch = 12
skirtoff =  13
poweroff30 = 16

# Define Components GPIO pin
proxSensor = 19
uv = 21
Step_Ena = 22
leica = 17

# Define Inhibits
fmi = 26 # Full Mission Inhibit
ibf = 20 # Insert Before Flight

inhibited = 1 # changed from 0 to 1

# Flags setup
GPIO.setup(launch, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(skirtoff, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(poweroff30, GPIO.IN, pull_up_down = GPIO.PUD_UP)

# Components setup
GPIO.setup(proxSensor, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(uv, GPIO.OUT, initial=False)
GPIO.setup(Step_Ena, GPIO.OUT)
GPIO.setup(leica, GPIO.OUT)

# Inhibits setup
GPIO.setup(fmi, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(ibf, GPIO.IN, pull_up_down = GPIO.PUD_UP)

# Checking the state of input GPIOS
print("launch " + str(GPIO.input(launch)))
print("skirt " + str(GPIO.input(skirtoff)))
print("power " + str(GPIO.input(poweroff30)))
print("proximity sensor " + str(GPIO.input(proxSensor)))

#---------------------------------------------Functions-------------------------------------------------------#

def checkFlag(flag):
    check = 0
    output = ''
    on = 0

    while(1):
        # Get current time to pass to thermocouples.py
        cTime = getTimer()
        cTime = int(cTime[0:-2])

        if(flag == launch):
            if(cTime >= -10 and GPIO.input(fmi) and on == 0):
                print("T" + getTimer() + "\r\nPowering on Leica at ( " + time.asctime(time.localtime()) + " )")
                turnOnLeica() 
                on = 1
            elif(cTime >= 10 and GPIO.input(fmi) == 0 and on == 0):
                print("T" + getTimer() + "\r\nPLeica inhibited at ( " + time.asctime(time.localtime()) + " )")
                
            check = 0
            output = "T" + getTimer() + "Time to Launch at ( "
        elif(flag == skirtoff):
            check = 0
            output = "T" + getTimer() + "Rocket Flying for at ( "
        elif(flag == proxSensor):
            check = 1
            output = "T" + getTimer() + "Skirt not cleared proximity sensor at ( " 
        else:
            check = 0
            output = "T" + getTimer() + "Oscar deployed ( "
        output += time.asctime(time.localtime()) + " )"

        count = 0

        for _ in range(0,50):
            if(GPIO.input(flag) == check):
                count += 1
        
        print(" Count", flag, "|", count)
        
        if (count >= 45):
            break
        else:
            print("" + output)
        
        time.sleep(1)

def checkInhibit():
    count = 0
    output = "T" + getTimer() + "Full Mission Inhibit is "

    for x in range(0,50):
        if(GPIO.input(ibf) == 0):
            count += 1
    if (count >= 45):
        output += "active at ( " + time.asctime(time.localtime()) + " )"
        inhibited = 0

    else:
        output += "not active at ( " + time.asctime(time.localtime()) + " )"
        inhibited = 1

    print("" + output)

    return inhibited

def turnOnLeica():
        GPIO.output(leica, GPIO.HIGH)
        time.sleep(1)
        GPIO.output(leica, GPIO.LOW)
        time.sleep(3)
        GPIO.output(leica, GPIO.HIGH)
        time.sleep(1)
        GPIO.output(leica, GPIO.LOW)

def getTimer():
    ct = time.perf_counter()
    timer = ct - st - 20 # 240 seconds - pi boot time (24 seconds) #216
    timer = round(timer)
    if (timer < 0):
        return str(timer) + ": "
    else:
        return "+" + str(timer) + ": "

# Exit and turn off motors on keyboard interrupt
@atexit.register
def exitHandling():
	# on exit turn off motors
	GPIO.output(Step_Ena, True)
	GPIO.cleanup()
	sys.exit(0)

# Turn of BED's 
def motorsOff():
	GPIO.output(Step_Ena, True)

#--------------------------------------------Program Start----------------------------------------------------#

if __name__ == "__main__":
    
    
    
    subprocess.Popen(["time", "-f", "Elapsed time: %E seconds"])
    
    # print Program Banner
    print("\r\nRocksat 2020 - 2021 Flight ")
    print("\r\nTeam UPR")
    print("T" + getTimer() + "Payload start at ( " + time.asctime(time.localtime()) + " )") 
    
    # Turn off motors to prevent overheating and damage to BED
    motorsOff()
    
    # Check for Full Mission Inhibit
    print("T" + getTimer() + "Checking for Full Mission Inhibit at  ( " + time.asctime(time.localtime()) + " )")
    
    # Turn on UVC Lamps
    if(checkInhibit() == 0 and GPIO.input(fmi) == 1):
        GPIO.output(uv, GPIO.HIGH)
        print("T" + getTimer() + "UVC Lamps on at ( " + time.asctime(time.localtime()) + " )")
    else:
            print("T" + getTimer() + "UVC Lamps not turned On. Inhibit Active at ( " + time.asctime(time.localtime()) + " )")
    
    # print UV Sensor Data
    #print("T", getTimer(), "UV SENSOR DATA ( ", time.asctime(time.localtime()) , " )")
    
    # Get current time to pass to thermocouples.py
    cTime = getTimer()
    cTime = cTime[1:-2]
    
    # Start running thermocouples
    if(GPIO.input(fmi)):
        print("T" + getTimer() + "Starting thermocouples at ( " + time.asctime(time.localtime()) + " )")
        tempPlot = ["sudo", "chrt", "--rr", "99", "python3", "thermocouplePrints.py", cTime]
        runTemp = subprocess.Popen(tempPlot)
    else:
        print("T" + getTimer() + "Thermocouples inhibited at ( " + time.asctime(time.localtime()) + " )")
    
    print("T" + getTimer() + "Checking if rocket has launched at  ( " + time.asctime(time.localtime()) + " )")
    
    checkFlag(launch)
    
    # Get current time to pass to endoscope.py
    cTime = getTimer()
    cTime = cTime[1:-2]
    
    """
    # disable endoscope 
    
    # Start endoscope cam
    if(GPIO.input(fmi)):
        print("T" + getTimer() + "Powering on endoscope at  ( " + time.asctime(time.localtime()) + " )")
        cam = ["sudo", "chrt", "--rr", "99", "taskset", "-c", "2", "python", "/home/rocksat/Desktop/endoscopePrint.py", cTime]
        runCam = subprocess.Popen(cam)
    else:
        print("T" + getTimer() + "Endoscope inhibited at ( " + time.asctime(time.localtime()) + " )")
    """
    
    print("T" + getTimer() + "Launching at ( " + time.asctime(time.localtime()) + " )")
    
    
    # Turn off UVC Lamps
    GPIO.output(uv, GPIO.LOW)
    print("T" + getTimer() + "UVC Lamps turned off at ( " + time.asctime(time.localtime()) + " )")
    
    # print UV Sensor Data
    #print("T", getTimer(), "UV SENSOR DATA ( ", time.asctime(time.localtime()) , " )")
    
    checkFlag(skirtoff)
    
    # Check if skirt is off
    checkFlag(proxSensor)
    
    print("T" + getTimer() + "Skirt cleared proximity sensor ( " + time.asctime(time.localtime()) + " )")
    
    # Wait for rocket to reach apogee to deploy Oscar at optimal altitude
    cTime = " " 
    while(1):
        print("T" + getTimer() + "Waiting for rocket to reach Apogee ( " + time.asctime(time.localtime()) + " )")
        cTime = getTimer()
        if(int(cTime[1:-2]) >= 60 and cTime[0] != "-"): # 198
            break
        time.sleep(1)
    
    print("T" + getTimer() + "Rocket reached apogee ( " + time.asctime(time.localtime()) + " )")
    
    # print UV Sensor Data
    #print("T", getTimer(), "UV SENSOR DATA ( ", time.asctime(time.localtime()) , " )")
    
    # Deploy Oscar
    if(GPIO.input(fmi)):
        print("T" + getTimer() + "Deploying Oscar ( " + time.asctime(time.localtime()) + " )")
        deploy = ["sudo", "chrt", "--rr", "99", "taskset", "-c", "3", "python", "/home/rocksat/Desktop/motors.py", "open"]
        runDeploy = subprocess.run(deploy)
    else:
        print("T" + getTimer() + "Oscar inhibited at ( " + time.asctime(time.localtime()) + " )")
    
    motorsOff()
    
    checkFlag(poweroff30)
    
    # Retract Oscar
    if(GPIO.input(fmi)):
        print("T" + getTimer() + "Retracting Oscar ( " + time.asctime(time.localtime()) + " )")
        retract= ["sudo", "chrt", "--rr", "99", "taskset", "-c", "3", "python", "/home/rocksat/Desktop/motors.py", "close"]
        runRetract = subprocess.run(retract)
        print("T" + getTimer() + "Oscar Retracted ( " + time.asctime(time.localtime()) + " )")
    else:
        print("T" + getTimer() + "Oscar inhibited at ( " + time.asctime(time.localtime()) + " )")
        
    
    if(GPIO.input(fmi)):
        runTemp.wait()
        # runCam.wait() # endoscope thing.
    
    print("T" + getTimer() + "Rocksat-X 2021 Mission End at ( " + time.asctime(time.localtime()) + " )")
    
    # Exit successfully
    sys.exit(0)
    
    #----------------------------------------------Program End----------------------------------------------------#
    
