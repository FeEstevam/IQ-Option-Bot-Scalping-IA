# 🤖 IQ Option Bot — Scalping + IA (Google Gemini)

Bot automatizado de opções binárias para a plataforma **IQ Option**, com análise técnica local e validação opcional por **Inteligência Artificial (Google Gemini)**. Interface gráfica moderna construída com `customtkinter`.

---

## ✨ Funcionalidades

- 📊 **Análise técnica local** com EMA 9, EMA 21, WMA 5 e RSI 14
- 🧠 **Validação por IA** — envia os últimos 20 candles ao Google Gemini para confirmar ou bloquear o sinal
- 🎛️ **Interface gráfica** intuitiva em modo escuro (Dark)
- ⚡ **Fallback automático** para pares OTC quando o mercado principal está fechado
- 📈 **Placar em tempo real** com contagem de WINS, LOSS e lucro acumulado
- 🛑 **Filtragem por confiança** — a IA só aprova entradas com confiança ≥ 75%
- 🔄 Suporte a **contas PRACTICE e REAL**
- ⏱️ Expiração configurável: 1, 2, 3, 4, 5 ou 15 minutos
- 📜 **Console de execução** com log timestampado em tempo real

---

## 🗂️ Estrutura do Projeto

```
ops/
├── interface.py   # Interface gráfica (CustomTkinter) e loop principal do bot
├── bot.py         # Lógica de análise técnica, consulta à IA e execução de ordens
├── script.lua     # Script de indicadores para visualização em plataformas de gráfico
└── README.md
```

---

## 🧠 Estratégia de Trading

### Indicadores utilizados

| Indicador | Configuração | Função |
|-----------|-------------|--------|
| **EMA 9** | Período 9 | Média rápida (sinal) |
| **EMA 21** | Período 21 | Média lenta (tendência) |
| **WMA 5** | Período 5 | Linha guia (direção do momento) |
| **RSI 14** | Período 14 | Filtro de sobrecompra/sobrevenda |

### Lógica de entrada

**CALL (compra):**
- Linha guia virou para cima + RSI entre 48 e 75, **ou**
- EMA rápida > EMA lenta + linha guia ascendente + candle de alta ou preço acima da EMA 9 + RSI entre 50 e 72

**PUT (venda):**
- Linha guia virou para baixo + RSI entre 25 e 52, **ou**
- EMA rápida < EMA lenta + linha guia descendente + candle de baixa ou preço abaixo da EMA 9 + RSI entre 28 e 50

### Validação por IA (opcional)

Quando ativada, o bot envia os últimos 20 candles com os indicadores calculados ao **Google Gemini**, que analisa:
1. Padrões de preço e estrutura dos candles
2. Estado da tendência (definida ou lateral)
3. Confirmação ou contradição do sinal técnico local

A IA retorna `CALL`, `PUT` ou `AGUARDAR` com um nível de **confiança de 0 a 100%**. Entradas com confiança abaixo de **75%** são bloqueadas automaticamente.

---

## 🚀 Instalação

### Pré-requisitos

- Python 3.9+
- Conta na [IQ Option](https://iqoption.com)
- *(Opcional)* Chave de API do [Google AI Studio](https://aistudio.google.com/apikey) para usar a validação por IA

### Dependências

```bash
pip install customtkinter pandas numpy iqoptionapi google-generativeai
```

> **Nota:** O pacote `google-generativeai` é necessário apenas se for usar a validação por IA.

---

## ▶️ Como usar

1. Execute a interface:
   ```bash
   python interface.py
   ```

2. Preencha os campos:
   - **E-mail** e **Senha** da sua conta IQ Option
   - **Paridade** (ex: `EURUSD`, `EURUSD-OTC`, `AUDCAD`)
   - **Valor da entrada** em dólares
   - **Tipo de conta:** `PRACTICE` (demo) ou `REAL`
   - **Expiração da ordem:** 1 a 15 minutos

3. *(Opcional)* Ative a **Validação por IA**, cole sua Gemini API Key e o bot passará a confirmar cada sinal com o Gemini antes de abrir uma ordem.

4. Clique em **▶ INICIAR BOT** e acompanhe o console de execução em tempo real.

5. Clique em **⏹ PARAR BOT** para encerrar com segurança.

---

## 📊 Script Lua (Indicadores Visuais)

O arquivo `script.lua` é um script de indicadores para plataformas de gráfico compatíveis com Lua. Ele plota visualmente:

- **Linha Guia** (WMA 5) em verde/vermelho conforme a direção
- **EMA Rápida** (9) em azul-ciano
- **EMA Lenta** (21) em amarelo
- **Setas de CALL** (triângulo verde abaixo da barra)
- **Setas de PUT** (triângulo vermelho acima da barra)

Útil para validar visualmente a estratégia antes de usar o bot.

---

## ⚠️ Aviso Legal

> **ATENÇÃO:** Este bot é um projeto de estudo/pesquisa. Opções binárias envolvem alto risco de perda financeira. Use **exclusivamente em conta PRACTICE** até entender completamente o comportamento da estratégia. O autor não se responsabiliza por eventuais perdas financeiras decorrentes do uso deste software.

---

## 🛠️ Tecnologias

- [Python](https://python.org) — linguagem principal
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) — interface gráfica moderna
- [iqoptionapi](https://github.com/Lu-Yi-Hsun/iqoptionapi) — integração com a IQ Option
- [Pandas](https://pandas.pydata.org) / [NumPy](https://numpy.org) — cálculo dos indicadores
- [Google Generative AI](https://ai.google.dev) — validação dos sinais via Gemini
