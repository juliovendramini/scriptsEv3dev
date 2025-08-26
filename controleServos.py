#!/usr/bin/env pybricks-micropython
#ATENCAO, NÃO RECOMENDO MAIS O USO DISSO. NÃO FUNCIONA BEM!
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


def vaParaAnguloServo1(valor): #abrir porta
    desativaServo2()
    #wait(100)
    valorBase=9945
    anguloGarra=610000+(valorBase*valor)
    '''duty_cycle = open("/sys/class/pwm/pwmchip1/pwm0/duty_cycle", 'w')
    duty_cycle.write(str(anguloGarra))
    duty_cycle.close()'''
    os.system("sh -c 'echo %d > /sys/class/pwm/pwmchip1/pwm0/duty_cycle'" %anguloGarra)
    usaServo1()

def vaParaAnguloServo2(valor):#garra direita
    desativaServo1()
    #wait(100)
    valorBase=9945
    anguloGarra=610000+(valorBase*valor)
    '''duty_cycle = open("/sys/class/pwm/pwmchip1/pwm0/duty_cycle", 'w')
    duty_cycle.write(str(anguloGarra))
    duty_cycle.close()'''
    os.system("sh -c 'echo %d > /sys/class/pwm/pwmchip1/pwm0/duty_cycle'" %anguloGarra)
    usaServo2()


def vaParaAnguloServo3(valor):#Subir garra
    desativaServo4()
    #wait(100)
    valorBase=9945
    anguloGarra=610000+(valorBase*valor)
    '''duty_cycle = open("/sys/class/pwm/pwmchip0/pwm0/duty_cycle", 'w')
    duty_cycle.write(str(anguloGarra))
    duty_cycle.close()'''
    os.system("sh -c 'echo %d > /sys/class/pwm/pwmchip0/pwm0/duty_cycle'" %anguloGarra)
    usaServo3()

def vaParaAnguloServo4(valor):#garra esquerda
    desativaServo3()
    #wait(100)
    valorBase=9945
    anguloGarra=610000+(valorBase*valor)
    '''duty_cycle = open("/sys/class/pwm/pwmchip0/pwm0/duty_cycle", 'w')
    duty_cycle.write(str(anguloGarra))
    duty_cycle.close()'''
    os.system("sh -c 'echo %d > /sys/class/pwm/pwmchip0/pwm0/duty_cycle'" %anguloGarra)
    usaServo4()

    
def usaServo1():
    '''direction = open("/sys/class/gpio/gpio90/direction", 'w')
    direction.write('out')
    direction.close()'''
    #os.system("sh -c 'echo out > /sys/class/gpio/gpio90/direction'")
    #wait(20)
    '''value = open("/sys/class/gpio/gpio90/value", 'w')
    value.write('1')
    value.close()'''
    #os.system("sh -c 'echo 1 > /sys/class/gpio/gpio90/value'")
    '''direction = open("/sys/class/gpio/gpio83/direction", 'w')
    direction.write('in')
    direction.close()'''
    os.system("sh -c 'echo in > /sys/class/gpio/gpio83/direction'")

def desativaServo2():
    os.system("sh -c 'echo out > /sys/class/gpio/gpio90/direction'")
    os.system("sh -c 'echo 1 > /sys/class/gpio/gpio90/value'")

def desativaServo1():
    os.system("sh -c 'echo out > /sys/class/gpio/gpio83/direction'")
    os.system("sh -c 'echo 1 > /sys/class/gpio/gpio83/value'")

def usaServo2():
    '''direction = open("/sys/class/gpio/gpio83/direction", 'w')
    direction.write('out')
    direction.close()'''
    #os.system("sh -c 'echo out > /sys/class/gpio/gpio83/direction'")
   # wait(20)
    '''value = open("/sys/class/gpio/gpio83/value", 'w')
    value.write('1')
    value.close()'''
    #os.system("sh -c 'echo 1 > /sys/class/gpio/gpio83/value'")
    '''direction = open("/sys/class/gpio/gpio90/direction", 'w')
    direction.write('in')
    direction.close()'''
    os.system("sh -c 'echo in > /sys/class/gpio/gpio90/direction'")
    

