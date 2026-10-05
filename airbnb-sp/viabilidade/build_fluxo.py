"""Planilha de fluxo de pagamento e break-even - SAMPA 135 (studio para Airbnb).

Abas: Premissas (entradas), Tabela SAMPA 135 (cópia da tabela da incorporadora),
Fluxo mensal (jan/27 a dez/58, tudo em fórmulas) e Resumo (indicadores + gráfico).
"""
from datetime import date
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.comments import Comment
from openpyxl.chart import LineChart, Reference

SRC = "SAMPA135_tabela_pre-lancamento_set2026.xlsx"  # tabela recebida da incorporadora (ajuste o caminho)
OUT = "SAMPA135_fluxo_breakeven.xlsx"

# ---------- estilos ----------
F = "Arial"
f_norm = Font(name=F, size=10)
f_bold = Font(name=F, size=10, bold=True)
f_title = Font(name=F, size=14, bold=True)
f_input = Font(name=F, size=10, color="0000FF")          # entrada (azul)
f_link = Font(name=F, size=10, color="008000")           # link para outra aba (verde)
f_head = Font(name=F, size=10, bold=True, color="FFFFFF")
fill_key = PatternFill("solid", fgColor="FFFF00")         # premissa-chave
fill_head = PatternFill("solid", fgColor="1F2A2E")
fill_sub = PatternFill("solid", fgColor="EDEAE3")
thin = Side(style="thin", color="D0CCC2")
BRL = 'R$ #,##0;(R$ #,##0);"-"'
BRL2 = 'R$ #,##0.00;(R$ #,##0.00);"-"'
PCT = '0.0%;(0.0%);"-"'
DT = 'mmm/yy'

wb = Workbook()

# =====================================================================
# Aba 1: Tabela SAMPA 135 (cópia literal da tabela recebida)
# =====================================================================
src = load_workbook(SRC).active
wt = wb.active
wt.title = "Tabela SAMPA 135"
for row in src.iter_rows():
    for c in row:
        if c.value is not None:
            wt[c.coordinate] = c.value
            wt[c.coordinate].font = f_norm
wt["A1"].font = f_title
for c in wt[4]:
    c.font = f_bold; c.fill = fill_sub; c.alignment = Alignment(wrap_text=True, vertical="top")
for r in range(5, 15):
    for col in "EFGHIJKLM":
        wt[f"{col}{r}"].number_format = BRL if col not in "LM" else BRL2
wt["A24"] = "Fonte: tabela de pré-lançamento SAMPA 135 (set/2026) enviada pelo usuário. Valores copiados sem alteração."
wt["A24"].font = Font(name=F, size=9, italic=True)
for i, w in enumerate([10, 7, 11, 8, 11, 12, 14, 14, 12, 16, 12, 13, 13, 14], 1):
    wt.column_dimensions[get_column_letter(i)].width = w
wt.row_dimensions[4].height = 42
T = "'Tabela SAMPA 135'"

# =====================================================================
# Aba 2: Premissas
# =====================================================================
wp = wb.create_sheet("Premissas", 0)
wp["A1"] = "Premissas do estudo - SAMPA 135 (studio para Airbnb)"; wp["A1"].font = f_title
wp["A2"] = "Edite só as células em azul (amarelo = premissas que mais mexem no resultado). Todo o resto é calculado."
wp["A2"].font = Font(name=F, size=9, italic=True)

P = {}  # nome -> endereço absoluto 'Premissas'!$C$n
row = 4
def section(title):
    global row
    row += 1
    wp[f"A{row}"] = title; wp[f"A{row}"].font = f_bold
    for col in "ABCD":
        wp[f"{col}{row}"].fill = fill_sub
    row += 1

def inp(key, label, value, fmt=None, note="", key_assumption=False, formula=False):
    """Escreve uma premissa: rótulo (A), valor (C), nota (D)."""
    global row
    wp[f"A{row}"] = label; wp[f"A{row}"].font = f_norm
    c = wp[f"C{row}"]; c.value = value
    c.font = f_norm if formula else f_input
    if key_assumption and not formula:
        c.fill = fill_key
    if fmt: c.number_format = fmt
    if note:
        wp[f"D{row}"] = note; wp[f"D{row}"].font = Font(name=F, size=9, color="6B6A64")
    P[key] = f"Premissas!$C${row}"
    row += 1

section("1. Unidade (da tabela da incorporadora)")
inp("final", "Final escolhido (lista)", "6, 7 e 8", note="Escolha na lista. Padrão: 21,94 m², a mais próxima do foco de ~20 m².", key_assumption=True)
MATCH = f"MATCH({{}},{T}!$A$5:$A$14,0)"
def tab(col):
    return f"=INDEX({T}!${col}$5:${col}$14,MATCH({P['final']},{T}!$A$5:$A$14,0))"
inp("area", "Área privativa (m²)", tab("C"), '0.00', formula=True)
inp("entrada", "Entrada (ato)", tab("E"), BRL, formula=True)
inp("p3060", "Parcela 30 e 60 dias (cada uma)", tab("F"), BRL, "2 parcelas desse valor (a soma fecha com o preço total)", formula=True)
inp("mensal", "Parcela mensal (19x)", tab("G"), BRL, formula=True)
inp("semestral", "Parcela semestral (3x)", tab("H"), BRL, formula=True)
inp("chaves_pg", "Parcela das chaves (ago/28)", tab("I"), BRL, formula=True)
inp("fin_tab", "Saldo financiado na entrega (tabela)", tab("J"), BRL, formula=True)
inp("preco", "Preço total (tabela)", tab("K"), BRL, formula=True)
inp("precom2", "Preço por m²", f"={P['preco']}/{P['area']}", BRL, formula=True)

section("2. Datas")
inp("base", "Data-base da tabela", date(2026, 9, 1), DT, "Valores da tabela são de set/2026 e corrigem pelo INCC até o pagamento")
inp("compra", "Data da compra (assinatura)", date(2027, 1, 1), DT, "Informado pelo usuário: jan/27", key_assumption=True)
inp("ini_mensal", "1ª parcela mensal", date(2027, 1, 1), DT, "Tabela: 19 mensais a partir de jan/27")
inp("n_mensal", "Nº de parcelas mensais", 19, '0')
inp("sem1", "1ª semestral", date(2027, 6, 1), DT, "Tabela: 3 semestrais a partir de jun/27")
inp("sem2", "2ª semestral", date(2027, 12, 1), DT)
inp("sem3", "3ª semestral", date(2028, 6, 1), DT)
inp("chaves", "Entrega das chaves", date(2028, 8, 1), DT, "Informado pelo usuário: ago/28", key_assumption=True)
inp("meses_mob", "Meses para mobiliar (sem aluguel)", 2, '0', "Informado pelo usuário: 2 meses")
inp("ini_op", "Início do aluguel (Airbnb)", f"=DATE(YEAR({P['chaves']}),MONTH({P['chaves']})+{P['meses_mob']}+1,1)", DT, formula=True)

