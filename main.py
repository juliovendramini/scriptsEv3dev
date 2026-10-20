#!/usr/bin/env pybricks-micropython
# =============================================================================
#  Exemplo completo do sensor de linha/cor Pro1616 no EV3 (Pybricks / ev3dev)
# =============================================================================
#
#  Arquivos que precisam estar JUNTOS na mesma pasta do EV3:
#    main.py                 (este arquivo)
#    sensorLinhaPro1616.py   (a biblioteca do sensor)
#
#  Ligação: cabo do sensor na porta de SENSOR S1 do EV3 (pode trocar abaixo).
#  Motores: roda esquerda na porta B, roda direita na porta C.
#
#  O que o sensor manda (16 números, ~33 vezes por segundo):
#    - 4 reflexões infravermelhas (IR), da esquerda para a direita:
#          0 = preto, ~100 = branco calibrado (a fita prata dá ~80, MENOS que o branco)
#    - 3 sensores de cor TCS34725 (1 = esquerda, 2 = meio, 3 = direita), cada um com
#      R, G, B e C (C = "claridade", a luz total). Branco calibrado dá ~127 em tudo.
#      A fita prata reflete mais que o branco: o C dela passa de ~160.
#    - A fileira de IR fica uns 9 mm À FRENTE da fileira de cor.
#
#  O programa abre um MENU (use CIMA/BAIXO para escolher e o botão do MEIO para entrar):
#    1. Valores brutos   -> mostra os 16 números na tela
#    2. Cor por HSV      -> classifica a cor com Matiz/Saturação/Brilho
#    3. Cores aprendidas -> ensina as cores do campo para a biblioteca e salva
#    4. Calibrar         -> calibra branco e preto no próprio sensor
#    5. Seguir linha PID -> segue a linha com PID na reflexão IR, vira no verde,
#                           para no vermelho
#  Dentro de qualquer modo, o botão ESQUERDA volta para o menu.
#
#  Os números das constantes (velocidade, PID, limiares de cor) são um PONTO DE
#  PARTIDA: cada robô e cada pista pede um ajuste. Use os modos 1 e 2 para olhar os
#  valores de verdade antes de mexer.
# =============================================================================

from pybricks.hubs import EV3Brick
from pybricks.ev3devices import Motor
from pybricks.parameters import Port, Button, Direction
from pybricks.tools import wait, StopWatch

from sensorLinhaPro1616 import SensorLinhaPro


# -----------------------------------------------------------------------------
#  Configuração do robô
# -----------------------------------------------------------------------------

PORTA_SENSOR = Port.S1

# intervalo=0.01: pede leitura ao sensor a cada ~10 ms (o padrão é 30 ms).
# Para seguir linha, quanto mais leituras por segundo, melhor.
# arquivo_cores: onde ficam guardadas as cores aprendidas no modo 3.
ARQUIVO_CORES = "cores.json"

ev3 = EV3Brick()
sensor = SensorLinhaPro(PORTA_SENSOR, intervalo=0.01, arquivo_cores=ARQUIVO_CORES)

# Se o robô andar para trás quando devia ir para frente, troque para
# Direction.COUNTERCLOCKWISE (depende de como os motores foram montados).
motor_esq = Motor(Port.B, positive_direction=Direction.CLOCKWISE)
motor_dir = Motor(Port.C, positive_direction=Direction.CLOCKWISE)

# Medidas do robô, usadas para girar e andar uma distância certa (em milímetros).
DIAMETRO_RODA = 56        # roda padrão do EV3: 56 mm
DISTANCIA_RODAS = 120     # de centro a centro dos pneus, meça no seu robô

# Quantos graus cada roda precisa girar para o ROBÔ girar 1 grau no lugar.
# Girando no lugar, cada roda anda num círculo com diâmetro = DISTANCIA_RODAS,
# então: graus_roda = graus_robo * DISTANCIA_RODAS / DIAMETRO_RODA
GRAUS_RODA_POR_GRAU_ROBO = DISTANCIA_RODAS / DIAMETRO_RODA


# -----------------------------------------------------------------------------
#  Funções de ajuda: tela, botões e movimento
# -----------------------------------------------------------------------------

def tela(*linhas):
    """Limpa a tela e escreve cada texto numa linha (cabem umas 8 linhas)."""
    ev3.screen.clear()
    for i, texto in enumerate(linhas):
        ev3.screen.draw_text(0, i * 16, texto)


