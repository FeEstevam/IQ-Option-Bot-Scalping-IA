import time
import json
import pandas as pd
import numpy as np

# ==========================================
# FUNÇÕES MATEMÁTICAS DOS INDICADORES
# ==========================================
def calc_ema(series, length):
    return series.ewm(span=length, adjust=False).mean()

def calc_wma(series, length):
    weights = np.arange(1, length + 1)
    return series.rolling(length).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)

def calc_rsi(series, length):
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1/length, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/length, adjust=False).mean()
    rs = avg_gain / (avg_loss + 1e-9)
    return 100 - (100 / (1 + rs))


# ==========================================
# ANÁLISE TÉCNICA (INDICADORES LOCAIS)
# ==========================================
def analisar_sinal(velas):
    """
    Analisa as velas e retorna sinal de compra/venda.
    Retorna: (sinal_str_ou_None, status_info_str, df_com_indicadores)
    """
    if not velas or len(velas) < 30:
        return None, "Aguardando mais velas...", None

    df = pd.DataFrame(velas)
    df.rename(columns={'max': 'high', 'min': 'low'}, inplace=True)

    df['ema_fast'] = calc_ema(df['close'], 9)
    df['ema_slow'] = calc_ema(df['close'], 21)
    df['trend_line'] = calc_wma(df['close'], 5)
    df['rsi'] = calc_rsi(df['close'], 14)

    if pd.isna(df['rsi'].iloc[-2]):
        return None, "Calculando indicadores...", None

    atual = df.iloc[-2]
    ant   = df.iloc[-3]
    ant2  = df.iloc[-4]

    is_up       = bool(atual['trend_line'] >= ant['trend_line'])
    turned_up   = bool(atual['trend_line'] > ant['trend_line'] and ant['trend_line'] <= ant2['trend_line'])
    turned_down = bool(atual['trend_line'] < ant['trend_line'] and ant['trend_line'] >= ant2['trend_line'])
    trend_bull  = bool(atual['ema_fast'] > atual['ema_slow'])
    trend_bear  = bool(atual['ema_fast'] < atual['ema_slow'])
    candle_bull = bool(atual['close'] > atual['open'] and atual['close'] > ant['high'])
    candle_bear = bool(atual['close'] < atual['open'] and atual['close'] < ant['low'])
    rsi_val     = float(atual['rsi'])

    buy = (turned_up and 48 < rsi_val < 75) or \
          (trend_bull and is_up and (candle_bull or atual['close'] > atual['ema_fast']) and 50 < rsi_val < 72)

    sell = (turned_down and 25 < rsi_val < 52) or \
           (trend_bear and not is_up and (candle_bear or atual['close'] < atual['ema_fast']) and 28 < rsi_val < 50)

    direcao = "ALTA 🟢" if is_up else "BAIXA 🔴"
    info = f"Guia: {direcao} | RSI: {rsi_val:.1f} | EMA9>{atual['ema_slow']:.5f}:{trend_bull}"

    if buy:
        return "call", info, df
    if sell:
        return "put", info, df
    return None, info, df