section("3. Correções e financiamento")
inp("incc", "INCC durante a obra (a.a.)", 0.055, PCT, "Estimativa (INCC-FGV recente ~5-6% a.a.). Tabela: corrige mensalmente pelo INCC", key_assumption=True)
inp("juros", "Juros do financiamento (a.a.)", 0.12, PCT, "Derivado da tabela: parcelas 1 e 120 batem com SAC a 12% a.a.", key_assumption=True)
inp("prazo", "Prazo do financiamento (meses)", 120, '0', "Tabela: financiamento direto em 120x. Para simular banco, use 360 e a taxa do banco")
inp("ipca_fin", "Correção do saldo pós-chaves (a.a.)", 0.04, PCT, "Premissa: IPCA ~4%. A tabela não informa o indexador; confirmar com a incorporadora", key_assumption=True)
inp("itbi", "ITBI + escritura/registro (% do preço)", 0.04, PCT, "ITBI SP 3% + registro ~1%. Pago nas chaves (tabela, nota D)")
inp("mobilia", "Mobília, decoração e enxoval", 30000, BRL, "Estimativa para ~22 m². Dividido pelos meses de mobília", key_assumption=True)

section("4. Operação Airbnb (valores de hoje, corrigidos pela inflação)")
inp("diaria", "Diária média", 230, BRL, "Cenário base do estudo (R$ 220-245 média SP). Ajuste conforme a região do prédio", key_assumption=True)
inp("ocup", "Ocupação média", 0.62, PCT, "Mediana de SP: 61-63%", key_assumption=True)
inp("dias", "Dias por mês", 30, '0')
inp("ramp_m", "Meses de ramp-up (início)", 3, '0', "Anúncio novo leva alguns meses para ganhar avaliações")
inp("ramp_f", "Ocupação no ramp-up (% da média)", 0.6, PCT)
inp("tx_airbnb", "Taxa Airbnb (anfitrião)", 0.16, PCT, "Modelo de taxa única do anfitrião")
inp("gestora", "Gestora (% da receita bruta)", 0.20, PCT, "Mercado: 15-28%")
inp("cond", "Condomínio + IPTU (mês)", 750, BRL, "Estimativa. Pago a partir das chaves", key_assumption=True)
inp("contas", "Luz, internet, streaming, amenities (mês)", 300, BRL)
inp("manut", "Manutenção e reposição (mês)", 150, BRL)
inp("infl", "Inflação de diária e custos (a.a.)", 0.04, PCT)
inp("ir", "IR sobre aluguel (alíquota marginal)", 0.275, PCT, "Carnê-leão. Deduz Airbnb, gestora, condomínio e IPTU. Use 0 se não tiver outra renda tributável alta")

section("5. Valorização e venda")
inp("valoriz", "Valorização do imóvel (a.a.)", 0.05, PCT, "SP: +3,8% em 12 meses (FipeZap jul/26). Teste 3-8%", key_assumption=True)
inp("corret", "Corretagem na venda", 0.06, PCT)
inp("ir_gc", "IR sobre ganho de capital", 0.15, PCT, "Sem fatores de redução (conservador)")

section("6. Consórcio (alternativa ao financiamento direto)")
inp("c_adesao", "Adesão ao consórcio", date(2027, 1, 1), DT, "Junto com a compra (jan/27). A carta só quita o imóvel com habite-se, ou seja, nas chaves")
inp("c_prazo", "Prazo do plano (meses)", 180, '0', "Imóvel: 150-240 meses é o comum")
inp("c_tadm", "Taxa de administração (total do plano)", 0.18, PCT, "Mercado: 15-25% (algumas a partir de 9,5%)", key_assumption=True)
inp("c_fr", "Fundo de reserva (total do plano)", 0.02, PCT, "Mercado: 1-5%, comum 2-3%")
inp("c_idx", "Reajuste anual da carta e parcelas", 0.055, PCT, "Normalmente INCC (aniversário anual). Mesmo INCC da obra")
inp("c_red", "Parcela reduzida até a contemplação (% da integral)", 0.5, PCT, "Informado pelo usuário: 50%. A diferença é diluída depois da contemplação")
inp("c_emb", "Lance embutido (% da carta)", 0.30, PCT, "Informado pelo usuário: embutido. Limite usual 25-30%; reduz o crédito recebido", key_assumption=True)
inp("c_livre", "Lance livre em dinheiro (% da carta)", 0.0, PCT, "Lances vencedores: 20-40% (grupos novos 10-20%). Some ao embutido se precisar", key_assumption=True)
inp("c_contemp", "Mês da contemplação", date(2028, 6, 1), DT, "Premissa: até as chaves. Sem contemplação até ago/28 seria preciso outra fonte para quitar o saldo", key_assumption=True)
inp("c_itbi", "Usar o crédito também para ITBI/registro? (1=sim, 0=não)", 1, '0', "Administradoras costumam permitir o uso do excedente em despesas de registro")
inp("cA_val", "Estrutura A: valor de cada carta", 100000, BRL, "Informado pelo usuário: cartas de R$ 100 mil", key_assumption=True)
inp("cA_qtd", "Estrutura A: quantidade de cartas", 5, '0', "5 cartas cobrem o saldo das chaves + ITBI com 30% de embutido. Cada carta precisa ser contemplada")
inp("cB_val", "Estrutura B: valor de cada carta", 300000, BRL, "Informado pelo usuário: cartas de R$ 300 mil", key_assumption=True)
inp("cB_qtd", "Estrutura B: quantidade de cartas", 2, '0', "1 carta não cobre o saldo; 2 cartas sobram crédito, que abate o plano")