def botao_apertado():
    """Devolve o botão apertado (ou None). Espera soltar, para não contar duas vezes."""
    apertados = ev3.buttons.pressed()
    if not apertados:
        return None
    while ev3.buttons.pressed():
        wait(10)
    return apertados[0]


def limita(valor, maximo):
    """Prende o valor entre -maximo e +maximo."""
    return max(-maximo, min(maximo, valor))


def parar_motores():
    motor_esq.brake()
    motor_dir.brake()


def girar(graus_robo, velocidade=250):
    """Gira o robô no lugar. graus_robo positivo = para a DIREITA."""
    graus_roda = graus_robo * GRAUS_RODA_POR_GRAU_ROBO
    motor_esq.run_angle(velocidade, graus_roda, wait=False)
    motor_dir.run_angle(velocidade, -graus_roda)   # este espera terminar


def andar_mm(mm, velocidade=250):
    """Anda reto uma distância em milímetros (negativo = para trás)."""
    # uma volta da roda (360 graus) anda o perímetro: pi * diâmetro
    graus_roda = mm * 360 / (3.1416 * DIAMETRO_RODA)
    motor_esq.run_angle(velocidade, graus_roda, wait=False)
    motor_dir.run_angle(velocidade, graus_roda)


# -----------------------------------------------------------------------------
#  Cor por HSV
# -----------------------------------------------------------------------------
#
#  HSV separa a cor em três números:
#    H (matiz, 0-360): QUAL é a cor, como um ângulo numa roda de cores
#         0 = vermelho, 60 = amarelo, 120 = verde, 240 = azul, 360 = vermelho de novo
#    S (saturação, 0-100): o quanto a cor é "forte". Branco, cinza, preto e prata
#         têm S baixo (não têm cor); verde e vermelho de fita têm S alto.
#    V (brilho, 0-100): o quanto é claro. Preto tem V baixo.
#
#  A vantagem: o H de uma fita verde quase não muda se a luz ficar mais forte ou
#  mais fraca; só o V muda. Por isso comparar H é mais fácil que comparar R, G e B.
#
#  sensor.le_hsv(n) já faz a conta. Na biblioteca o RGB é dobrado antes (para o
#  branco calibrado ~127 virar ~255), então o branco dá V perto de 100.
#  Existe também sensor.le_hsv120(n), com tudo na escala 0-120 (igual ao Paint).
#
#  Os limites abaixo são um exemplo. Olhe no modo 2 os valores da SUA pista e ajuste.

V_PRETO = 20          # V abaixo disto: preto
S_SEM_COR = 25        # S abaixo disto: não tem cor (branco, cinza ou prata)
V_BRANCO = 60         # sem cor e V acima disto: branco
C_PRATA = 165         # sem cor e C (claridade bruta) acima disto: prata

# faixas de matiz (H) de cada cor: (de, até)
FAIXAS_H = (
    ("vermelho", 330, 360),
    ("vermelho", 0, 20),
    ("amarelo", 20, 75),
    ("verde", 75, 170),
    ("azul", 170, 270),
)


def cor_por_hsv(n):
    """Cor no sensor de cor n (1 = esquerda, 2 = meio, 3 = direita) usando HSV."""
    h, s, v = sensor.le_hsv(n)
    c = sensor.le_rgbc(n)[3]          # claridade bruta (branco ~127, prata > 160)

    if v < V_PRETO:
        return "preto"
    if s < S_SEM_COR:
        # sem cor: decide pelo brilho
        if c > C_PRATA:
            return "prata"         # a prata reflete MAIS que o branco
        if v > V_BRANCO:
            return "branco"
        return "cinza"             # meio a meio: borda da linha, por exemplo
    for nome, de, ate in FAIXAS_H:
        if de <= h < ate:
            return nome
    return "desconhecida"


# -----------------------------------------------------------------------------
#  Posição da linha usando os 4 IR
# -----------------------------------------------------------------------------
#
#  Ideia: cada IR "vota" na posição dele, com peso igual ao quanto ele vê de preto.
#    IR:      0      1      2      3        (esquerda -> direita)
#    peso:  -150    -50    +50   +150
#  Linha embaixo dos dois IR do meio  -> posição ~0
#  Linha embaixo do IR 3 (direita)    -> posição ~+150
#  Linha embaixo do IR 0 (esquerda)   -> posição ~-150
#  Isso é a "média ponderada" (o mesmo cálculo do getPosicaoLinha() do Arduino).
#
#  Se seu robô estiver com o sensor girado (IR 0 na direita), troque os sinais.

