import time
from comunicacaoPython import ComunicacaoSerialJSON

# Teste de comunicação serial JSON no PC
# Altere a porta serial conforme necessário (ex: "COM3" no Windows ou "/dev/ttyUSB0" no Linux)
PORTA = "COM7"

comunicacao = ComunicacaoSerialJSON(PORTA, baudrate=115200)

i = 0
try:
    while True:
        angX = comunicacao.obterAtributo("angX")
        if(angX is not None):
            print("recebi o angX", angX)
            comunicacao.definirAtributo("velM1", angX * 15)
        else:
            comunicacao.definirAtributo("velM1", 0)
        angY = comunicacao.obterAtributo("angY")
        if(angY is not None):
            print("recebi o angY", angY)
            comunicacao.definirAtributo("velM2", angY * 15)
        else:
            comunicacao.definirAtributo("velM2", 0)
        m1Ang = comunicacao.obterAtributo("m1Ang")
        if(m1Ang is not None):
            print("recebi o m1Ang", m1Ang)
        m2Ang = comunicacao.obterAtributo("m2Ang")
        if(m2Ang is not None):
            print("recebi o m2Ang", m2Ang)
        time.sleep(0.03)
finally:
    comunicacao.fechar()
