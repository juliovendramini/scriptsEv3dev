#include "ComunicacaoSerialJSON.h"
#include <string.h>

// ---------------------------------------------------------------------------
// Construtor
// ---------------------------------------------------------------------------
ComunicacaoSerialJSON::ComunicacaoSerialJSON(Stream& serial, unsigned long tempoAtributo)
    : _serial(serial), _tempoAtributo(tempoAtributo), _numTempos(0)
{
    _docRecebido.clear();
    _docEnviar.clear();
}

// ---------------------------------------------------------------------------
// Registro e verificação de timestamps por chave
// ---------------------------------------------------------------------------
void ComunicacaoSerialJSON::_registrarTempo(const char* chave) {
    // atualiza se já existe
    for (int i = 0; i < _numTempos; i++) {
        if (strncmp(_tempos[i].chave, chave, COMM_MAX_CHAVE) == 0) {
            _tempos[i].tempo = millis();
            return;
        }
    }
    // insere novo
    if (_numTempos < COMM_MAX_ATRIBUTOS) {
        strncpy(_tempos[_numTempos].chave, chave, COMM_MAX_CHAVE - 1);
        _tempos[_numTempos].chave[COMM_MAX_CHAVE - 1] = '\0';
        _tempos[_numTempos].tempo = millis();
        _numTempos++;
    }
}

bool ComunicacaoSerialJSON::_dentroDoTimeout(const char* chave) const {
    for (int i = 0; i < _numTempos; i++) {
        if (strncmp(_tempos[i].chave, chave, COMM_MAX_CHAVE) == 0) {
            return (millis() - _tempos[i].tempo) <= _tempoAtributo;
        }
    }
    return false;
}

// ---------------------------------------------------------------------------
// Processamento de uma linha JSON recebida
// ---------------------------------------------------------------------------
void ComunicacaoSerialJSON::_processarLinha(const String& linha) {
    StaticJsonDocument<COMM_DOC_SIZE> docTemp;
    DeserializationError erro = deserializeJson(docTemp, linha);
    if (erro) return;

    JsonObject obj = docTemp.as<JsonObject>();
    for (JsonPair kv : obj) {
        const char* chave = kv.key().c_str();
        _docRecebido[chave] = kv.value();
        _registrarTempo(chave);
    }
}

// ---------------------------------------------------------------------------
// Expiração de atributos sem atualização
// ---------------------------------------------------------------------------
void ComunicacaoSerialJSON::_expirarAtributos() {
    unsigned long agora = millis();
    for (int i = 0; i < _numTempos; i++) {
        if ((agora - _tempos[i].tempo) > _tempoAtributo) {
            _docRecebido.remove(_tempos[i].chave);
        }
    }
}

// ---------------------------------------------------------------------------
// atualizar() — chamar no loop()
// ---------------------------------------------------------------------------
void ComunicacaoSerialJSON::atualizar() {
    // receber
    while (_serial.available()) {
        char c = (char)_serial.read();
        if (c == '\r') continue;
        if (c == '\n') {
            _bufferRecebido.trim();
            if (_bufferRecebido.length() > 0) {
                _processarLinha(_bufferRecebido);
            }
            _bufferRecebido = "";
        } else {
            _bufferRecebido += c;
        }
    }

    // enviar
    if (_docEnviar.size() > 0) {
        serializeJson(_docEnviar, _serial);
        _serial.print('\n');
        _docEnviar.clear();
    }

    // expirar atributos antigos
    _expirarAtributos();
}

// ---------------------------------------------------------------------------
// definirAtributo — sobrecargas por tipo
// ---------------------------------------------------------------------------
void ComunicacaoSerialJSON::definirAtributo(const char* chave, int valor) {
    _docEnviar[chave] = valor;
}

void ComunicacaoSerialJSON::definirAtributo(const char* chave, long valor) {
    _docEnviar[chave] = valor;
}

void ComunicacaoSerialJSON::definirAtributo(const char* chave, float valor) {
    _docEnviar[chave] = valor;
}

void ComunicacaoSerialJSON::definirAtributo(const char* chave, bool valor) {
    _docEnviar[chave] = valor;
}

void ComunicacaoSerialJSON::definirAtributo(const char* chave, const char* valor) {
    _docEnviar[chave] = valor;
}

void ComunicacaoSerialJSON::definirAtributo(const char* chave, const String& valor) {
    _docEnviar[chave] = valor.c_str();
}

// ---------------------------------------------------------------------------
// existeAtributo
// ---------------------------------------------------------------------------
bool ComunicacaoSerialJSON::existeAtributo(const char* chave) {
    return _docRecebido.containsKey(chave) && _dentroDoTimeout(chave);
}

// ---------------------------------------------------------------------------
// obterAtributo* — obtém e consome o atributo
// ---------------------------------------------------------------------------
int ComunicacaoSerialJSON::obterAtributoInt(const char* chave, int valorPadrao) {
    if (!existeAtributo(chave)) return valorPadrao;
    int val = _docRecebido[chave].as<int>();
    _docRecebido.remove(chave);
    return val;
}

long ComunicacaoSerialJSON::obterAtributoLong(const char* chave, long valorPadrao) {
    if (!existeAtributo(chave)) return valorPadrao;
    long val = _docRecebido[chave].as<long>();
    _docRecebido.remove(chave);
    return val;
}

float ComunicacaoSerialJSON::obterAtributoFloat(const char* chave, float valorPadrao) {
    if (!existeAtributo(chave)) return valorPadrao;
    float val = _docRecebido[chave].as<float>();
    _docRecebido.remove(chave);
    return val;
}

bool ComunicacaoSerialJSON::obterAtributoBool(const char* chave, bool valorPadrao) {
    if (!existeAtributo(chave)) return valorPadrao;
    bool val = _docRecebido[chave].as<bool>();
    _docRecebido.remove(chave);
    return val;
}

String ComunicacaoSerialJSON::obterAtributoString(const char* chave, const char* valorPadrao) {
    if (!existeAtributo(chave)) return String(valorPadrao);
    String val = _docRecebido[chave].as<String>();
    _docRecebido.remove(chave);
    return val;
}

// ---------------------------------------------------------------------------
// aguardarAtributo — bloqueia até o atributo chegar ou timeout estourar
// ---------------------------------------------------------------------------
bool ComunicacaoSerialJSON::aguardarAtributo(const char* chave, unsigned long timeout) {
    unsigned long inicio = millis();
    while (millis() - inicio < timeout) {
        atualizar();
        if (existeAtributo(chave)) return true;
        delay(10);
    }
    return false;
}
