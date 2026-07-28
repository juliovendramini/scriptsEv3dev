from pybricks.iodevices import UARTDevice
import threading
import time
import struct


class PlacaMuxVl53l0xTCS34725:
    """Biblioteca de comunicação (EV3/Pybricks) com a placa mux que combina
    2 sensores de distância (VL53L0X) nas portas 0 e 1 (conectores 1 e 2
    da placa) com 2 sensores de cor (TCS34725) nas portas 2 e 3 (conectores
    3 e 4 da placa), além dos 4 botões (BT_1 a BT_4).

    Layout dos 14 valores (int16, 2 bytes cada, 28 bytes no total)
    recebidos da placa:
      [0]      distância porta 0 (VL53L0X - conector 1)
      [1]      distância porta 1 (VL53L0X - conector 2)
      [2..5]   r, g, b, c da porta 2 (TCS34725 - conector 3)
      [6..9]   r, g, b, c da porta 3 (TCS34725 - conector 4)
      [10..13] botões BT_1, BT_2, BT_3, BT_4

    Comunicação binária: envia 1 byte de comando ('A'), recebe 28 bytes de dados.
    """

    # Comando enviado à placa (igual ao DISTANCIA_4_PORTAS do firmware)
    LEITURA_TODAS_PORTAS = ord('A')

    _QTD_VALORES = 14
    _QTD_BYTES = _QTD_VALORES * 2  # 28 bytes

    def __init__(self, porta, baudrate=115200, intervalo=0.05):
        """
        Args:
            porta: Porta do EV3 (Port.S1, Port.S2, etc.)
            baudrate: Velocidade serial (padrão 115200, igual à placa)
            intervalo: Intervalo entre leituras em segundos (padrão 50ms)
        """
        self.serial = UARTDevice(porta, baudrate, 100)
        self.lista = [0] * self._QTD_VALORES
        self._conectado = False
        self._executando = True
        self._pausado = False
        self._intervalo = intervalo
        self._ultimo_tempo = 0

        self._thread = threading.Thread(target=self._loop_leitura)
        self._thread.daemon = True
        self._thread.start()

    # ── Leitura serial interna ──────────────────────────────────────────

    def _ler_disponivel(self):
        """Lê todos os bytes disponíveis no buffer serial."""
        n = self.serial.waiting()
        if n > 0:
            return self.serial.read(n)
        return b""

    def _loop_leitura(self):
        while self._executando:
            if self._pausado:
                time.sleep(0.05)
                continue
            try:
                self._ler_disponivel()
                self.serial.write(bytes([self.LEITURA_TODAS_PORTAS]))
                buf = b""
                inicio = time.time()
                while len(buf) < self._QTD_BYTES and time.time() - inicio < 0.15:
                    trecho = self._ler_disponivel()
                    if trecho:
                        buf += trecho
                    else:
                        time.sleep(0.005)

                if len(buf) >= self._QTD_BYTES:
                    for i in range(self._QTD_VALORES):
                        self.lista[i] = struct.unpack('>h', buf[i * 2 : i * 2 + 2])[0]
                    self._conectado = True
                    self._ultimo_tempo = time.time()

            except Exception:
                self._conectado = False

            time.sleep(self._intervalo)

    # ── Propriedades gerais ─────────────────────────────────────────────

    @property
    def conectado(self):
        """True se a placa respondeu nos últimos 2 segundos."""
        return self._conectado and (time.time() - self._ultimo_tempo < 2)

    @property
    def valores(self):
        """Retorna cópia dos 14 valores brutos recebidos da placa."""
        return list(self.lista)

    # ── Sensores de distância (portas 0 e 1 - VL53L0X) ──────────────────

    def le_distancia(self, porta):
        """Lê a distância (mm) das portas 0 e 1 (sensores VL53L0X)."""
        if porta < 0 or porta > 1:
            raise ValueError('Porta inválida. As portas 0 e 1 são sensores de distância (VL53L0X).')
        return self.lista[porta]

    # ── Sensores de cor (portas 2 e 3 - TCS34725) ───────────────────────

    def le_cor(self, porta):
        """Retorna (r, g, b, c) das portas 2 e 3 (sensores TCS34725)."""
        if porta < 2 or porta > 3:
            raise ValueError('Porta inválida. As portas 2 e 3 são sensores de cor (TCS34725).')
        base = 2 + (porta - 2) * 4
        return tuple(self.lista[base : base + 4])

    # ── Botões (portas 0 a 3 - BT_1 a BT_4) ─────────────────────────────

    def botao_apertado(self, porta):
        """Lê o estado (True/False) dos botões BT_1 a BT_4 (portas 0 a 3)."""
        if porta < 0 or porta > 3:
            raise ValueError('Porta inválida. Deve ser 0, 1, 2 ou 3.')
        return self.lista[10 + porta] == 1

    # ── Controle ──────────────────────────────────────────────────────

    def fechar(self):
        """Para a thread de leitura."""
        self._executando = False