PESOS_IR = (-150, -50, 50, 150)
ESCURO_MINIMO = 40    # soma do "escuro" dos 4 IR abaixo disto = não tem linha embaixo


def posicao_linha():
    """Posição da linha de -150 (esquerda) a +150 (direita), ou None se não achou linha."""
    reflexoes = sensor.le_reflexao()
    # transforma reflexão (0 preto, 100 branco) em "escuro" (0 branco, 100 preto)
    escuro = [100 - min(r, 100) for r in reflexoes]
    total = sum(escuro)
    if total < ESCURO_MINIMO:
        return None
    soma = 0
    for peso, e in zip(PESOS_IR, escuro):
        soma += peso * e
    return soma / total


# -----------------------------------------------------------------------------
#  Modo 1: valores brutos
# -----------------------------------------------------------------------------

def modo_valores_brutos():
    while botao_apertado() != Button.LEFT:
        ir = sensor.le_reflexao()
        tela(
            "IR: {} {} {} {}".format(ir[0], ir[1], ir[2], ir[3]),
            "     R   G   B   C",
            "1: {:3} {:3} {:3} {:3}".format(*sensor.le_rgbc(1)),
            "2: {:3} {:3} {:3} {:3}".format(*sensor.le_rgbc(2)),
            "3: {:3} {:3} {:3} {:3}".format(*sensor.le_rgbc(3)),
            "conectado: {}".format(sensor.conectado),
            "pos linha: {}".format(posicao_linha()),
            "ESQUERDA = voltar",
        )
        wait(100)    # atualizar a tela mais rápido que isso só faz piscar


# -----------------------------------------------------------------------------
#  Modo 2: cor por HSV
# -----------------------------------------------------------------------------

def modo_cor_hsv():
    while botao_apertado() != Button.LEFT:
        linhas = ["   H   S   V  cor"]
        for n in (1, 2, 3):
            h, s, v = sensor.le_hsv(n)
            linhas.append("{}:{:3} {:3} {:3} {}".format(n, h, s, v, cor_por_hsv(n)[:8]))
        linhas.append("")
        linhas.append("Anote o H de cada fita")
        linhas.append("e ajuste FAIXAS_H.")
        linhas.append("ESQUERDA = voltar")
        tela(*linhas)
        # print aparece no terminal do VS Code: bom para anotar os números
        print([sensor.le_hsv(n) for n in (1, 2, 3)])
        wait(150)


# -----------------------------------------------------------------------------
#  Modo 3: cores aprendidas (classificador da biblioteca)
# -----------------------------------------------------------------------------
#
#  A biblioteca também sabe classificar cores sozinha: sensor.cor(n).
#  Ela guarda uma "referência" para cada cor (como a cor é e o quanto ela varia) e
#  devolve a mais parecida. Já vem com valores padrão, mas fica MUITO melhor se você
#  ensinar as cores da pista de verdade:
#     1. coloque os 3 sensores de cor em cima da cor (robô parado)
#     2. sensor.aprende_cor('verde')     -> lê 25 vezes e guarda
#     3. sensor.salva_cores('cores.json') -> grava no EV3; na próxima vez o
#        SensorLinhaPro(..., arquivo_cores='cores.json') já carrega sozinho
#  Funções úteis:
#     sensor.cor(n)         -> 'verde', 'preto', ... ou 'desconhecida'
#     sensor.cores()        -> as 3 de uma vez: [esquerda, meio, direita]
#     sensor.cor_piso()     -> votação dos 3 (sem maioria vale o do meio)
#     sensor.distancias(n)  -> [(distância, nome), ...]: quanto menor, mais parecido.
#                              Acima de sensor.limiar (6) vira 'desconhecida'.
#     sensor.usa_cores([...]) -> só considera essas cores (menos chance de errar)

CORES_DA_PISTA = ["branco", "preto", "prata", "verde", "vermelho"]


