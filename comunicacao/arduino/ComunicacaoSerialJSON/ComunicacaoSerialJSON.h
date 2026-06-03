#pragma once
#include <Arduino.h>
#include <ArduinoJson.h>  // Requer ArduinoJson v6: https://arduinojson.org/

/*
  ComunicacaoSerialJSON - Biblioteca Arduino para comunicação serial JSON.
  Compatível com os robôs LEGO EV3 e Spike Prime usando as libs comunicacaoEV3.py
  e comunicacaoSpike.py.

  Protocolo: mensagens JSON terminadas com '\n'.
  Ex: {"sensor":42,"botao":true}\n

  Uso básico:
    ComunicacaoSerialJSON comm(Serial1);   // porta serial conectada ao EV3/Spike

    void loop() {
      comm.atualizar();                          // chamar sempre no loop
      comm.definirAtributo("sensor", analogRead(A0));
      int val = comm.obterAtributoInt("led");
    }
*/

#ifndef COMM_MAX_ATRIBUTOS
#define COMM_MAX_ATRIBUTOS 16     // máximo de atributos simultâneos
#endif

#ifndef COMM_MAX_CHAVE
#define COMM_MAX_CHAVE 32         // tamanho máximo do nome de um atributo
#endif

#ifndef COMM_DOC_SIZE
#define COMM_DOC_SIZE 512         // tamanho do documento JSON interno
#endif

class ComunicacaoSerialJSON {
public:
    // serial      : porta serial (Serial, Serial1, Serial2, SoftwareSerial, etc.)
    // tempoAtributo: tempo em ms sem atualização para considerar atributo expirado
    ComunicacaoSerialJSON(Stream& serial, unsigned long tempoAtributo = 2000);

    // Deve ser chamado no loop() principal para processar envio e recebimento
    void atualizar();

    // Define um atributo para ser enviado na próxima chamada de atualizar()
    void definirAtributo(const char* chave, int valor);
    void definirAtributo(const char* chave, long valor);
    void definirAtributo(const char* chave, float valor);
    void definirAtributo(const char* chave, bool valor);
    void definirAtributo(const char* chave, const char* valor);
    void definirAtributo(const char* chave, const String& valor);

    // Obtém e consome o valor de um atributo recebido.
    // Retorna valorPadrao se o atributo não existe ou expirou.
    int    obterAtributoInt   (const char* chave, int valorPadrao = 0);
    long   obterAtributoLong  (const char* chave, long valorPadrao = 0L);
    float  obterAtributoFloat (const char* chave, float valorPadrao = 0.0f);
    bool   obterAtributoBool  (const char* chave, bool valorPadrao = false);
    String obterAtributoString(const char* chave, const char* valorPadrao = "");

    // Retorna true se o atributo foi recebido e ainda não expirou
    bool existeAtributo(const char* chave);

    // Bloqueia chamando atualizar() até o atributo chegar ou timeout (ms) estourar.
    // Retorna true se o atributo chegou a tempo.
    bool aguardarAtributo(const char* chave, unsigned long timeout = 2000);

private:
    Stream&       _serial;
    String        _bufferRecebido;
    unsigned long _tempoAtributo;

    StaticJsonDocument<COMM_DOC_SIZE> _docRecebido;
    StaticJsonDocument<COMM_DOC_SIZE> _docEnviar;

    struct Timestamp {
        char          chave[COMM_MAX_CHAVE];
        unsigned long tempo;
    };
    Timestamp _tempos[COMM_MAX_ATRIBUTOS];
    int       _numTempos;

    void _registrarTempo(const char* chave);
    bool _dentroDoTimeout(const char* chave) const;
    void _processarLinha(const String& linha);
    void _expirarAtributos();
};
