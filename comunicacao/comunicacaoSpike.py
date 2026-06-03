from pybricks.iodevices import UARTDevice
from pybricks.tools import wait, StopWatch
import ujson as json

''' Essa classe implementa a comunicação serial com o Spike usando JSON.
    Chame atualizar() regularmente no loop principal para processar envio e recebimento.
'''
class ComunicacaoSerialJSON:
    def __init__(self, porta, baudrate=115200, tempoAtributo=2):
        self.serial = UARTDevice(porta, baudrate, 20)
        self._atributos = {}
        self._temposAtributos = {}
        self._atributosEnviar = {}
        self._tempoAtributo = tempoAtributo * 1000  # em milissegundos
        self._buffer_recebido = b""
        self._ultimaComunicacao = None
        self._relogio = StopWatch()

    def atualizar(self):
        # receber
        try:
            dados = self.serial.read_all()
            if dados:
                self._buffer_recebido += dados
                while b'\n' in self._buffer_recebido:
                    linha, self._buffer_recebido = self._buffer_recebido.split(b'\n', 1)
                    print(linha)
                    if linha:
                        try:
                            linha = linha.strip()
                            obj = json.loads(linha)
                            self._ultimaComunicacao = self._relogio.time()
                            for chave, valor in obj.items():
                                self._atributos[chave] = valor
                                self._temposAtributos[chave] = self._ultimaComunicacao
                        except Exception:
                            print("erro Exception 1")
                            pass
        except Exception:
            print("erro Exception 2")
            pass

        # enviar
        if self._atributosEnviar:
            try:
                mensagem = json.dumps(self._atributosEnviar) + '\n'
                self.serial.write(mensagem)
                self._atributosEnviar.clear()
            except Exception:
                print("erro Exception 3")
                pass

        # timeout
        agora = self._relogio.time()
        for chave in list(self._atributos.keys()):
            if agora - self._temposAtributos.get(chave, 0) > self._tempoAtributo:
                self._atributos[chave] = None


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
        inicio = self._relogio.time()
        while self._relogio.time() - inicio < timeout * 1000:
            self.atualizar()
            valor = self.obterAtributo(chave)
            if valor is not None:
                return valor
            wait(100)
        return None

    #retorna True se o atributo existe e não é None
    def existeAtributo(self, chave):
        return chave in self._atributos and self._atributos[chave] is not None

    def tempoDesdeUltimaComunicacao(self):
        """Retorna em segundos quanto tempo faz desde a última comunicação recebida, ou None se nunca recebeu."""
        if self._ultimaComunicacao is None:
            return None
        return (self._relogio.time() - self._ultimaComunicacao) / 1000

    def fechar(self):
        self._executando = False
        # UARTDevice não possui método close, mas threads serão finalizadas

    def __getitem__(self, chave):
        return self.obterAtributo(chave)

    def __setitem__(self, chave, valor):
        self.definirAtributo(chave, valor)