def modo_cores_aprendidas():
    sensor.usa_cores(CORES_DA_PISTA)
    escolhida = 0
    while True:
        b = botao_apertado()
        if b == Button.LEFT:
            return
        if b == Button.UP:
            escolhida = (escolhida + 1) % len(CORES_DA_PISTA)
        if b == Button.CENTER:
            nome = CORES_DA_PISTA[escolhida]
            tela("Aprendendo " + nome, "nao mexa no robo...")
            sensor.aprende_cor(nome)
            ev3.speaker.beep()
        if b == Button.DOWN:
            sensor.salva_cores(ARQUIVO_CORES)
            tela("Salvo em", ARQUIVO_CORES)
            ev3.speaker.beep(800)
            wait(800)

        dist, mais_perto = sensor.distancias(2)[0]
        tela(
            # [:6] corta o nome para caber na tela ('descon' = desconhecida)
            " ".join(nome[:6] for nome in sensor.cores()),
            "Piso: " + sensor.cor_piso(),
            "Meio: {} ({:.1f})".format(mais_perto, dist),
            "",
            "Ensinar: " + CORES_DA_PISTA[escolhida],
            "CIMA troca  MEIO ensina",
            "BAIXO salva",
            "ESQUERDA = voltar",
        )
        wait(100)


# -----------------------------------------------------------------------------
#  Modo 4: calibração do sensor
# -----------------------------------------------------------------------------
#
#  A calibração fica gravada DENTRO do sensor (não precisa repetir toda vez).
#  Branco: todos os IR e os 3 sensores de cor sobre o branco. Leva uns 7 segundos.
#  Preto:  os IR sobre o preto.

def modo_calibrar():
    for cor, funcao in (("BRANCO", sensor.calibra_branco), ("PRETO", sensor.calibra_preto)):
        tela("Coloque sobre o " + cor, "", "MEIO = calibrar", "ESQUERDA = pular")
        while True:
            b = botao_apertado()
            if b == Button.CENTER:
                tela("Calibrando " + cor + "...")
                ok = funcao()
                tela(cor + (": OK" if ok else ": FALHOU"))
                ev3.speaker.beep(1000 if ok else 200, 300)
                wait(1000)
                break
            if b == Button.LEFT:
                break
            wait(20)


# -----------------------------------------------------------------------------
#  Modo 5: seguir linha com PID
# -----------------------------------------------------------------------------
#
#  ERRO = onde a linha está (posicao_linha): 0 = no centro, + = linha à direita.
#  O PID calcula uma CORREÇÃO a partir do erro:
#
#    P (proporcional): correção = KP * erro
#        quanto mais longe a linha, mais forte a curva. Só com P o robô costuma
#        "zigue-zaguear": aumente KP até ele seguir as curvas, sem exagerar.
#    D (derivativo):   correção += KD * (erro - erro_anterior)
#        olha se o erro está aumentando ou diminuindo; funciona como um freio que
#        acalma o zigue-zague. Depois de achar o KP, aumente KD aos poucos.
#    I (integral):     correção += KI * soma_de_todos_os_erros
#        corrige um erro pequeno que fica sempre para o mesmo lado. Em seguidor de
#        linha quase não é preciso: comece com KI = 0.
#
#  Depois aplicamos nos motores:
#    roda esquerda = VELOCIDADE + correção
#    roda direita  = VELOCIDADE - correção
#  Linha à direita (erro +) -> esquerda mais rápida -> robô vira para a direita.

VELOCIDADE = 250      # graus/s de cada roda na reta
VELOCIDADE_MAXIMA = 700
KP = 1.6
KI = 0.0
KD = 6.0
LIMITE_INTEGRAL = 3000    # impede a integral de crescer sem fim

# Quantas leituras seguidas a cor precisa aparecer para acreditarmos nela.
# Evita falso verde/vermelho na borda da linha, onde o sensor vê metade preto.
CONFIRMA_COR = 3

# Escolha o jeito de reconhecer as cores na pista:
#   True  -> cor_por_hsv() deste arquivo (limites que você ajusta à mão)
#   False -> sensor.cor() da biblioteca (cores aprendidas no modo 3)
USAR_HSV = True


def cor_do_sensor(n):
    if USAR_HSV:
        return cor_por_hsv(n)
    return sensor.cor(n)


def curva_no_verde(verde_esq, verde_dir):
    """Ideia da regra do verde (Rescue Line): o verde fica antes do cruzamento e
    diz para que lado virar. Verde dos dois lados = beco sem saída: meia-volta."""
    parar_motores()
    ev3.speaker.beep(1200, 100)
    andar_mm(60)                    # avança até o meio do cruzamento (ajuste)
    if verde_esq and verde_dir:
        girar(180)
    elif verde_esq:
        girar(-90)
    else:
        girar(90)
    andar_mm(20)                    # sai de cima do verde antes de voltar ao PID


