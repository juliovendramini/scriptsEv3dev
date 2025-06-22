from pybricks.iodevices import UARTDevice
import threading
import json
import time
''' Essa classe implementa a comunicação serial com o EV3 usando JSON.
    Ela permite enviar e receber atributos de forma assíncrona, com suporte a timeout
    para atributos que não são recebidos em um determinado período.
    A classe utiliza threads para receber dados da porta serial, enviar dados e gerenciar timeouts.
    Ela simplifica o processo de comunicação serial, permitindo que os atributos sejam definidos e obtidos sem preocupação com o sincronismo da comunicação.
'''
class ComunicacaoSerialJSON:
    def __init__(self, porta, baudrate=115200, tempoAtributo=2):
        self.serial = UARTDevice(porta, baudrate, 20)
        self._atributos = {}
        self._temposAtributos = {}
        self._atributosEnviar = {}
        self._tempoAtributo = tempoAtributo
        self._executando = True
        self._buffer_recebido = b""

        self._threadReceber = threading.Thread(target=self._loopReceber)
        self._threadReceber.start()

        self._threadTimeout = threading.Thread(target=self._loopTimeout)
        self._threadTimeout.start()

        self._threadEnviar = threading.Thread(target=self._loopEnviar)
        self._threadEnviar.start()

    def _loopReceber(self):
        while self._executando:
            try:
                dados = self.serial.read_all()
                if dados:
                    self._buffer_recebido += dados
                    while b'\n' in self._buffer_recebido:
                        linha, self._buffer_recebido = self._buffer_recebido.split(b'\n', 1)
                        if linha:
                            try:
                                obj = json.loads(linha.decode())
                                for chave, valor in obj.items():
                                    self._atributos[chave] = valor
                                    self._temposAtributos[chave] = time.time()
                            except Exception:
                                pass
            except Exception:
                pass

    def _loopEnviar(self):
        while self._executando:
            if self._atributosEnviar:
                try:
                    mensagem = json.dumps(self._atributosEnviar) + '\n'
                    self.serial.write(mensagem.encode())
                    self._atributosEnviar.clear()
                except Exception:
                    pass
            time.sleep(0.05)

    def _loopTimeout(self):
        while self._executando:
            agora = time.time()
            for chave in list(self._atributos.keys()):
                if agora - self._temposAtributos.get(chave, 0) > self._tempoAtributo:
                    self._atributos[chave] = None
            time.sleep(2)


    def definirAtributo(self, chave, valor):
        self._atributosEnviar[chave] = valor


    def obterAtributo(self, chave):
        x = self._atributos.get(chave, None)
        if x is not None:
            self._atributos[chave] = None
        return x

    #aguarda até que o atributo esteja disponível ou o timeout seja atingido
    #retorna o valor do atributo se estiver disponível, ou None se o timeout for atingido
    def aguardarAtributo(self, chave, timeout=2): #tempo em segundos
        inicio = time.time()
        while time.time() - inicio < timeout:
            valor = self.obterAtributo(chave)
            if valor is not None:
                return valor
            time.sleep(0.1)
        return None

    #retorna True se o atributo existe e não é None
    def existeAtributo(self, chave):
        return chave in self._atributos and self._atributos[chave] is not None

    def fechar(self):
        self._executando = False
        # UARTDevice não possui método close, mas threads serão finalizadas

    def __getitem__(self, chave):
        return self.ObterAtributo(chave)

    def __setitem__(self, chave, valor):
        self.DefinirAtributo(chave, valor)