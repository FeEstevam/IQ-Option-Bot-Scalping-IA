instrument { name = "Estratégia Scalping 30s (EMA + RSI + Guia)", overlay = true }

-- Parâmetros de Entrada
ema_fast_len = input (9, "EMA Rápida (Sinal)", input.integer, 1)
ema_slow_len = input (21, "EMA Lenta (Tendência)", input.integer, 1)
trend_len = input (5, "Período da Linha Guia", input.integer, 1)

rsi_len = input (14, "Período RSI", input.integer, 1)
rsi_ob = input (70, "Sobrecompra RSI", input.integer, 50, 95)
rsi_os = input (30, "Sobrevenda RSI", input.integer, 5, 50)

bull_color = input ("#00E676", "Cor Alta / Compra", input.color)
bear_color = input ("#FF1744", "Cor Baixa / Venda", input.color)
ema_fast_color = input ("#00E5FF", "Cor EMA Rápida", input.color)
ema_slow_color = input ("#FFD600", "Cor EMA Lenta", input.color)

-- Médias Móveis e Indicadores
local ema_fast = ema(close, ema_fast_len)
local ema_slow = ema(close, ema_slow_len)
local trend_line = wma(close, trend_len)
local rsi_val = rsi(close, rsi_len)

-- Linha Seguidora (Alta / Baixa)
local is_up = trend_line >= trend_line[1]
local trend_line_color = iff(is_up, bull_color, bear_color)

-- Plotagem das Linhas
plot(trend_line, "Linha Guia", trend_line_color, 3)
plot(ema_fast, "EMA Rápida", ema_fast_color, 1)
plot(ema_slow, "EMA Lenta", ema_slow_color, 2)

-- Condições de Compra e Venda
local trend_bull = ema_fast > ema_slow and is_up
local trend_bear = ema_fast < ema_slow and not is_up

local trend_turned_up = trend_line > trend_line[1] and trend_line[1] <= trend_line[2]
local trend_turned_down = trend_line < trend_line[1] and trend_line[1] >= trend_line[2]

local candle_bull = close > open and close > high[1]
local candle_bear = close < open and close < low[1]

local buy_signal = (trend_turned_up or (trend_bull and candle_bull and low <= ema_fast and close > ema_fast)) and (rsi_val > 50 and rsi_val < rsi_ob)
local sell_signal = (trend_turned_down or (trend_bear and candle_bear and high >= ema_fast and close < ema_fast)) and (rsi_val < 50 and rsi_val > rsi_os)

-- Sinais Visuais no Gráfico
plot_shape(buy_signal, "Compra CALL", shape_style.triangleup, shape_size.large, bull_color, shape_location.belowbar)
plot_shape(sell_signal, "Venda PUT", shape_style.triangledown, shape_size.large, bear_color, shape_location.abovebar)