def modo_seguir_linha():
    tela("Seguindo linha...", "", "ESQUERDA = parar")
    erro_anterior = 0
    integral = 0
    conta_verde_esq = 0
    conta_verde_dir = 0
    conta_vermelho = 0
    voltas = 0
    cronometro = StopWatch()

    while not Button.LEFT in ev3.buttons.pressed():
        # ---------- 1. cores: verde nas laterais, vermelho no meio ----------
        cor_esq = cor_do_sensor(1)
        cor_dir = cor_do_sensor(3)
        conta_verde_esq = conta_verde_esq + 1 if cor_esq == "verde" else 0
        conta_verde_dir = conta_verde_dir + 1 if cor_dir == "verde" else 0
        conta_vermelho = conta_vermelho + 1 if cor_do_sensor(2) == "vermelho" else 0

        if conta_vermelho >= CONFIRMA_COR:
            # fim da pista (exemplo): para e avisa
            parar_motores()
            ev3.speaker.beep(400, 600)
            tela("Vermelho: fim!")
            wait(1500)
            return

        if conta_verde_esq >= CONFIRMA_COR or conta_verde_dir >= CONFIRMA_COR:
            # um dos lados confirmou: olha o outro de novo (pode ser verde duplo)
            curva_no_verde(cor_esq == "verde", cor_dir == "verde")
            conta_verde_esq = conta_verde_dir = 0
            erro_anterior = 0
            integral = 0
            continue

        # ---------- 2. erro: onde está a linha ----------
        posicao = posicao_linha()
        if posicao is None:
            # Perdeu a linha. Se ela estava quase no centro, provavelmente é um
            # "gap" (falha na linha): segue reto. Se estava num canto, foi uma curva
            # fechada: força a curva para o lado onde a linha foi vista por último.
            if abs(erro_anterior) < 60:
                erro = 0
            else:
                erro = 150 if erro_anterior > 0 else -150
        else:
            erro = posicao

        # ---------- 3. PID ----------
        integral += erro
        integral = limita(integral, LIMITE_INTEGRAL)
        derivada = erro - erro_anterior
        correcao = KP * erro + KI * integral + KD * derivada
        erro_anterior = erro

        # ---------- 4. motores ----------
        # limita a velocidade: o motor grande do EV3 não passa muito de ~800 graus/s
        # e um pico do D (linha que "pula" de lugar) não deve virar um tranco.
        motor_esq.run(limita(VELOCIDADE + correcao, VELOCIDADE_MAXIMA))
        motor_dir.run(limita(VELOCIDADE - correcao, VELOCIDADE_MAXIMA))

        voltas += 1
        wait(10)    # ~100 vezes por segundo (o sensor atualiza a cada ~10 ms)

    parar_motores()
    segundos = cronometro.time() / 1000
    if segundos > 0:
        print("PID rodou a {:.0f} vezes por segundo".format(voltas / segundos))


# -----------------------------------------------------------------------------
#  Menu principal
# -----------------------------------------------------------------------------

MODOS = (
    ("Valores brutos", modo_valores_brutos),
    ("Cor por HSV", modo_cor_hsv),
    ("Cores aprendidas", modo_cores_aprendidas),
    ("Calibrar", modo_calibrar),
    ("Seguir linha PID", modo_seguir_linha),
)


def esperar_sensor():
    """Espera o sensor responder (até 5 s)."""
    tela("Procurando sensor...")
    relogio = StopWatch()
    while not sensor.conectado:
        if relogio.time() > 5000:
            tela("Sensor nao responde!", "", "Confira o cabo na", "porta S1.")
            ev3.speaker.beep(200, 800)
            while not sensor.conectado:
                wait(100)
        wait(50)
    ev3.speaker.beep()


def main():
    esperar_sensor()
    escolhido = 0
    while True:
        linhas = []
        for i, (nome, _) in enumerate(MODOS):
            marcador = ">" if i == escolhido else " "
            linhas.append("{} {}. {}".format(marcador, i + 1, nome))
        linhas.append("")
        linhas.append("MEIO = entrar")
        tela(*linhas)

        b = botao_apertado()
        if b == Button.UP:
            escolhido = (escolhido - 1) % len(MODOS)
        elif b == Button.DOWN:
            escolhido = (escolhido + 1) % len(MODOS)
        elif b == Button.CENTER:
            MODOS[escolhido][1]()      # chama a função do modo escolhido
            parar_motores()
        wait(50)


main()
