import customtkinter as ctk
import threading
import time
from iqoptionapi.stable_api import IQ_Option
from bot import analisar_sinal, executar_ordem, consultar_ia

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

CONFIANCA_MINIMA = 75  # % mínimo para executar a ordem via IA


class BotApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("IQ Option Bot  •  Scalping + IA")
        self.geometry("660x870")
        self.resizable(False, False)

        self.api        = None
        self.is_running = False
        self.wins       = 0
        self.losses     = 0
        self.lucro      = 0.0

        # ── Título ─────────────────────────────────────────────────────────
        ctk.CTkLabel(self, text="🤖  IQ Option Bot  •  Scalping + IA",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(14, 4))

        # ── Placar ─────────────────────────────────────────────────────────
        self.placar_frame = ctk.CTkFrame(self, fg_color="#181818", corner_radius=10)
        self.placar_frame.pack(padx=20, pady=(0, 6), fill="x")
        self.placar_label = ctk.CTkLabel(
            self.placar_frame,
            text="Placar: 0 WINS | 0 LOSS  |  Lucro: $0.00",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#00E676"
        )
        self.placar_label.pack(pady=8)

        # ── Formulário principal ────────────────────────────────────────────
        form = ctk.CTkFrame(self)
        form.pack(padx=20, pady=4, fill="both")

        def campo(row, col, label, **kwargs):
            ctk.CTkLabel(form, text=label,
                         font=ctk.CTkFont(size=12, weight="bold")
                         ).grid(row=row*2, column=col, padx=14, pady=(8,2), sticky="w")
            e = ctk.CTkEntry(form, width=258, **kwargs)
            e.grid(row=row*2+1, column=col, padx=14, pady=(0,10))
            return e

        self.email_e    = campo(0, 0, "E-mail da Conta")
        self.senha_e    = campo(0, 1, "Senha", show="*")
        self.paridade_e = campo(1, 1, "Paridade / Moeda")
        self.valor_e    = campo(2, 0, "Valor da Entrada ($)")

        self.email_e.insert(0, "amanda-cerqueira@tuamaeaquelaursa.com")
        self.senha_e.insert(0, "123123000")
        self.paridade_e.insert(0, "EURUSD-OTC")
        self.valor_e.insert(0, "2.0")

        # Conta (linha 1, col 0)
        ctk.CTkLabel(form, text="Tipo de Conta",
                     font=ctk.CTkFont(size=12, weight="bold")
                     ).grid(row=2, column=0, padx=14, pady=(8,2), sticky="w")
        self.conta_var = ctk.StringVar(value="PRACTICE")
        ctk.CTkOptionMenu(form, values=["PRACTICE", "REAL"],
                          variable=self.conta_var, width=258
                          ).grid(row=3, column=0, padx=14, pady=(0,10))

        # Expiração (linha 2, col 1)
        ctk.CTkLabel(form, text="Expiração da Ordem",
                     font=ctk.CTkFont(size=12, weight="bold")
                     ).grid(row=4, column=1, padx=14, pady=(8,2), sticky="w")
        self.exp_var = ctk.StringVar(value="1min")
        ctk.CTkOptionMenu(form, values=["1min","2min","3min","4min","5min","15min"],
                          variable=self.exp_var, width=258
                          ).grid(row=5, column=1, padx=14, pady=(0,10))

        # ── Seção IA ────────────────────────────────────────────────────────
        ia_frame = ctk.CTkFrame(self, fg_color="#0d1b2a", corner_radius=10,
                                border_width=1, border_color="#1e4d8c")
        ia_frame.pack(padx=20, pady=(4, 6), fill="x")

        # Cabeçalho IA
        header_ia = ctk.CTkFrame(ia_frame, fg_color="transparent")
        header_ia.pack(padx=14, pady=(10, 4), fill="x")

        ctk.CTkLabel(header_ia, text="🧠  Validação por IA  (Google Gemini)",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="#4fc3f7"
                     ).pack(side="left")

        self.ia_ativa_var = ctk.BooleanVar(value=False)
        self.ia_toggle = ctk.CTkCheckBox(
            header_ia,
            text="Ativar",
            variable=self.ia_ativa_var,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#4fc3f7",
            fg_color="#1e4d8c",
            hover_color="#2962ff",
            command=self._toggle_ia
        )
        self.ia_toggle.pack(side="right", padx=4)

        # Linha: API Key + botão de ajuda
        key_row = ctk.CTkFrame(ia_frame, fg_color="transparent")
        key_row.pack(padx=14, pady=(0, 4), fill="x")

        ctk.CTkLabel(key_row, text="Gemini API Key:",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="#90caf9"
                     ).pack(side="left", padx=(0, 8))

        self.api_key_e = ctk.CTkEntry(
            key_row, show="*", width=340,
            placeholder_text="Cole sua chave aqui  (grátis em aistudio.google.com/apikey)",
            state="disabled",
            fg_color="#0a1628", border_color="#1e4d8c"
        )
        self.api_key_e.pack(side="left", fill="x", expand=True)

        # Linha: status da IA
        self.ia_status_label = ctk.CTkLabel(
            ia_frame,
            text="⚫ IA desativada",
            font=ctk.CTkFont(size=11),
            text_color="#546e7a"
        )
        self.ia_status_label.pack(padx=14, pady=(2, 10), anchor="w")

        # ── Botões ─────────────────────────────────────────────────────────
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=8)

        self.start_btn = ctk.CTkButton(
            btn_frame, text="▶ INICIAR BOT",
            fg_color="#00C853", hover_color="#00E676",
            width=220, height=42, font=ctk.CTkFont(size=14, weight="bold"),
            command=self.start_bot)
        self.start_btn.grid(row=0, column=0, padx=10)

        self.stop_btn = ctk.CTkButton(
            btn_frame, text="⏹ PARAR BOT",
            fg_color="#D50000", hover_color="#FF1744",
            width=220, height=42, font=ctk.CTkFont(size=14, weight="bold"),
            state="disabled", command=self.stop_bot)
        self.stop_btn.grid(row=0, column=1, padx=10)

        # ── Console ────────────────────────────────────────────────────────
        ctk.CTkLabel(self, text="Console de Execução:",
                     font=ctk.CTkFont(size=13, weight="bold")
                     ).pack(pady=(4,2), padx=24, anchor="w")
        self.console = ctk.CTkTextbox(self, width=620, height=230,
                                      font=ctk.CTkFont(family="Consolas", size=11),
                                      state="disabled")
        self.console.pack(padx=20, pady=(0, 12))

    # ── Toggle IA ──────────────────────────────────────────────────────────
    def _toggle_ia(self):
        ativa = self.ia_ativa_var.get()
        if ativa:
            self.api_key_e.configure(state="normal")
            self.ia_status_label.configure(
                text="🟡 IA ativada  –  confiança mínima para executar: 75%",
                text_color="#ffd54f")
        else:
            self.api_key_e.configure(state="disabled")
            self.ia_status_label.configure(
                text="⚫ IA desativada",
                text_color="#546e7a")

    def _set_ia_status(self, texto, cor):
        """Atualiza o label de status da IA de forma thread-safe."""
        self.after(0, lambda: self.ia_status_label.configure(text=texto, text_color=cor))

    # ── Helpers ────────────────────────────────────────────────────────────
    def log(self, msg):
        hora = time.strftime("%H:%M:%S")
        self.console.configure(state="normal")
        self.console.insert("end", f"[{hora}] {msg}\n")
        self.console.see("end")
        self.console.configure(state="disabled")

    def set_placar(self, tipo, valor):
        """
        Regra simples:
          - Qualquer operação (CALL ou PUT) que AUMENTOU o saldo = WIN
          - Qualquer operação (CALL ou PUT) que DIMINUIU o saldo = LOSS
          - Saldo igual = EMPATE (não conta win nem loss)
        """
        if tipo == "WIN":
            self.wins  += 1
            self.lucro += valor        # valor positivo
        elif tipo == "LOSS":
            self.losses += 1
            self.lucro  += valor       # valor negativo (já veio como diff negativo)
        # EMPATE: não altera wins nem losses
        cor   = "#00E676" if self.lucro >= 0 else "#FF1744"
        sinal = "+" if self.lucro >= 0 else ""
        self.placar_label.configure(
            text=f"Placar: {self.wins} WINS | {self.losses} LOSS  |  Lucro: ${sinal}{self.lucro:.2f}",
            text_color=cor)

    def _exp_min(self):
        try:
            return int(self.exp_var.get().replace("min","").strip())
        except:
            return 1

    def _valor(self):
        try:
            return float(self.valor_e.get().replace(",","."))
        except:
            return 2.0

    # ── Loop Principal ─────────────────────────────────────────────────────
    def bot_loop(self, email, senha, tipo_conta, paridade):
        self.log("Conectando...")
        try:
            self.api = IQ_Option(email, senha)
            ok, reason = self.api.connect()
        except Exception as e:
            self.log(f"❌ Erro de conexão: {e}")
            self.after(0, self.stop_bot); return

        if not ok:
            self.log(f"❌ Autenticação falhou: {reason}")
            self.after(0, self.stop_bot); return

        self.api.change_balance(tipo_conta)
        saldo = self.api.get_balance()
        self.log(f"✅ Conectado! Saldo ({tipo_conta}): ${saldo:.2f}")

        ia_ativa = self.ia_ativa_var.get()
        api_key  = self.api_key_e.get().strip() if ia_ativa else ""

        if ia_ativa:
            if api_key:
                self.log("🧠 IA Gemini ATIVADA  –  confiança mínima: 75%")
            else:
                self.log("⚠️ IA ativada mas sem API Key – voltando ao modo técnico local.")
                ia_ativa = False

        self.log(f"🔍 Analisando {paridade}...")

        ultima_vela   = None
        ultimo_status = 0

        while self.is_running:
            try:
                valor   = self._valor()
                exp_min = self._exp_min()
                velas   = self.api.get_candles(paridade, 30, 60, time.time())

                # Fallback automático para OTC
                if (not velas or len(velas) < 30) and "-OTC" not in paridade.upper():
                    v2 = self.api.get_candles(paridade + "-OTC", 30, 60, time.time())
                    if v2 and len(v2) >= 30:
                        paridade = paridade + "-OTC"
                        velas = v2
                        self.log(f"ℹ️ Alternado para {paridade}")

                if not velas or len(velas) < 30:
                    self.log("Aguardando velas..."); time.sleep(3); continue

                sinal, info, _ = analisar_sinal(velas)

                # Log de status a cada 10s
                if time.time() - ultimo_status > 10:
                    self.log(f"📊 {info}")
                    ultimo_status = time.time()

                candle_id = velas[-2].get("from", 0)

                if sinal and candle_id != ultima_vela:
                    ultima_vela = candle_id
                    self.log(f"⚡ PRÉ-SINAL: {sinal.upper()} | Valor: ${valor:.2f} | Exp: {exp_min}min")

                    # ── VALIDAÇÃO POR IA ──────────────────────────────────
                    sinal_final = sinal
                    if ia_ativa:
                        self._set_ia_status("🔵 Consultando IA Gemini...", "#4fc3f7")
                        self.log("🧠 Consultando IA Gemini para validar o sinal...")

                        decisao, confianca, motivo = consultar_ia(
                            velas, sinal, api_key, log_fn=self.log
                        )

                        emoji_conf = "✅" if confianca >= CONFIANCA_MINIMA else "🛑"
                        self.log(f"🧠 IA: \"{motivo}\"")
                        self.log(f"   Decisão: {decisao.upper()} | Confiança: {confianca}% {emoji_conf}")

                        if decisao == "aguardar" or confianca < CONFIANCA_MINIMA:
                            self.log(f"🛑 IA BLOQUEOU entrada (confiança {confianca}% < {CONFIANCA_MINIMA}%). Aguardando...")
                            self._set_ia_status(
                                f"🛑 Última: BLOQUEADO  –  confiança {confianca}%  |  {motivo[:50]}",
                                "#ef9a9a")
                            time.sleep(1)
                            continue  # pula esta vela, aguarda próximo sinal

                        sinal_final = decisao  # pode ser "call" ou "put" confirmado pela IA
                        self._set_ia_status(
                            f"✅ Última: {decisao.upper()} aprovado  –  confiança {confianca}%",
                            "#a5d6a7")
                    # ── FIM VALIDAÇÃO IA ──────────────────────────────────

                    saldo_antes = self.api.get_balance()
                    sucesso, tipo_op, oid = executar_ordem(
                        self.api, valor, paridade, sinal_final, exp_min)

                    if sucesso:
                        origem = f"IA ({confianca}%)" if ia_ativa else "Técnico"
                        self.log(f"🚀 Ordem {sinal_final.upper()} ABERTA via {tipo_op} | Origem: {origem} (ID:{oid})")
                        self.log(f"⏳ Aguardando {exp_min * 60}s...")

                        # Aguarda expiração sem bloquear
                        for _ in range(exp_min * 60):
                            if not self.is_running: break
                            time.sleep(1)

                        if not self.is_running: break

                        time.sleep(2)
                        saldo_depois = self.api.get_balance()
                        diff = saldo_depois - saldo_antes

                        self.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                        if diff > 0.01:
                            self.log(f"🎉 WIN ({sinal_final.upper()})! Ganhou: +${diff:.2f}")
                            self.after(0, lambda d=diff: self.set_placar("WIN", d))
                        elif diff < -0.01:
                            self.log(f"🔻 LOSS ({sinal_final.upper()})! Perdeu: -${abs(diff):.2f}")
                            self.after(0, lambda d=diff: self.set_placar("LOSS", d))
                        else:
                            self.log(f"⚖️ EMPATE ({sinal_final.upper()})! Saldo devolvido.")
                            self.after(0, lambda: self.set_placar("EMPATE", 0))
                        self.log(f"💰 Saldo: ${saldo_depois:.2f}")
                        self.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                        self.log("🔄 Buscando próxima oportunidade...")
                    else:
                        self.log(f"❌ Falha ao abrir ordem em {paridade}.")
                        time.sleep(3)

                time.sleep(1)

            except Exception as e:
                self.log(f"⚠️ {e}")
                time.sleep(2)

        self.log("⏹ Bot parado.")
        try: self.api.api.close()
        except: pass

    # ── Controles ─────────────────────────────────────────────────────────
    def start_bot(self):
        email    = self.email_e.get().strip()
        senha    = self.senha_e.get().strip()
        paridade = self.paridade_e.get().strip()
        conta    = self.conta_var.get()

        if not email or not senha or not paridade:
            self.log("❌ Preencha todos os campos."); return

        try:
            float(self.valor_e.get().replace(",","."))
        except:
            self.log("❌ Valor inválido."); return

        self.is_running = True
        self.wins = self.losses = 0
        self.lucro = 0.0
        self.placar_label.configure(
            text="Placar: 0 WINS | 0 LOSS  |  Lucro: $0.00",
            text_color="#00E676")

        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.console.configure(state="normal")
        self.console.delete("1.0","end")
        self.console.configure(state="disabled")

        threading.Thread(
            target=self.bot_loop,
            args=(email, senha, conta, paridade),
            daemon=True
        ).start()

    def stop_bot(self):
        self.is_running = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self._set_ia_status("⚫ IA desativada", "#546e7a")
        self.log("⏹ Parando o bot...")


if __name__ == "__main__":
    BotApp().mainloop()
