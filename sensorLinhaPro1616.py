from pybricks.iodevices import UARTDevice
import math
import threading
import time

try:
    import json
except ImportError:
    import ujson as json


class SensorLinhaPro:
    """Biblioteca de comunicação com o sensor de linha Pro1616 para EV3.

    Layout dos 16 bytes recebidos do sensor:
      [0-3]:   Reflexão IR dos 4 sensores. Escala do firmware: 0 = preto, ~100 = branco
               calibrado. A fita prata lê MENOS que o branco no IR (~80): o IR não serve
               para achar o prata.
      [4-7]:   Sensor de cor TCS1       (R, G, B, C)
      [8-11]:  Sensor de cor TCS meio   (R, G, B, C)
      [12-15]: Sensor de cor TCS2       (R, G, B, C)
      O TCS é calibrado no branco e o firmware envia METADE do valor: branco ~127, o que
      deixa folga até 255 para superfícies refletivas (a fita prata passa de 127).

    Comunicação binária: envia 1 byte de comando, recebe 16 bytes de dados.

    Detecção de cor
    ---------------
    Cada cor é uma referência (média e desvio) de até cinco características:
      cromaticidade r/(r+g+b), g/(r+g+b), b/(r+g+b)  -> a cor em si, independe do brilho
      brilho C / 127                                  -> branco = 1, prata > 1, preto ~ 0
      IR / 100 (só com usar_ir=True)                  -> branco = 1, prata ~0,8, preto ~ 0
    O IR vem DESLIGADO por padrão: a fileira de IR fica uns 9 mm à frente dos TCS e, na borda da
    linha e nas curvas, o IR já está no branco enquanto o TCS ainda está no preto.
    A leitura vai para a referência mais próxima (distância medida em desvios). Se nenhuma
    estiver perto o bastante, o resultado é COR_DESCONHECIDA.

    As referências padrão são só um ponto de partida. No tempo de calibração, coloque o
    robô sobre cada cor e chame aprende_cor('verde') etc.; salve com salva_cores() e
    carregue com carrega_cores() (ou passe arquivo_cores no construtor).

        sensor = SensorLinhaPro(Port.S1, arquivo_cores='cores.json')
        sensor.usa_cores(['branco', 'preto', 'prata', 'verde', 'vermelho'])
        sensor.aprende_cor('verde')           # robô parado com os 3 TCS sobre o verde
        sensor.salva_cores('cores.json')
        sensor.cor(2)                         # 'verde'  (TCS do meio)
        sensor.cor_piso()                     # votação dos 3 TCS
        sensor.detecta_cor(2)                 # mesma coisa, como constante COR_*
    """

    # Modos do sensor (comandos enviados ao Arduino)
    MODO_CALIBRADO = 0x61
    MODO_CALIBRA_BRANCO = 0x62
    MODO_CALIBRA_PRETO = 0x63

    # Cores (PRATA é nova)
    COR_NADA = -1
    COR_PRETO = 0
    COR_BRANCO = 1
    COR_VERMELHO = 2
    COR_VERDE = 3
    COR_AZUL = 4
    COR_AMARELO = 5
    COR_DESCONHECIDA = 6
    COR_PRATA = 7

    NOMES_CORES = {
        -1: "nada",
        0: "preto",
        1: "branco",
        2: "vermelho",
        3: "verde",
        4: "azul",
        5: "amarelo",
        6: "desconhecida",
        7: "prata",
    }
    CODIGO_COR = {v: k for k, v in NOMES_CORES.items()}

    # Referências padrão na escala do firmware: (R, G, B, C) do TCS e IR. Estimativas!
    REFERENCIAS_PADRAO = {
        "branco":   ((127, 128, 126, 127), 100),
        "preto":    ((3, 3, 4, 5), 2),
        "prata":    ((190, 195, 200, 205), 80),
        "azul":     ((20, 45, 115, 66), 70),
        "vermelho": ((115, 25, 22, 58), 85),
        "verde":    ((30, 85, 45, 62), 75),
        "amarelo":  ((125, 115, 35, 110), 95),
    }
    # desvio mínimo de cada característica (cr, cg, cb, brilho, ir)
    DESVIO_MINIMO = (0.03, 0.03, 0.03, 0.08, 0.08)
    # abaixo deste brilho (escala 0-255) a cromaticidade é só ruído e não pesa
    BRILHO_MINIMO_COR = 15
    # IR que fica do lado de cada TCS: TCS1 -> IR 0, meio -> IR 1 e 2, TCS2 -> IR 3
    IR_DO_TCS = {1: (0,), 2: (1, 2), 3: (3,)}

    _QTD_VALORES = 16

    # Mapeamento sensor (1,2,3) → índice base na lista de valores
    _OFFSET_COR = {1: 4, 2: 8, 3: 12}

    def __init__(self, porta, baudrate=115200, intervalo=0.03,
                 arquivo_cores=None, limiar=6.0, usar_ir=False):
        """
        Args:
            porta: Porta do EV3 (Port.S1, Port.S2, etc.)
            baudrate: Velocidade serial (padrão 115200, igual ao sensor)
            intervalo: Intervalo entre leituras em segundos (~33 Hz padrão)
            arquivo_cores: JSON com referências aprendidas (opcional)
            limiar: distância máxima (em desvios) para aceitar uma cor
            usar_ir: considera também a reflexão IR na classificação de cor (padrão False,
                ver a explicação no início da classe)
        """
        self.serial = UARTDevice(porta, baudrate, 100)
        self.lista = [0] * self._QTD_VALORES
        self.limiar = limiar
        self.usar_ir = usar_ir
        self.referencias = {}
        for nome, (rgbc, ir) in self.REFERENCIAS_PADRAO.items():
            self.referencias[nome] = (self.caracteristicas(rgbc, ir), self.DESVIO_MINIMO)
        if arquivo_cores:
            self.carrega_cores(arquivo_cores)
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
                self.serial.write(bytes([self.MODO_CALIBRADO]))
                buf = b""
                inicio = time.time()
                while len(buf) < self._QTD_VALORES and time.time() - inicio < 0.15:
                    trecho = self._ler_disponivel()
                    if trecho:
                        buf += trecho
                    else:
                        time.sleep(0.005)

                if len(buf) >= self._QTD_VALORES:
                    # troca a lista inteira de uma vez: IR e TCS sempre do mesmo quadro
                    self.lista = list(buf[0:self._QTD_VALORES])
                    self._conectado = True
                    self._ultimo_tempo = time.time()

            except Exception:
                self._conectado = False

            time.sleep(self._intervalo)

    # ── Propriedades gerais ─────────────────────────────────────────────

    @property
    def conectado(self):
        """True se o sensor respondeu nos últimos 2 segundos."""
        return self._conectado and (time.time() - self._ultimo_tempo < 2)

    @property
    def valores(self):
        """Retorna cópia dos 16 valores brutos do sensor."""
        return list(self.lista)

    # ── Reflexão IR (índices 0-3) ───────────────────────────────────────

    def reflexao(self, sensor):
        """Valor de reflexão do sensor IR (0-3): 0 = preto, ~100 = branco; prata ~80."""
        if 0 <= sensor <= 3:
            return self.lista[sensor]
        return 0

    def le_reflexao(self):
        """Retorna lista com os 4 valores de reflexão IR."""
        return self.lista[0:4]

    # ── Cor RGBC (sensor: 1=TCS1, 2=TCS meio, 3=TCS2) ──────────────────

    def le_rgbc(self, sensor):
        """Retorna [R, G, B, C] do sensor de cor (1=TCS1, 2=TCS meio, 3=TCS2). Branco ~127."""
        base = self._OFFSET_COR.get(sensor)
        if base is not None:
            return self.lista[base:base + 4]
        return None

    def le_rgb(self, sensor):
        """Retorna [R, G, B] do sensor de cor (1=TCS1, 2=TCS meio, 3=TCS2)."""
        base = self._OFFSET_COR.get(sensor)
        if base is not None:
            return self.lista[base:base + 3]
        return None

    def le_hsv(self, sensor):
        """Retorna [H, S, V] do sensor de cor (1=TCS1, 2=TCS meio, 3=TCS2).
        H: 0-360, S: 0-100, V: 0-100."""
        rgb = self.le_rgb(sensor)
        if rgb is not None:
            return list(self.rgb_para_hsv(rgb[0], rgb[1], rgb[2]))
        return None

    def le_hsv120(self, sensor, valor_maximo=127):
        """Retorna [H, S, V] do sensor de cor (1=TCS1, 2=TCS meio, 3=TCS2).
        H: 0-120, S: 0-120, V: 0-120"""
        rgb = self.le_rgb(sensor)
        if rgb is not None:
            return list(self.rgb_para_hsv120(rgb[0], rgb[1], rgb[2], valor_maximo))
        return None

    # ── Calibração ──────────────────────────────────────────────────────

    def calibra_branco(self, timeout_ms=10000):
        """Solicita calibração do branco. Retorna True se confirmada."""
        return self._executar_calibracao(self.MODO_CALIBRA_BRANCO, timeout_ms)

    def calibra_preto(self, timeout_ms=5000):
        """Solicita calibração do preto. Retorna True se confirmada."""
        return self._executar_calibracao(self.MODO_CALIBRA_PRETO, timeout_ms)

    def _executar_calibracao(self, modo, timeout_ms):
        self._pausado = True
        time.sleep(0.15)
        try:
            self._ler_disponivel()
        except Exception:
            pass
        self.serial.write(bytes([modo]))
        resultado = False
        inicio = time.time()
        while (time.time() - inicio) * 1000 < timeout_ms:
            try:
                dados = self._ler_disponivel()
                if dados and 1 in dados:
                    resultado = True
                    break
            except Exception:
                pass
            time.sleep(0.2)
        self._pausado = False
        return resultado

    # ── Conversão RGB → HSV ─────────────────────────────────────────────

    @staticmethod
    def rgb_para_hsv(r, g, b):
        """Converte RGB (0-255) para HSV.
        Retorna (H: 0-360, S: 0-100, V: 0-100)."""
        #preciso colocar o valor para 0-255 e garantir q o maximo é 255 para evitar erros de leitura
        r = r*2
        g = g*2
        b = b*2
        if r > 255:
            r = 255
        if g > 255:
            g = 255
        if b > 255:
            b = 255
        r_n = r / 255.0
        g_n = g / 255.0
        b_n = b / 255.0

        cmax = max(r_n, g_n, b_n)
        cmin = min(r_n, g_n, b_n)
        delta = cmax - cmin

        if delta == 0:
            h = 0.0
        elif cmax == r_n:
            h = 60.0 * (((g_n - b_n) / delta) % 6)
        elif cmax == g_n:
            h = 60.0 * (((b_n - r_n) / delta) + 2)
        else:
            h = 60.0 * (((r_n - g_n) / delta) + 4)
        if h < 0:
            h += 360.0

        s = 0.0 if cmax == 0 else (delta / cmax) * 100.0
        v = cmax * 100.0

        return (round(h), round(s), round(v))

    @staticmethod
    def rgb_para_hsv120(r, g, b, valor_maximo=127):
        """Converte RGB para HSV na escala 0-120 (estilo Paint clássico do Windows).
        Retorna (H: 0-120, S: 0-120, V: 0-120).
        valor_maximo: valor de referência para normalização (padrão 127)."""
        if r > valor_maximo:
            r = valor_maximo
        if g > valor_maximo:
            g = valor_maximo
        if b > valor_maximo:
            b = valor_maximo
        r_n = min(r / valor_maximo, 1.0)
        g_n = min(g / valor_maximo, 1.0)
        b_n = min(b / valor_maximo, 1.0)

        cmax = max(r_n, g_n, b_n)
        cmin = min(r_n, g_n, b_n)
        delta = cmax - cmin

        if delta == 0:
            h = 0
        elif cmax == r_n:
            h = int(60 * ((g_n - b_n) / delta + 6)) % 360
        elif cmax == g_n:
            h = int(60 * ((b_n - r_n) / delta + 2))
        else:
            h = int(60 * ((r_n - g_n) / delta + 4))

        # Mapeia Hue de [0, 360] para [0, 120]
        h = h * 120 // 360

        s = int((delta / cmax) * 120) if cmax != 0 else 0
        v = int(cmax * 120)

        return (h, s, v)

    # ── Detecção de cor por referências ─────────────────────────────────

    @staticmethod
    def caracteristicas(rgbc, ir):
        """(cr, cg, cb, brilho, ir): cromaticidade e valores relativos ao branco calibrado."""
        r, g, b, c = (float(x) for x in rgbc)
        s = r + g + b
        if s <= 0:
            cr = cg = cb = 1.0 / 3
        else:
            cr, cg, cb = r / s, g / s, b / s
        return (cr, cg, cb, c / 127.0, float(ir) / 100.0)

    def _distancia(self, f, referencia):
        media, desvio = referencia
        pesa_cor = min(f[3], media[3]) * 127.0 >= self.BRILHO_MINIMO_COR
        soma = 0.0
        for i in range(5):
            if i < 3 and not pesa_cor:
                continue
            if i == 4 and not self.usar_ir:
                continue
            soma += ((f[i] - media[i]) / desvio[i]) ** 2
        return math.sqrt(soma)

    def _leitura(self, sensor):
        lista = self.lista
        base = self._OFFSET_COR[sensor]
        idx = self.IR_DO_TCS[sensor]
        ir = sum(lista[i] for i in idx) / len(idx)
        return self.caracteristicas(lista[base:base + 4], ir)

    def distancias(self, sensor=2):
        """Lista [(distância, nome)] ordenada; útil para depurar e ajustar o limiar."""
        f = self._leitura(sensor)
        return sorted((self._distancia(f, ref), nome) for nome, ref in self.referencias.items())

    def cor(self, sensor=2):
        """Nome da cor no sensor (1=TCS1, 2=TCS meio, 3=TCS2) ou 'desconhecida'."""
        d = self.distancias(sensor)
        if not d:
            return "desconhecida"
        dist, nome = d[0]
        return nome if dist <= self.limiar else "desconhecida"

    def cores(self):
        """Nome da cor nos três TCS: [TCS1, meio, TCS2]."""
        return [self.cor(s) for s in (1, 2, 3)]

    def cor_piso(self):
        """Votação dos três TCS; sem maioria, vale o do meio."""
        v = self.cores()
        for nome in set(v):
            if v.count(nome) >= 2:
                return nome
        return v[1]

    def detecta_cor(self, sensor):
        """Cor no sensor (1=TCS1, 2=TCS meio, 3=TCS2) como constante COR_*."""
        if sensor not in self._OFFSET_COR:
            return self.COR_NADA
        if not self.conectado and not any(self.lista):
            return self.COR_NADA
        return self.CODIGO_COR.get(self.cor(sensor), self.COR_DESCONHECIDA)

    def nome_cor(self, sensor):
        """Retorna nome da cor detectada pelo sensor (1, 2 ou 3)."""
        return self.NOMES_CORES.get(self.detecta_cor(sensor), "desconhecida")

    def detectar_cor(self, r, g, b, c, ir=None):
        """Classifica um RGBC avulso (escala do firmware, branco ~127). Retorna constante COR_*.
        Sem IR, usa só cromaticidade e brilho."""
        f = self.caracteristicas((r, g, b, c), 100 if ir is None else ir)
        usar_ir = self.usar_ir
        self.usar_ir = usar_ir and ir is not None
        try:
            d = sorted((self._distancia(f, ref), nome) for nome, ref in self.referencias.items())
        finally:
            self.usar_ir = usar_ir
        if not d or d[0][0] > self.limiar:
            return self.COR_DESCONHECIDA
        return self.CODIGO_COR.get(d[0][1], self.COR_DESCONHECIDA)

    # ── Referências de cor (calibração no campo) ────────────────────────

    def usa_cores(self, nomes):
        """Mantém só as cores listadas (ex.: na Maze não há verde nem amarelo)."""
        self.referencias = {n: r for n, r in self.referencias.items() if n in nomes}
        for n in nomes:
            if n not in self.referencias and n in self.REFERENCIAS_PADRAO:
                rgbc, ir = self.REFERENCIAS_PADRAO[n]
                self.referencias[n] = (self.caracteristicas(rgbc, ir), self.DESVIO_MINIMO)

    def aprende_cor(self, nome, amostras=25, intervalo=0.03, sensores=(1, 2, 3)):
        """Robô parado com os sensores sobre a cor `nome`: lê várias vezes e grava a
        referência (média e 2 desvios de folga). Retorna (media, desvio)."""
        fs = []
        for _ in range(amostras):
            for s in sensores:
                fs.append(self._leitura(s))
            time.sleep(intervalo)
        n = len(fs)
        media = tuple(sum(f[i] for f in fs) / n for i in range(5))
        desvio = tuple(
            max(2.0 * math.sqrt(sum((f[i] - media[i]) ** 2 for f in fs) / max(1, n - 1)),
                self.DESVIO_MINIMO[i])
            for i in range(5))
        self.referencias[nome] = (media, desvio)
        return self.referencias[nome]

    def esquece_cor(self, nome):
        self.referencias.pop(nome, None)

    def salva_cores(self, arquivo="cores.json"):
        dados = {}
        for n, (m, d) in self.referencias.items():
            dados[n] = {"media": list(m), "desvio": list(d)}
        with open(arquivo, "w") as f:
            json.dump(dados, f)

    def carrega_cores(self, arquivo="cores.json"):
        """Carrega referências salvas. Retorna False se o arquivo não existir."""
        try:
            with open(arquivo) as f:
                dados = json.load(f)
        except (OSError, ValueError):
            return False
        for nome, r in dados.items():
            desvio = tuple(max(d, m) for d, m in zip(r["desvio"], self.DESVIO_MINIMO))
            self.referencias[nome] = (tuple(r["media"]), desvio)
        return True

    # ── Controle ────────────────────────────────────────────────────────

    def fechar(self):
        """Para a thread de leitura."""
        self._executando = False