section("7. Alternativa: aplicar o mesmo dinheiro (carteira espelho)")
inp("cdi27", "CDI médio 2027 (a.a.)", 0.125, PCT, "Focus out/26: Selic 13,75% fim/26 e 12% fim/27", key_assumption=True)
inp("cdi28", "CDI médio 2028 (a.a.)", 0.11, PCT, "Focus: Selic 10,5% fim/28")
inp("cdi29", "CDI médio 2029 em diante (a.a.)", 0.10, PCT, "Focus: Selic 10% em 2029; mantido no longo prazo", key_assumption=True)
inp("ipca_real", "Tesouro IPCA+: juro real (a.a.)", 0.065, PCT, "IPCA+ 2045 ~7,2% hoje (caiu no pregão de 05/10/26); 6,5% conservador. IPCA = inflação da seção 4", key_assumption=True)
inp("ir_aplic", "IR sobre rendimento da aplicação", 0.15, PCT, "Tabela regressiva acima de 2 anos. LCI/LCA isentas rendem ~90% do CDI (resultado parecido)")

section("Taxas mensais equivalentes (calculadas)")
for k, lab in [("incc", "INCC"), ("juros", "Juros"), ("ipca_fin", "Correção do saldo"), ("infl", "Inflação"), ("valoriz", "Valorização")]:
    inp(k + "_m", f"{lab} ao mês", f"=(1+{P[k]})^(1/12)-1", '0.000%', formula=True)

wp.column_dimensions["A"].width = 44; wp.column_dimensions["B"].width = 2
wp.column_dimensions["C"].width = 16; wp.column_dimensions["D"].width = 86
dv = DataValidation(type="list", formula1=f"={T}!$A$5:$A$14", allow_blank=False)
wp.add_data_validation(dv); dv.add(P["final"].split("!")[1].replace("$", ""))
wp.freeze_panes = "A4"

# =====================================================================
# Aba 3: Fluxo mensal
# =====================================================================
wf = wb.create_sheet("Fluxo mensal")
heads = [
 ("A", "Mês", 9), ("B", "Fase", 11), ("C", "Meses desde a tabela", 9),
 ("D", "Pagto incorporadora (tabela)", 13), ("E", "Fator INCC", 8), ("F", "Pagto incorporadora corrigido", 13),
 ("G", "ITBI + registro", 11), ("H", "Mobília", 11),
 ("I", "Nº parcela financ.", 8), ("J", "Saldo corrigido", 13), ("K", "Juros", 11), ("L", "Amortização", 11),
 ("M", "Parcela financiamento", 13), ("N", "Saldo devedor", 13),
 ("O", "Ocupação", 9), ("P", "Receita bruta", 12), ("Q", "Taxa Airbnb", 11), ("R", "Gestora", 11),
 ("S", "Condomínio + IPTU", 11), ("T", "Contas", 10), ("U", "Manutenção", 10), ("V", "IR", 10),
 ("W", "Resultado do imóvel (após IR)", 13), ("X", "Fluxo de caixa do mês", 13), ("Y", "Caixa acumulado", 14),
 ("Z", "Valor de mercado", 13), ("AA", "Patrimônio líquido se vender", 14), ("AB", "Posição total (caixa + patrimônio)", 15),
 ("AC", "Flag: aluguel cobre parcela", 11), ("AD", "Flag: caixa acumulado ≥ 0", 11), ("AE", "Flag: posição ≥ 0", 11),
]
wf["A1"] = "Fluxo mensal - pagamento, operação e break-even (R$ nominais)"; wf["A1"].font = f_title
wf["A2"] = ("Saídas negativas no fluxo de caixa. Pagamentos da obra corrigidos pelo INCC desde a data-base da tabela; "
            "financiamento SAC com correção do saldo; receita e custos corrigidos pela inflação.")
wf["A2"].font = Font(name=F, size=9, italic=True)
HR = 4
for col, h, w in heads:
    c = wf[f"{col}{HR}"]; c.value = h; c.font = f_head; c.fill = fill_head
    c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
    wf.column_dimensions[col].width = w
wf.row_dimensions[HR].height = 54

