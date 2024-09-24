#!/usr/bin/env pybricks-micropython
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import (Motor, TouchSensor, ColorSensor,
                                 InfraredSensor, UltrasonicSensor, GyroSensor)
from pybricks.parameters import Port, Stop, Direction, Button, Color
from pybricks.tools import wait, StopWatch, DataLog
from pybricks.robotics import DriveBase
from pybricks.media.ev3dev import SoundFile, ImageFile
import os


# This program requires LEGO EV3 MicroPython v2.0 or higher.
# Click "Open user guide" on the EV3 extension tab for more information.

def vaParaAnguloServo2(valor):
    usaServo2()
    valorBase=9945
    anguloGarra=610000+(valorBase*valor)
    os.system("sh -c 'echo %d > /sys/class/pwm/pwmchip1/pwm0/duty_cycle'" %anguloGarra)

def vaParaAnguloServo1(valor):
    usaServo1()
    valorBase=9945
    anguloGarra=610000+(valorBase*valor)
    os.system("sh -c 'echo %d > /sys/class/pwm/pwmchip1/pwm0/duty_cycle'" %anguloGarra)


def vaParaAnguloServo4(valor):
    usaServo4()
    valorBase=9945
    anguloGarra=610000+(valorBase*valor)
    os.system("sh -c 'echo %d > /sys/class/pwm/pwmchip0/pwm0/duty_cycle'" %anguloGarra)


def vaParaAnguloServo3(valor):
    usaServo3()
    valorBase=9945
    anguloGarra=610000+(valorBase*valor)
    os.system("sh -c 'echo %d > /sys/class/pwm/pwmchip0/pwm0/duty_cycle'" %anguloGarra)


    
def usaServo1():
    os.system("sh -c 'echo out > /sys/class/gpio/gpio90/direction'")
    wait(20)
    os.system("sh -c 'echo 1 > /sys/class/gpio/gpio90/value'")
    os.system("sh -c 'echo in > /sys/class/gpio/gpio83/direction'")

def usaServo2():
    os.system("sh -c 'echo out > /sys/class/gpio/gpio83/direction'")
    wait(20)
    os.system("sh -c 'echo 1 > /sys/class/gpio/gpio83/value'")
    os.system("sh -c 'echo in > /sys/class/gpio/gpio90/direction'")
    

def usaServo4():
    os.system("sh -c 'echo out > /sys/class/gpio/gpio104/direction'")
    wait(20)
    os.system("sh -c 'echo 1 > /sys/class/gpio/gpio104/value'")
    os.system("sh -c 'echo in > /sys/class/gpio/gpio89/direction'")

def usaServo3():
    os.system("sh -c 'echo out > /sys/class/gpio/gpio89/direction'")
    wait(20)
    os.system("sh -c 'echo 1 > /sys/class/gpio/gpio89/value'")
    os.system("sh -c 'echo in > /sys/class/gpio/gpio104/direction'")


def ativaServos():
    os.system("sh -c 'echo 1 > /sys/class/pwm/pwmchip1/pwm0/enable'")
    os.system("sh -c 'echo 1 > /sys/class/pwm/pwmchip0/pwm0/enable'")
    wait(20)

def desativaServos():
    os.system("sh -c 'echo 0 > /sys/class/pwm/pwmchip0/pwm0/enable'")
    os.system("sh -c 'echo 0 > /sys/class/pwm/pwmchip0/pwm0/enable'")
    wait(20)


# Create your objects here.
ev3 = EV3Brick()
ativaServos()
vaParaAnguloServo1(0)
wait(2000)
vaParaAnguloServo1(180)
wait(2000)
vaParaAnguloServo2(0)
wait(2000)
vaParaAnguloServo2(180)
wait(2000)
vaParaAnguloServo3(0)
wait(2000)
vaParaAnguloServo3(180)
wait(2000)
vaParaAnguloServo4(0)
wait(2000)
vaParaAnguloServo4(180)
wait(2000)
desativaServos()
# Write your program here.
ev3.speaker.beep()
