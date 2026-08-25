from pybricks.iodevices import UARTDevice
import threading
import time
import struct


class PlacaMuxVl53l0xTCS34725:
    """Biblioteca de comunicação (EV3/Pybricks) com a placa mux que combina
    o servo motor da porta 0 (conector 1) e o sensor de distância (VL53L0X)
    da porta 1 (conector 2) com 2 sensores de cor (TCS34725) nas portas 2 e 3
    (conectores 3 e 4 da placa), além dos 4 botões (BT_1 a BT_4).

    Layout dos 14 valores (int16, 2 bytes cada, 28 bytes no total)
    recebidos da placa:
      [0]      ângulo do servo motor porta 0 (conector 1)
      [1]      distância porta 1 (VL53L0X - conector 2)
      [2..5]   r, g, b, c da porta 2 (TCS34725 - conector 3)
      [6..9]   r, g, b, c da porta 3 (TCS34725 - conector 4)
      [10..13] botões BT_1, BT_2, BT_3, BT_4

    Comunicação binária: envia 1 byte de comando ('A'), recebe 28 bytes de
    dados; ou envia 1 byte de comando ('B' + ângulo) para mover o servo, sem
    resposta da placa.
    """

    # Comando enviado à placa (igual ao DISTANCIA_4_PORTAS do firmware)
    LEITURA_TODAS_PORTAS = ord('A')
    # + ângulo (0 a 180) define a posição do servo (igual ao CARACTERE_SERVO_PORTA1 do firmware)
    CARACTERE_SERVO_PORTA1 = ord('B')

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
        self._angulo_pendente = None

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
                # sem lock: MicroPython (EV3) nao possui threading.Lock, entao
                # apenas lemos e zeramos a variavel (troca atomica em CPython/MicroPython)
                angulo = self._angulo_pendente
                self._angulo_pendente = None

                if angulo is not None:
                    # a placa não envia resposta para o comando de servo
                    self.serial.write(bytes([self.CARACTERE_SERVO_PORTA1 + angulo]))
                    self.lista[0] = angulo
                else:
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

    # ── Servo motor (porta 0 - conector 1) ────────────────────────

    def movimenta_servo(self, angulo):
        """Define o ângulo (0 a 180) do servo motor da porta 0 (conector 1)."""
        angulo = max(0, min(180, int(angulo)))
        self._angulo_pendente = angulo

    def le_angulo_servo(self):
        """Retorna o último ângulo do servo motor (porta 0) reportado pela placa."""
        return self.lista[0]

    # ── Sensor de distância (porta 1 - VL53L0X) ──────────────

    def le_distancia(self, porta=1):
        """Lê a distância (mm) da porta 1 (sensor VL53L0X - conector 2)."""
        if porta != 1:
            raise ValueError('Porta inválida. Apenas a porta 1 (conector 2) possui sensor de distância (VL53L0X).')
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