first = HR + 1
months = []
d = date(2027, 1, 1)
while d <= date(2058, 12, 1):
    months.append(d); d = date(d.year + (d.month // 12), d.month % 12 + 1, 1)
last = first + len(months) - 1

p = P
for idx, m in enumerate(months):
    r = first + idx
    A = f"$A{r}"
    if idx == 0:
        wf[f"A{r}"] = f"={p['compra']}"
    else:
        wf[f"A{r}"] = f"=DATE(YEAR(A{r-1}),MONTH(A{r-1})+1,1)"
    wf[f"A{r}"].number_format = DT
    # Fase
    wf[f"B{r}"] = (f'=IF({A}<{p["chaves"]},"Obra",IF({A}={p["chaves"]},"Chaves",'
                   f'IF({A}<{p["ini_op"]},"Mobiliando","Airbnb")))')
    # meses desde a data-base da tabela
    wf[f"C{r}"] = f"=(YEAR({A})-YEAR({p['base']}))*12+MONTH({A})-MONTH({p['base']})"
    # pagamento à incorporadora pelo cronograma da tabela (valores nominais)
    wf[f"D{r}"] = (f"=({A}={p['compra']})*{p['entrada']}"
                   f"+(({A}=EDATE({p['compra']},1))+({A}=EDATE({p['compra']},2)))*{p['p3060']}"
                   f"+AND({A}>={p['ini_mensal']},{A}<EDATE({p['ini_mensal']},{p['n_mensal']}))*{p['mensal']}"
                   f"+(({A}={p['sem1']})+({A}={p['sem2']})+({A}={p['sem3']}))*{p['semestral']}"
                   f"+({A}={p['chaves']})*{p['chaves_pg']}")
    wf[f"E{r}"] = f"=(1+{p['incc_m']})^C{r}"
    wf[f"F{r}"] = f"=D{r}*E{r}"
    wf[f"G{r}"] = f"=({A}={p['chaves']})*{p['itbi']}*{p['preco']}*(1+{p['incc_m']})^C{r}"
    wf[f"H{r}"] = f"=IF(AND({A}>{p['chaves']},{A}<{p['ini_op']}),{p['mobilia']}/MAX(1,{p['meses_mob']}),0)"
    # financiamento SAC com correção monetária do saldo
    msk = f"((YEAR({A})-YEAR({p['chaves']}))*12+MONTH({A})-MONTH({p['chaves']}))"
    wf[f"I{r}"] = f"=IF(AND({A}>{p['chaves']},{msk}<={p['prazo']}),{msk},0)"
    prevN = f"N{r-1}" if idx > 0 else "0"
    wf[f"J{r}"] = f"=IF(I{r}>0,{prevN}*(1+{p['ipca_fin_m']}),0)"
    wf[f"K{r}"] = f"=J{r}*{p['juros_m']}"
    wf[f"L{r}"] = f"=IF(I{r}>0,J{r}/({p['prazo']}-I{r}+1),0)"
    wf[f"M{r}"] = f"=K{r}+L{r}"
    wf[f"N{r}"] = f"=IF({A}={p['chaves']},{p['fin_tab']}*E{r},IF(I{r}>0,J{r}-L{r},0))"
    # operação
    mop = f"((YEAR({A})-YEAR({p['ini_op']}))*12+MONTH({A})-MONTH({p['ini_op']}))"
    inf = f"(1+{p['infl_m']})^((YEAR({A})-YEAR({p['compra']}))*12+MONTH({A})-MONTH({p['compra']}))"
    wf[f"O{r}"] = f"=IF({A}>={p['ini_op']},{p['ocup']}*IF({mop}<{p['ramp_m']},{p['ramp_f']},1),0)"
    wf[f"P{r}"] = f"=O{r}*{p['diaria']}*{p['dias']}*{inf}"
    wf[f"Q{r}"] = f"=P{r}*{p['tx_airbnb']}"
    wf[f"R{r}"] = f"=P{r}*{p['gestora']}"
    wf[f"S{r}"] = f"=IF({A}>={p['chaves']},{p['cond']}*{inf},0)"
    wf[f"T{r}"] = f"=IF({A}>={p['ini_op']},{p['contas']}*{inf},0)"
    wf[f"U{r}"] = f"=IF({A}>={p['ini_op']},{p['manut']}*{inf},0)"
    wf[f"V{r}"] = f"=IF({A}>={p['ini_op']},MAX(0,P{r}-Q{r}-R{r}-S{r})*{p['ir']},0)"
    wf[f"W{r}"] = f"=P{r}-Q{r}-R{r}-S{r}-T{r}-U{r}-V{r}"
    wf[f"X{r}"] = f"=W{r}-F{r}-G{r}-H{r}-M{r}"
    wf[f"Y{r}"] = f"=X{r}" if idx == 0 else f"=Y{r-1}+X{r}"
    # valor e posição (a partir das chaves)
    mc = f"((YEAR({A})-YEAR({p['compra']}))*12+MONTH({A})-MONTH({p['compra']}))"
    wf[f"Z{r}"] = f"={p['preco']}*(1+{p['incc_m']})^((YEAR({p['compra']})-YEAR({p['base']}))*12+MONTH({p['compra']})-MONTH({p['base']}))*(1+{p['valoriz_m']})^{mc}"
    custo = f"({p['preco']}*(1+{p['incc_m']})^((YEAR({p['chaves']})-YEAR({p['base']}))*12+MONTH({p['chaves']})-MONTH({p['base']}))*(1+{p['itbi']}))"
    wf[f"AA{r}"] = (f'=IF({A}>={p["chaves"]},Z{r}*(1-{p["corret"]})-N{r}'
                    f'-{p["ir_gc"]}*MAX(0,Z{r}*(1-{p["corret"]})-{custo}),"")')
    wf[f"AB{r}"] = f'=IF({A}>={p["chaves"]},Y{r}+AA{r},"")'
    # flags de break-even (data quando a condição é atendida)
    wf[f"AC{r}"] = f'=IF(AND({A}>={p["ini_op"]},W{r}>=M{r}),{A},"")'
    wf[f"AD{r}"] = f'=IF(AND({A}>={p["ini_op"]},Y{r}>=0),{A},"")'
    wf[f"AE{r}"] = f'=IF(AND({A}>={p["chaves"]},N(AB{r})>=0),{A},"")'

    for col, _, _ in heads:
        c = wf[f"{col}{r}"]; c.font = f_norm
        if col in ("A", "AC", "AD", "AE"): c.number_format = DT
        elif col in ("C", "I"): c.number_format = '0;-0;"-"'
        elif col == "E": c.number_format = '0.0000'
        elif col == "O": c.number_format = PCT
        elif col != "B": c.number_format = BRL
    if wf[f"A{r}"].value and m.month == 1:
        for col, _, _ in heads:
            wf[f"{col}{r}"].border = Border(top=thin)
wf.freeze_panes = f"C{first}"
for col in ("C", "E", "AC", "AD", "AE"):
    wf.column_dimensions[col].hidden = False
FL = "'Fluxo mensal'"
rng = lambda col: f"{FL}!${col}${first}:${col}${last}"


# =====================================================================
# Abas 5/6: Consórcio (uma por estrutura de cartas)
# =====================================================================
FLX = "'Fluxo mensal'"
def make_consorcio(title, vkey, qkey, label):
    wc = wb.create_sheet(title)
    wc["A1"] = f"Consórcio - {label}"; wc["A1"].font = f_title
    wc["A2"] = ("Obra paga em dinheiro como na tabela; consórcio desde a adesão (parcela reduzida até a contemplação); "
                "crédito quita o saldo nas chaves no lugar do financiamento direto. Operação Airbnb igual à aba Fluxo mensal.")
    wc["A2"].font = Font(name=F, size=9, italic=True)
    V, Q, n = P[vkey], P[qkey], P["c_prazo"]
    K = f"(1+{P['c_tadm']}+{P['c_fr']})"
    cols = [("A","Mês",9),("B","Nº parcela consórcio",8),("C","Valor da carta corrigido (unid.)",13),
            ("D","Fração do plano paga no mês",10),("E","Amortização extra (fração)",10),("F","Fração acumulada",9),
            ("G","Parcela consórcio (todas as cartas)",13),("H","Lance livre (dinheiro)",12),("I","Complemento em dinheiro nas chaves",13),
            ("J","Saldo devedor do consórcio",14),("K","Fluxo de caixa do mês",13),("L","Caixa acumulado",14),
            ("M","Patrimônio líquido se vender",14),("N","Posição total",14),
            ("O","Flag: aluguel cobre parcela",10),("P","Flag: caixa ≥ 0",10),("Q","Flag: posição ≥ 0",10)]
    for col, h, w in cols:
        c = wc[f"{col}{HR}"]; c.value = h; c.font = f_head; c.fill = fill_head
        c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
        wc.column_dimensions[col].width = w
    wc.row_dimensions[HR].height = 54
    # células auxiliares (coluna S/T)
    aux = {}
    ar = HR
    def helper(key, label, formula, fmt=BRL):
        nonlocal ar
        wc[f"S{ar}"] = label; wc[f"S{ar}"].font = f_norm
        wc[f"T{ar}"] = formula; wc[f"T{ar}"].font = f_norm; wc[f"T{ar}"].number_format = fmt
        aux[key] = f"$T${ar}"; ar += 1
    wc[f"S{HR-1}"] = "Cálculos auxiliares"; wc[f"S{HR-1}"].font = f_bold
    rngc = lambda col: f"${col}${first}:${col}${last}"
    helper("vc", "Valor da carta na contemplação (unid.)", f"=INDEX({rngc('C')},MATCH({P['c_contemp']},{rngc('A')},0))")
    helper("cred", "Crédito líquido liberado (após lance embutido)", f"={Q}*{aux['vc']}*(1-{P['c_emb']})")
    helper("need", "Necessidade nas chaves (saldo + ITBI se usar crédito)",
           f"=INDEX({FLX}!$N${first}:$N${last},MATCH({P['chaves']},{FLX}!$A${first}:$A${last},0))"
           f"+{P['c_itbi']}*INDEX({FLX}!$G${first}:$G${last},MATCH({P['chaves']},{FLX}!$A${first}:$A${last},0))")
    helper("exc", "Crédito excedente (abate o plano)", f"=MAX(0,{aux['cred']}-{aux['need']})")
    helper("falta", "Falta cobrir em dinheiro", f"=MAX(0,{aux['need']}-{aux['cred']})")
    helper("vk", "Valor da carta nas chaves (unid.)", f"=INDEX({rngc('C')},MATCH({P['chaves']},{rngc('A')},0))")
    helper("custo", "Custo de aquisição p/ IR (preço corrigido + ITBI)",
           f"={P['preco']}*(1+{P['incc_m']})^((YEAR({P['chaves']})-YEAR({P['base']}))*12+MONTH({P['chaves']})-MONTH({P['base']}))*(1+{P['itbi']})")
    helper("ok", "Contemplação até as chaves?", f'=IF({P["c_contemp"]}<={P["chaves"]},"OK","ATENÇÃO: contemplação depois das chaves")', '@')
    wc.column_dimensions["S"].width = 46; wc.column_dimensions["T"].width = 16

    for idx in range(len(months)):
        r = first + idx; A = f"$A{r}"
        wc[f"A{r}"] = f"={FLX}!A{r}"
        ms = f"((YEAR({A})-YEAR({P['c_adesao']}))*12+MONTH({A})-MONTH({P['c_adesao']}))"
        wc[f"B{r}"] = f"=IF(AND({A}>={P['c_adesao']},{ms}<{n}),{ms}+1,0)"
        wc[f"C{r}"] = f"={V}*(1+{P['c_idx']})^INT(MAX(0,{ms})/12)"
        prevF = f"F{r-1}" if idx > 0 else "0"
        wc[f"D{r}"] = (f"=IF(B{r}=0,0,IF({A}<={P['c_contemp']},{P['c_red']}/{n},"
                       f"MAX(0,1-{prevF})/({n}-B{r}+1)))")
        wc[f"E{r}"] = (f"=({A}={P['c_contemp']})*({P['c_emb']}+{P['c_livre']})/{K}"
                       f"+({A}={P['chaves']})*{aux['exc']}/MAX(1,{Q}*{aux['vk']}*{K})")
        wc[f"F{r}"] = f"=MIN(1,{prevF}+D{r}+E{r})"
        wc[f"G{r}"] = f"={Q}*D{r}*C{r}*{K}"
        wc[f"H{r}"] = f"=({A}={P['c_contemp']})*{P['c_livre']}*{Q}*C{r}"
        wc[f"I{r}"] = f"=({A}={P['chaves']})*{aux['falta']}"
        wc[f"J{r}"] = f"=IF(B{r}>0,{Q}*(1-F{r})*C{r}*{K},0)"
        # fluxo: operação (W) - obra (F) - ITBI em dinheiro se não usar crédito (G) - mobília (H) - consórcio
        wc[f"K{r}"] = (f"={FLX}!W{r}-{FLX}!F{r}-(1-{P['c_itbi']})*{FLX}!G{r}-{FLX}!H{r}-G{r}-H{r}-I{r}")
        wc[f"L{r}"] = f"=K{r}" if idx == 0 else f"=L{r-1}+K{r}"
        wc[f"M{r}"] = (f'=IF({A}>={P["chaves"]},{FLX}!Z{r}*(1-{P["corret"]})-J{r}'
                       f'-{P["ir_gc"]}*MAX(0,{FLX}!Z{r}*(1-{P["corret"]})-{aux["custo"]}),"")')
        wc[f"N{r}"] = f'=IF({A}>={P["chaves"]},L{r}+M{r},"")'
        wc[f"O{r}"] = f'=IF(AND({A}>={P["ini_op"]},{FLX}!W{r}>=G{r}),{A},"")'
        wc[f"P{r}"] = f'=IF(AND({A}>={P["ini_op"]},L{r}>=0),{A},"")'
        wc[f"Q{r}"] = f'=IF(AND({A}>={P["chaves"]},N(N{r})>=0),{A},"")'
        for col, _, _ in cols:
            c = wc[f"{col}{r}"]; c.font = f_norm
            if col in ("A", "O", "P", "Q"): c.number_format = DT
            elif col == "B": c.number_format = '0;-0;"-"'
            elif col in ("D", "E", "F"): c.number_format = '0.000%;-0.000%;"-"'
            else: c.number_format = BRL
    wc.freeze_panes = f"B{first}"
    return wc, aux

wcA, auxA = make_consorcio("Consórcio A", "cA_val", "cA_qtd", "Estrutura A (cartas de R$ 100 mil)")
wcB, auxB = make_consorcio("Consórcio B", "cB_val", "cB_qtd", "Estrutura B (cartas de R$ 300 mil)")

# =====================================================================
# Aba Comparativo: financiamento direto x consórcio A x consórcio B
# =====================================================================
wq = wb.create_sheet("Comparativo", 0)
wq["A1"] = "Comparativo: financiamento direto x consórcio (SAMPA 135)"; wq["A1"].font = f_title
wq["A2"] = "Valores nominais em R$. Mesma unidade, obra e operação Airbnb; muda só como o saldo das chaves é pago."
wq["A2"].font = Font(name=F, size=9, italic=True)
NA2 = '"Não atinge até dez/58"'
def R(sheet, col): return f"'{sheet}'!${col}${first}:${col}${last}"
heads_q = ["Indicador", "Financiamento direto (tabela)", "Consórcio A", "Consórcio B"]
for i, h in enumerate(heads_q):
    c = wq.cell(row=4, column=i+1, value=h); c.font = f_head; c.fill = fill_head
    c.alignment = Alignment(wrap_text=True, horizontal="center", vertical="center")
wq.row_dimensions[4].height = 32
fin = "Fluxo mensal"
def cons_rows(sh, aux):
    return {
     "estrutura": f'={P["cA_qtd"] if sh=="Consórcio A" else P["cB_qtd"]}&" carta(s) de R$ "&ROUND({P["cA_val"] if sh=="Consórcio A" else P["cB_val"]}/1000,0)&" mil"',
     "credito": f"='{sh}'!{aux['cred']}",
     "sobra": f"='{sh}'!{aux['exc']}-'{sh}'!{aux['falta']}",
     "obra": f"=-SUMIFS({R(sh,'K')},{R(sh,'A')},\"<=\"&{P['chaves']})",
     "parc_ini": f"=INDEX({R(sh,'G')},MATCH({P['c_adesao']},{R(sh,'A')},0))",
     "parc_pos": f"=INDEX({R(sh,'G')},MATCH(EDATE({P['chaves']},1),{R(sh,'A')},0))",
     "fluxo1": f"=AVERAGEIFS({R(sh,'K')},{R(sh,'A')},\">=\"&{P['ini_op']},{R(sh,'A')},\"<\"&EDATE({P['ini_op']},12))",
     "aporte": f"=MIN({R(sh,'L')})",
     "be_op": f"=IF(MIN({R(sh,'O')})=0,{NA2},MIN({R(sh,'O')}))",
     "be_cx": f"=IF(MIN({R(sh,'P')})=0,{NA2},MIN({R(sh,'P')}))",
     "be_pat": f"=IF(MIN({R(sh,'Q')})=0,{NA2},MIN({R(sh,'Q')}))",
     "fim": f"=EDATE({P['c_adesao']},{P['c_prazo']}-1)",
     "pago": f"=SUM({R(sh,'G')})+SUM({R(sh,'H')})",
     "p10": f"=INDEX({R(sh,'N')},MATCH(EDATE({P['chaves']},120),{R(sh,'A')},0))",
     "p20": f"=INDEX({R(sh,'N')},MATCH(EDATE({P['chaves']},240),{R(sh,'A')},0))",
     "ok": f"='{sh}'!{aux['ok']}",
    }
finr = {
 "estrutura": '="SAC 120x a 12% a.a. + correção"',
 "credito": f"=INDEX({R(fin,'N')},MATCH({P['chaves']},{R(fin,'A')},0))",
 "sobra": '="-"',
 "obra": f"=-SUMIFS({R(fin,'X')},{R(fin,'A')},\"<=\"&{P['chaves']})",
 "parc_ini": '="-"',
 "parc_pos": f"=INDEX({R(fin,'M')},MATCH(1,{R(fin,'I')},0))",
 "fluxo1": f"=AVERAGEIFS({R(fin,'X')},{R(fin,'A')},\">=\"&{P['ini_op']},{R(fin,'A')},\"<\"&EDATE({P['ini_op']},12))",
 "aporte": f"=MIN({R(fin,'Y')})",
 "be_op": f"=IF(MIN({R(fin,'AC')})=0,{NA2},MIN({R(fin,'AC')}))",
 "be_cx": f"=IF(MIN({R(fin,'AD')})=0,{NA2},MIN({R(fin,'AD')}))",
 "be_pat": f"=IF(MIN({R(fin,'AE')})=0,{NA2},MIN({R(fin,'AE')}))",
 "fim": f"=EDATE({P['chaves']},{P['prazo']})",
 "pago": f"=SUM({R(fin,'M')})",
 "p10": f"=INDEX({R(fin,'AB')},MATCH(EDATE({P['chaves']},120),{R(fin,'A')},0))",
 "p20": f"=INDEX({R(fin,'AB')},MATCH(EDATE({P['chaves']},240),{R(fin,'A')},0))",
 "ok": '="-"',
}
rowsq = [
 ("Estrutura", "estrutura", '@'),
 ("Crédito líquido (consórcio) / saldo financiado (financiamento)", "credito", BRL),
 ("Crédito que sobra (+) ou falta (−) nas chaves", "sobra", BRL),
 ("Desembolso até as chaves (obra + consórcio + ITBI/lances)", "obra", BRL),
 ("Parcela do consórcio na adesão (reduzida)", "parc_ini", BRL),
 ("Parcela depois das chaves", "parc_pos", BRL),
 ("Fluxo de caixa médio no 1º ano de aluguel (mês)", "fluxo1", BRL),
 ("Aporte máximo acumulado", "aporte", BRL),
 ("Break-even operacional (aluguel cobre a parcela)", "be_op", DT),
 ("Break-even de caixa (caixa acumulado ≥ 0)", "be_cx", DT),
 ("Break-even patrimonial (vender devolve tudo)", "be_pat", DT),
 ("Última parcela", "fim", DT),
 ("Total pago em parcelas + lances (financiamento ou consórcio)", "pago", BRL),
 ("Posição se vender 10 anos após as chaves", "p10", BRL),
 ("Posição se vender 20 anos após as chaves", "p20", BRL),
 ("Checagem: contemplação até as chaves", "ok", '@'),
]
cA, cB = cons_rows("Consórcio A", auxA), cons_rows("Consórcio B", auxB)
for i, (lab, key, fmt) in enumerate(rowsq):
    rr = 5 + i
    wq.cell(row=rr, column=1, value=lab).font = f_norm
    for j, src_ in enumerate((finr, cA, cB)):
        c = wq.cell(row=rr, column=2+j, value=src_[key]); c.font = Font(name=F, size=10, bold=key.startswith("be_"))
        c.number_format = fmt; c.alignment = Alignment(horizontal="right")
    if key.startswith("be_"):
        for j in range(4): wq.cell(row=rr, column=1+j).fill = PatternFill("solid", fgColor="F3DFD5")
rn = 5 + len(rowsq) + 1
for t in [
 "Premissas do consórcio na aba Premissas (seção 6). Pontos de atenção:",
 "• A carta só quita imóvel com habite-se e matrícula individualizada: o crédito paga o saldo nas chaves, não a obra.",
 "• Cada carta precisa ser contemplada até as chaves. Com 5 cartas são 5 contemplações; com 2, são 2. Sem contemplação a tempo, o saldo teria de ser pago de outra forma.",
 "• Lance embutido reduz o crédito: com 30%, cada R$ 100 mil de carta libera R$ 70 mil (corrigidos).",
 "• Parcelas do consórcio começam na adesão (jan/27), somando-se às parcelas da obra.",
 "• Não inclui seguro prestamista nem rendimento do crédito parado entre a contemplação e as chaves.",
]:
    wq.cell(row=rn, column=1, value=t).font = Font(name=F, size=9, bold=t.endswith(":")); rn += 1
wq.column_dimensions["A"].width = 60
for col in "BCD": wq.column_dimensions[col].width = 24
wq.freeze_panes = "B5"
wq["C5"] = cA["estrutura"]; wq["D5"] = cB["estrutura"]


# =====================================================================
# Aba: Imóvel x Aplicação (carteira espelho)
# =====================================================================
wi = wb.create_sheet("Imóvel x Aplicação")
wi["A1"] = "Imóvel x aplicação financeira: carteira espelho"; wi["A1"].font = f_title
wi["A2"] = ("Cada real que o imóvel tira do bolso é aplicado; quando o imóvel devolve dinheiro, a aplicação resgata o mesmo valor. "
            "Mesmo esforço de caixa nos dois mundos. Compara-se o patrimônio: imóvel vendido (líquido) x saldo aplicado (líquido de IR).")
wi["A2"].font = Font(name=F, size=9, italic=True)
icols = [("A","Mês",9),("B","CDI do ano (a.a.)",9),("C","CDI líquido (mês)",9),("D","IPCA+ líquido (mês)",9)]
scen = [("Financiamento", "Fluxo mensal", "X", "AA"), ("Consórcio A", "Consórcio A", "K", "M"), ("Consórcio B", "Consórcio B", "K", "M")]
letters = ["E","F","G","H","I","J","K","L","M","N","O","P"]
k = 0
for nm, sh, fcol, pcol in scen:
    for suf, w in (("fluxo do imóvel",12),("saldo em CDI",13),("saldo em IPCA+",13),("imóvel: patrimônio se vender",14)):
        icols.append((letters[k], f"{nm}: {suf}", w)); k += 1
for col, h, w in icols:
    c = wi[f"{col}{HR}"]; c.value = h; c.font = f_head; c.fill = fill_head
    c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
    wi.column_dimensions[col].width = w
wi.row_dimensions[HR].height = 66
for idx in range(len(months)):
    r = first + idx; A = f"$A{r}"
    wi[f"A{r}"] = f"='Fluxo mensal'!A{r}"
    wi[f"B{r}"] = f"=IF(YEAR({A})<=2027,{P['cdi27']},IF(YEAR({A})=2028,{P['cdi28']},{P['cdi29']}))"
    wi[f"C{r}"] = f"=(1+B{r}*(1-{P['ir_aplic']}))^(1/12)-1"
    wi[f"D{r}"] = f"=(1+((1+{P['ipca_real']})*(1+{P['infl']})-1)*(1-{P['ir_aplic']}))^(1/12)-1"
    k = 0
    for nm, sh, fcol, pcol in scen:
        cf, cc, ci, cp = letters[k:k+4]
        wi[f"{cf}{r}"] = f"='{sh}'!{fcol}{r}"
        prevc = f"{cc}{r-1}" if idx > 0 else "0"; previ = f"{ci}{r-1}" if idx > 0 else "0"
        wi[f"{cc}{r}"] = f"={prevc}*(1+$C{r})-{cf}{r}"
        wi[f"{ci}{r}"] = f"={previ}*(1+$D{r})-{cf}{r}"
        wi[f"{cp}{r}"] = f"='{sh}'!{pcol}{r}"
        k += 4
    for col, _, _ in icols:
        c = wi[f"{col}{r}"]; c.font = f_norm
        c.number_format = DT if col == "A" else ('0.00%' if col in "BCD" else BRL)
wi.freeze_panes = f"B{first}"

# Quadro-resumo na aba Comparativo
rq = wq.max_row + 2
wq.cell(row=rq, column=1, value="Imóvel x aplicação: patrimônio no horizonte (mesmo dinheiro tirado do bolso)").font = f_bold
rq += 1
hdr = ["Horizonte / cenário", "Imóvel (vendido, líquido)", "Aplicação CDI (líquida)", "Aplicação IPCA+ (líquida)", "Melhor opção"]
for j, h in enumerate(hdr):
    c = wq.cell(row=rq, column=1+j, value=h); c.font = f_head; c.fill = fill_head
    c.alignment = Alignment(wrap_text=True, horizontal="center", vertical="center")
wq.row_dimensions[rq].height = 30
rq += 1
IA = "'Imóvel x Aplicação'"
def RI(col): return f"{IA}!${col}${first}:${col}${last}"
cols_s = {"Financiamento": ("F","G","H"), "Consórcio A": ("J","K","L"), "Consórcio B": ("N","O","P")}
for anos in (10, 15, 20, 30):
    for nm, (cc, ci, cp) in cols_s.items():
        dt = f"EDATE({P['chaves']},{anos*12})" if anos < 30 else f"DATE(2058,8,1)"
        wq.cell(row=rq, column=1, value=f"{anos} anos após as chaves · {nm}").font = f_norm
        fimv = f"=INDEX({RI(cp)},MATCH({dt},{RI('A')},0))"
        fcdi = f"=INDEX({RI(cc)},MATCH({dt},{RI('A')},0))"
        fipc = f"=INDEX({RI(ci)},MATCH({dt},{RI('A')},0))"
        for j, fml in enumerate((fimv, fcdi, fipc)):
            c = wq.cell(row=rq, column=2+j, value=fml); c.font = f_norm; c.number_format = BRL
        wq.cell(row=rq, column=5, value=f'=IF(B{rq}>=MAX(C{rq},D{rq}),"Imóvel",IF(C{rq}>=D{rq},"CDI","IPCA+"))').font = f_bold
        if nm == "Financiamento":
            for j in range(5): wq.cell(row=rq, column=1+j).border = Border(top=thin)
        rq += 1
wq.cell(row=rq+1, column=1, value="Aplicação: saldo líquido de IR (15%). Imóvel: valor de mercado - corretagem - saldo devedor - IR sobre ganho de capital. Não considera aluguel imputado nem liquidez.").font = Font(name=F, size=9)
wq.column_dimensions["E"].width = 14

# =====================================================================
# Aba 4: Resumo
# =====================================================================
ws = wb.create_sheet("Resumo financiamento", 1)
ws["A1"] = "SAMPA 135 - Financiamento direto: viabilidade e break-even"; ws["A1"].font = f_title
ws["A2"] = "Valores nominais em R$. Todos os números vêm das abas Premissas e Fluxo mensal; mude as premissas e tudo recalcula."
ws["A2"].font = Font(name=F, size=9, italic=True)
NA = '"Não atinge até dez/58"'
items = [
 ("Unidade", None),
 ("Final", f"={P['final']}", None),
 ("Área privativa (m²)", f"={P['area']}", '0.00'),
 ("Preço de tabela", f"={P['preco']}", BRL),
 ("Preço por m²", f"={P['precom2']}", BRL),
 ("Até as chaves (jan/27 a ago/28)", None),
 ("Pago à incorporadora até as chaves (corrigido INCC)", f"=SUMIFS({rng('F')},{rng('A')},\"<=\"&{P['chaves']})", BRL),
 ("ITBI + registro", f"=SUM({rng('G')})", BRL),
 ("Mobília", f"=SUM({rng('H')})", BRL),
 ("Saldo financiado nas chaves (corrigido INCC)", f"=INDEX({rng('N')},MATCH({P['chaves']},{rng('A')},0))", BRL),
 ("Operação", None),
 ("Início do aluguel", f"={P['ini_op']}", DT),
 ("1ª parcela do financiamento", f"=INDEX({rng('M')},MATCH(1,{rng('I')},0))", BRL),
 ("Resultado mensal do imóvel após IR (1º mês pós ramp-up)", f"=INDEX({rng('W')},MATCH(EDATE({P['ini_op']},{P['ramp_m']}),{rng('A')},0))", BRL),
 ("Fluxo de caixa médio no 1º ano de aluguel (mês)", f"=AVERAGEIFS({rng('X')},{rng('A')},\">=\"&{P['ini_op']},{rng('A')},\"<\"&EDATE({P['ini_op']},12))", BRL),
 ("Aporte máximo acumulado (pior momento do caixa)", f"=MIN({rng('Y')})", BRL),
 ("Mês do aporte máximo", f"=INDEX({rng('A')},MATCH(MIN({rng('Y')}),{rng('Y')},0))", DT),
 ("Break-even", None),
 ("1) Operacional: aluguel líquido cobre a parcela", f"=IF(MIN({rng('AC')})=0,{NA},MIN({rng('AC')}))", DT),
 ("2) Caixa: dinheiro investido volta (caixa acumulado ≥ 0)", f"=IF(MIN({rng('AD')})=0,{NA},MIN({rng('AD')}))", DT),
 ("3) Patrimonial: vender devolve tudo (caixa + patrimônio ≥ 0)", f"=IF(MIN({rng('AE')})=0,{NA},MIN({rng('AE')}))", DT),
 ("Fim do financiamento", f"=EDATE({P['chaves']},{P['prazo']})", DT),
 ("Fotografias", None),
 ("Posição se vender 5 anos após as chaves", f"=INDEX({rng('AB')},MATCH(EDATE({P['chaves']},60),{rng('A')},0))", BRL),
 ("Posição se vender 10 anos após as chaves", f"=INDEX({rng('AB')},MATCH(EDATE({P['chaves']},120),{rng('A')},0))", BRL),
 ("Posição se vender 20 anos após as chaves", f"=INDEX({rng('AB')},MATCH(EDATE({P['chaves']},240),{rng('A')},0))", BRL),
]
r = 4
for it in items:
    if len(it) == 2 and it[1] is None:
        r += 1
        ws[f"A{r}"] = it[0]; ws[f"A{r}"].font = f_bold
        ws[f"A{r}"].fill = fill_sub; ws[f"B{r}"].fill = fill_sub
        r += 1; continue
    lab, fml, fmt = it
    ws[f"A{r}"] = lab; ws[f"A{r}"].font = f_norm
    ws[f"B{r}"] = fml; ws[f"B{r}"].font = Font(name=F, size=10, bold=lab[:2] in ("1)", "2)", "3)"))
    if fmt: ws[f"B{r}"].number_format = fmt
    ws[f"B{r}"].alignment = Alignment(horizontal="right")
    r += 1
r += 1
notes = [
 "Como ler:",
 "• Posição total = caixa acumulado (tudo que entrou menos tudo que saiu) + quanto sobraria vendendo o imóvel (após corretagem, saldo devedor e IR sobre o ganho).",
 "• Break-even patrimonial é o indicador do objetivo de alavancagem de patrimônio: a partir daí, vender devolve todo o dinheiro colocado.",
 "• Não inclui custo de oportunidade do dinheiro (ex.: o que o capital renderia no CDI).",
 "• Premissas não informadas pelo usuário (INCC, indexador pós-chaves, diária, ocupação, condomínio, mobília, valorização) estão na aba Premissas com a origem de cada número.",
]
for n in notes:
    ws[f"A{r}"] = n; ws[f"A{r}"].font = Font(name=F, size=9, bold=n.endswith(":")); r += 1
ws.column_dimensions["A"].width = 62; ws.column_dimensions["B"].width = 22

# gráfico: caixa acumulado e posição total
ch = LineChart()
ch.title = "Caixa acumulado x posição total (R$)"
ch.height = 9; ch.width = 20
data = Reference(wf, min_col=25, max_col=25, min_row=HR, max_row=last)    # Y
data2 = Reference(wf, min_col=28, max_col=28, min_row=HR, max_row=last)   # AB
ch.add_data(data, titles_from_data=True); ch.add_data(data2, titles_from_data=True)
ch.set_categories(Reference(wf, min_col=1, min_row=first, max_row=last))
ch.y_axis.number_format = 'R$ #,##0'; ch.x_axis.number_format = 'yyyy'
ch.y_axis.title = None; ch.x_axis.tickLblSkip = 24
ch.series[0].graphicalProperties.line.solidFill = "B4441F"
ch.series[1].graphicalProperties.line.solidFill = "2F6B3A"
ch.series[0].graphicalProperties.line.width = 22000; ch.series[1].graphicalProperties.line.width = 22000
ch.series[0].smooth = False; ch.series[1].smooth = False
ws.add_chart(ch, "D4")

wb.save(OUT)
print("ok", OUT, "linhas", first, last)