# ==========================================
# CONSULTA À IA (GOOGLE GEMINI)
# ==========================================
def consultar_ia(velas, sinal_tecnico, api_key, log_fn=None):
    """
    Envia os últimos 30 candles + indicadores para o Gemini 2.0 Flash.
    A IA valida se deve CALL, PUT ou AGUARDAR e retorna nível de confiança.

    Retorna: (decisao: str, confianca: int, motivo: str)
      - decisao  → "call" | "put" | "aguardar"
      - confianca → 0 a 100
      - motivo   → explicação textual da IA
    """
    FALLBACK = (sinal_tecnico, 100, "IA indisponível – usando análise técnica local.")

    if not api_key or not api_key.strip():
        return FALLBACK

    try:
        import google.generativeai as genai
    except ImportError:
        if log_fn:
            log_fn("⚠️ Pacote 'google-generativeai' não instalado. Execute: pip install google-generativeai")
        return FALLBACK

    try:
        genai.configure(api_key=api_key.strip())

        # Prepara os dados das últimas 30 velas para enviar à IA
        df = pd.DataFrame(velas[-30:])
        df.rename(columns={'max': 'high', 'min': 'low'}, inplace=True)
        df['ema9']  = calc_ema(df['close'], 9)
        df['ema21'] = calc_ema(df['close'], 21)
        df['rsi14'] = calc_rsi(df['close'], 14)

        candles_resumo = []
        for _, row in df.tail(20).iterrows():
            candles_resumo.append({
                "open":  round(float(row['open']),  5),
                "high":  round(float(row['high']),  5),
                "low":   round(float(row['low']),   5),
                "close": round(float(row['close']), 5),
                "ema9":  round(float(row['ema9']),  5) if not pd.isna(row['ema9'])  else None,
                "ema21": round(float(row['ema21']), 5) if not pd.isna(row['ema21']) else None,
                "rsi14": round(float(row['rsi14']), 2) if not pd.isna(row['rsi14']) else None,
            })

        prompt = f"""Você é um analista especialista em trading de opções binárias de curto prazo.
Analise os seguintes dados dos últimos 20 candles de 30 segundos com os indicadores EMA9, EMA21 e RSI14.

DADOS DOS CANDLES (do mais antigo para o mais recente):
{json.dumps(candles_resumo, indent=2)}

PRÉ-SINAL DOS INDICADORES TÉCNICOS LOCAIS: {sinal_tecnico.upper() if sinal_tecnico else 'NENHUM'}

Com base na estrutura dos candles, padrões de preço, cruzamentos de médias e nível de RSI, avalie:
1. Há um padrão claro de CALL (alta) ou PUT (baixa)?
2. O mercado está em tendência definida ou lateral/indeciso?
3. O pré-sinal técnico local é confirmado pelo contexto do gráfico?

Responda SOMENTE em JSON válido, sem texto adicional, no seguinte formato:
{{
  "decisao": "CALL" ou "PUT" ou "AGUARDAR",
  "confianca": <número inteiro de 0 a 100>,
  "motivo": "<explicação curta e objetiva em português, máx 120 caracteres>"
}}

REGRAS IMPORTANTES:
- Se RSI > 70 com tendência de alta: provável reversão, prefira AGUARDAR ou PUT
- Se RSI < 30 com tendência de baixa: provável reversão, prefira AGUARDAR ou CALL
- Se EMA9 cruzou EMA21 recentemente: sinal mais forte
- Se os últimos 3 candles são indecisivos (doji): AGUARDAR
- Só indique CALL ou PUT se confiança ≥ 60%"""

        model = genai.GenerativeModel("gemini-3.6-flash")
        resposta = model.generate_content(
            prompt,
            generation_config={"temperature": 0.1, "max_output_tokens": 256}
        )

        texto = resposta.text.strip()
        # Remove marcadores de código se a IA retornar ```json ... ```
        if texto.startswith("```"):
            texto = texto.split("```")[1]
            if texto.startswith("json"):
                texto = texto[4:]
        texto = texto.strip()

        dados = json.loads(texto)
        decisao   = str(dados.get("decisao", "AGUARDAR")).lower()
        confianca = int(dados.get("confianca", 0))
        motivo    = str(dados.get("motivo", ""))

        if decisao not in ("call", "put", "aguardar"):
            decisao = "aguardar"

        return decisao, confianca, motivo

    except json.JSONDecodeError:
        if log_fn:
            log_fn("⚠️ IA retornou formato inválido. Usando análise local.")
        return FALLBACK
    except Exception as e:
        if log_fn:
            log_fn(f"⚠️ Erro ao consultar IA: {e}")
        return FALLBACK


# ==========================================
# EXECUÇÃO DE ORDENS NA IQ OPTION
# ==========================================
def executar_ordem(api, valor, paridade, direcao, exp_min):
    """Tenta abrir a ordem. Retorna (sucesso, tipo_str, id_ou_None)."""
    exp_int = max(1, int(exp_min))
    pares = [paridade.upper()]
    if "-OTC" not in paridade.upper():
        pares.append(paridade.upper() + "-OTC")

    for p in pares:
        try:
            ok, oid = api.buy(valor, p, direcao, exp_int)
            if ok:
                return True, f"Binárias/{p}", oid
        except Exception:
            pass
        try:
            exp_d = 1 if exp_int < 5 else 5
            ok, oid = api.buy_digital_spot(p, valor, direcao, exp_d)
            if ok:
                return True, f"Digitais/{p}", oid
        except Exception:
            pass

    return False, "", None
