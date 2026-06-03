#exemplo para comunicação entre o SPIKE e qualquer outro equipamento via porta serial 
from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor, ColorSensor, UltrasonicSensor, ForceSensor
from pybricks.parameters import Button, Color, Direction, Port, Side, Stop
from pybricks.robotics import DriveBase
from pybricks.tools import wait, StopWatch
from pybricks.iodevices import UARTDevice
from ComunicacaoSerialJSONSpike import ComunicacaoSerialJSON
hub = PrimeHub()
comunicacao = ComunicacaoSerialJSON(Port.A)
motor1 = Motor(Port.E)
motor2 = Motor(Port.F)
portDebug = UARTDevice(Port.C)

cronometro = StopWatch()
i=0
cronometro.reset()

# while(True):
#     portDebug.write("a")
#     print(portDebug.read_all())
#     wait(100)  

#Assim envia
while(True):
    
    cronometro.reset()
    #print("motores:", motor1.angle(),motor2.angle())
    #print("imu:", hub.imu.tilt(), hub.imu.heading())
    #coloco todos os valores que quero enviar
    comunicacao.definirAtributo("angX",int(hub.imu.tilt()[0]))
    comunicacao.definirAtributo("angY",int(hub.imu.tilt()[1]))
    comunicacao.definirAtributo("angZ",int(hub.imu.heading()))
    comunicacao.definirAtributo("m1Ang",motor1.angle())
    comunicacao.definirAtributo("m2Ang",motor2.angle())
    #faço a atualizaçao da comunicacao (envio e recebo)
    comunicacao.atualizar()

    #agora atualizo tudo do brick que foi recebido
    
    velMotor1 = comunicacao.obterAtributo("velM1")
    if(velMotor1 is not None):
        velMotor1 = int(velMotor1)
        motor1.run(velMotor1)
    velMotor2 = comunicacao.obterAtributo("velM2")
    if(velMotor2 is not None):
        velMotor2 = int(velMotor2)
        motor2.run(velMotor2)
    if(comunicacao.existeAtributo("resZ")): #mando resetar o eixo Z
        hub.imu.reset_heading(0)
        print("Giroscopio resetado")
    if(comunicacao.tempoDesdeUltimaComunicacao() is None):
        print("nunca recebi dados")
    elif(comunicacao.tempoDesdeUltimaComunicacao() > 3): #isso serve para evitar que caso dê alguma desconexão, 
    #o spike nao fique andando loucamente com os motores ligados por muito tempo
        motor1.stop()
        motor2.stop()
        print("motores desligados por falta de comunicacao")
    else:
        print(comunicacao.tempoDesdeUltimaComunicacao())
    #atualizacao a cada 30ms (mais que suficiente)
    while(cronometro.time() < 30):
        continue

