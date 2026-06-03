/*
  exemplo_basico.ino
  ==================
  Demonstra a comunicação entre Arduino e EV3 / Spike Prime
  usando a biblioteca ComunicacaoSerialJSON.

  Conexão física (Arduino Mega / Uno com nível 5V → 3.3V via divisor resistivo):
  ┌──────────┐         ┌──────────────────┐
  │ EV3/Spike│         │      Arduino     │
  │  TX  ────┼─────────┼─ RX (Serial1 19) │
  │  RX  ────┼─────────┼─ TX (Serial1 18) │
  │  GND ────┼─────────┼─ GND             │
  └──────────┘         └──────────────────┘

  ATENÇÃO: O EV3 e o Spike operam em 3.3 V.
  Use um divisor resistivo (1 kΩ + 2 kΩ) ou conversor de nível no TX do Arduino.

  Protocolo:
    - Ambos os lados enviam objetos JSON planos terminados com '\n'
    - Ex: {"sensor":512,"botao":false}\n

  Dependência: ArduinoJson v6  (Sketch → Gerenciar Bibliotecas → "ArduinoJson")
*/

#include <ComunicacaoSerialJSON.h>

// Porta serial usada para comunicar com o EV3 / Spike (não use Serial0 se quiser
// manter o Monitor Serial para debug).
// Em placas com apenas uma porta UART (Uno/Nano) use SoftwareSerial — veja abaixo.
ComunicacaoSerialJSON comm(Serial1, 2000);  // 2000 ms de timeout por atributo

// --- Pinos de exemplo ---
const int PIN_LED    = 13;
const int PIN_SENSOR = A0;

void setup() {
    Serial.begin(115200);   // debug via USB
    Serial1.begin(115200);  // comunicação com EV3 / Spike

    pinMode(PIN_LED, OUTPUT);

    Serial.println("Arduino pronto.");
}

void loop() {
    // 1. Atualizar comunicação (processar envio e recebimento)
    comm.atualizar();

    // 2. Enviar leitura do sensor analógico para o EV3 / Spike
    comm.definirAtributo("sensor", analogRead(PIN_SENSOR));

    // 3. Receber comando "led" e acionar o LED
    if (comm.existeAtributo("led")) {
        int estadoLed = comm.obterAtributoInt("led");
        digitalWrite(PIN_LED, estadoLed ? HIGH : LOW);
        Serial.print("LED: ");
        Serial.println(estadoLed);
    }

    // 4. Exemplo: aguardar o atributo "iniciar" por até 3 segundos (bloqueante)
    // if (comm.aguardarAtributo("iniciar", 3000)) {
    //     Serial.println("Recebeu 'iniciar'!");
    // }

    delay(50);  // ~20 Hz
}


// =============================================================================
// USANDO SoftwareSerial (para Uno / Nano que têm apenas uma UART)
// =============================================================================
// #include <SoftwareSerial.h>
// #include <ComunicacaoSerialJSON.h>
//
// SoftwareSerial swSerial(10, 11);  // RX=10, TX=11
// ComunicacaoSerialJSON comm(swSerial, 2000);
//
// void setup() {
//     Serial.begin(115200);
//     swSerial.begin(115200);  // SoftwareSerial suporta até 57600 com mais estabilidade
// }
