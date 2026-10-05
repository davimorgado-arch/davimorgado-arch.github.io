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
# Aba 4: Resumo
# =====================================================================
ws = wb.create_sheet("Resumo", 0)
ws["A1"] = "SAMPA 135 - Viabilidade e break-even do studio para Airbnb"; ws["A1"].font = f_title
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
