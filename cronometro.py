import time
import os

class Cronometro:
    # se a criação do cronometro for sem nome de arquivo, ele não salva o tempo em arquivos
    # essa situação é utilizaza para cronometros temporarios
    def __init__(self, nomeArquivo = None):
        self.nomeArquivo = nomeArquivo
        self.tempo_inicial = None

    def iniciar(self):
        self.tempo_inicial = time.time()

    def resetar(self):
        self.tempo_inicial = time.time()
        # apago o arquivo do cronometro
        if(self.nomeArquivo != None):
            temp = "rm " + str(self.nomeArquivo)
            os.system(str(temp))

    def tempoDecorrido(self):
        return (time.time() - self.tempo_inicial)


    def salvarTempo(self):
        if(self.nomeArquivo != None):
            with open(self.nomeArquivo, 'w') as f:
                f.write(str(self.tempo_inicial))

    def carregarTempo(self):
        if(self.nomeArquivo != None):
            try:
                with open(self.nomeArquivo, 'r') as f:
                    self.tempo_inicial = float(f.read())
            except:
                self.tempo_inicial = time.time()
        self.rodando = True