def usaServo4():
    '''direction = open("/sys/class/gpio/gpio104/direction", 'w')
    direction.write('out')
    direction.close()'''
    #os.system("sh -c 'echo out > /sys/class/gpio/gpio104/direction'")
  #  wait(20)
    '''value = open("/sys/class/gpio/gpio104/value", 'w')
    value.write('1')
    value.close()'''
    #os.system("sh -c 'echo 1 > /sys/class/gpio/gpio104/value'")
    '''direction = open("/sys/class/gpio/gpio89/direction", 'w')
    direction.write('in')
    direction.close()'''
    os.system("sh -c 'echo in > /sys/class/gpio/gpio89/direction'")

def desativaServo3():
    os.system("sh -c 'echo out > /sys/class/gpio/gpio104/direction'")
    os.system("sh -c 'echo 1 > /sys/class/gpio/gpio104/value'")

def desativaServo4():
    os.system("sh -c 'echo out > /sys/class/gpio/gpio89/direction'")
    os.system("sh -c 'echo 1 > /sys/class/gpio/gpio89/value'")


def usaServo3():
    '''direction = open("/sys/class/gpio/gpio89/direction", 'w')
    direction.write('out')
    direction.close()'''
    #os.system("sh -c 'echo out > /sys/class/gpio/gpio89/direction'")
   # wait(20)
    '''value = open("/sys/class/gpio/gpio89/value", 'w')
    value.write('1')
    value.close()'''
    #os.system("sh -c 'echo 1 > /sys/class/gpio/gpio89/value'")
    
    '''direction = open("/sys/class/gpio/gpio104/direction", 'w')
    direction.write('in')
    direction.close()'''
    os.system("sh -c 'echo in > /sys/class/gpio/gpio104/direction'")


def ativaServos():
    '''enable = open("/sys/class/pwm/pwmchip1/pwm0/enable", 'w')
    enable.write('1')
    enable.close()'''
    os.system("sh -c 'echo 1 > /sys/class/pwm/pwmchip1/pwm0/enable'")
    '''enable = open("/sys/class/pwm/pwmchip0/pwm0/enable", 'w')
    enable.write('1')
    enable.close()'''
    os.system("sh -c 'echo 1 > /sys/class/pwm/pwmchip0/pwm0/enable'")
   # wait(20)

def ativaServos1_2():
    '''enable = open("/sys/class/pwm/pwmchip1/pwm0/enable", 'w')
    enable.write('1')
    enable.close()'''
    os.system("sh -c 'echo 1 > /sys/class/pwm/pwmchip1/pwm0/enable'")
    # wait(20)

def ativaServos3_4():
    '''enable = open("/sys/class/pwm/pwmchip0/pwm0/enable", 'w')
    enable.write('1')
    enable.close()'''
    os.system("sh -c 'echo 1 > /sys/class/pwm/pwmchip0/pwm0/enable'")
    # wait(20)

def desativaServos():
    '''enable = open("/sys/class/pwm/pwmchip1/pwm0/enable", 'w')
    enable.write('0')
    enable.close()'''
    os.system("sh -c 'echo 0 > /sys/class/pwm/pwmchip1/pwm0/enable'")
    '''enable = open("/sys/class/pwm/pwmchip0/pwm0/enable", 'w')
    enable.write('0')
    enable.close()'''
    os.system("sh -c 'echo 0 > /sys/class/pwm/pwmchip0/pwm0/enable'")
    wait(20)


# Create your objects here.
# ev3 = EV3Brick()



# ativaServos()
# vaParaAnguloServo1(90)
# wait(2000)
# vaParaAnguloServo2(90)
# wait(2000)
# vaParaAnguloServo3(90)
# wait(2000)
# vaParaAnguloServo4(90)
# wait(2000)
# desativaServos()
# # Write your program here.
# ev3.speaker.beep()
