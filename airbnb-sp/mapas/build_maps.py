"""Gera 3 mapas esquemáticos (tile map) dos 96 distritos de SP em SVG.

Cada distrito vira um quadrado posicionado pelo centróide aproximado
(lat/lon), encaixado numa grade. Cor em 5 classes, verde (maior) -> vermelho (menor).
"""
import json, math

# Centróides aproximados (lat, lon) dos 96 distritos oficiais
C = {
 # Centro
 "Sé":(-23.550,-46.634),"República":(-23.544,-46.642),"Bela Vista":(-23.561,-46.648),
 "Consolação":(-23.553,-46.660),"Santa Cecília":(-23.536,-46.652),"Bom Retiro":(-23.527,-46.637),
 "Liberdade":(-23.563,-46.633),"Cambuci":(-23.566,-46.618),"Brás":(-23.545,-46.617),"Pari":(-23.527,-46.616),
 # Oeste
 "Barra Funda":(-23.522,-46.664),"Perdizes":(-23.535,-46.678),"Jardim Paulista":(-23.571,-46.661),
 "Pinheiros":(-23.567,-46.691),"Itaim Bibi":(-23.587,-46.677),"Alto de Pinheiros":(-23.552,-46.712),
 "Lapa":(-23.522,-46.704),"Vila Leopoldina":(-23.530,-46.732),"Jaguaré":(-23.546,-46.748),
 "Butantã":(-23.571,-46.721),"Morumbi":(-23.600,-46.718),"Vila Sônia":(-23.599,-46.738),
 "Rio Pequeno":(-23.567,-46.758),"Raposo Tavares":(-23.590,-46.778),"Jaguara":(-23.509,-46.749),
 # Sul
 "Vila Mariana":(-23.589,-46.636),"Moema":(-23.602,-46.664),"Saúde":(-23.616,-46.637),
 "Campo Belo":(-23.623,-46.670),"Santo Amaro":(-23.645,-46.700),"Jabaquara":(-23.645,-46.645),
 "Cursino":(-23.618,-46.613),"Ipiranga":(-23.590,-46.605),"Sacomã":(-23.613,-46.596),
 "Vila Andrade":(-23.630,-46.735),"Campo Grande":(-23.677,-46.687),"Cidade Ademar":(-23.672,-46.655),
 "Pedreira":(-23.700,-46.660),"Socorro":(-23.680,-46.705),"Jardim São Luís":(-23.665,-46.745),
 "Campo Limpo":(-23.645,-46.765),"Capão Redondo":(-23.670,-46.780),"Jardim Ângela":(-23.712,-46.770),
 "Cidade Dutra":(-23.720,-46.700),"Grajaú":(-23.765,-46.690),"Parelheiros":(-23.850,-46.720),
 "Marsilac":(-23.950,-46.700),
 # Norte
 "Santana":(-23.500,-46.628),"Casa Verde":(-23.505,-46.660),"Limão":(-23.500,-46.678),
 "Vila Guilherme":(-23.510,-46.605),"Vila Maria":(-23.505,-46.585),"Tucuruvi":(-23.475,-46.606),
 "Mandaqui":(-23.475,-46.630),"Vila Medeiros":(-23.485,-46.583),"Jaçanã":(-23.460,-46.578),
 "Tremembé":(-23.440,-46.610),"Cachoeirinha":(-23.470,-46.665),"Freguesia do Ó":(-23.495,-46.695),
 "Brasilândia":(-23.465,-46.690),"Pirituba":(-23.480,-46.730),"São Domingos":(-23.495,-46.745),
 "Jaraguá":(-23.450,-46.745),"Perus":(-23.405,-46.750),"Anhanguera":(-23.420,-46.785),
 # Leste
 "Mooca":(-23.557,-46.598),"Belém":(-23.540,-46.595),"Tatuapé":(-23.540,-46.575),
 "Água Rasa":(-23.563,-46.578),"Vila Prudente":(-23.585,-46.580),"São Lucas":(-23.598,-46.555),
 "Carrão":(-23.553,-46.545),"Vila Formosa":(-23.570,-46.545),"Aricanduva":(-23.575,-46.515),
 "Penha":(-23.525,-46.545),"Vila Matilde":(-23.535,-46.525),"Cangaíba":(-23.505,-46.525),
 "Ponte Rasa":(-23.510,-46.500),"Artur Alvim":(-23.545,-46.490),"Cidade Líder":(-23.560,-46.490),
 "Sapopemba":(-23.605,-46.515),"São Rafael":(-23.625,-46.470),"Parque do Carmo":(-23.580,-46.470),
 "Itaquera":(-23.545,-46.455),"José Bonifácio":(-23.555,-46.425),"São Mateus":(-23.600,-46.475),
 "Iguatemi":(-23.610,-46.425),"Cidade Tiradentes":(-23.585,-46.400),"Guaianases":(-23.545,-46.405),
 "Lajeado":(-23.535,-46.380),"Ermelino Matarazzo":(-23.500,-46.480),"Vila Jacuí":(-23.505,-46.460),
 "São Miguel":(-23.495,-46.440),"Jardim Helena":(-23.485,-46.420),"Vila Curuçá":(-23.505,-46.415),
 "Itaim Paulista":(-23.500,-46.395),
}
assert len(C) == 96, len(C)

# Siglas de 3 letras (únicas) para caber no quadrado
AB = {
 "Sé":"SÉ","República":"REP","Bela Vista":"BVI","Consolação":"CON","Santa Cecília":"SCE","Bom Retiro":"BRE",
 "Liberdade":"LIB","Cambuci":"CBC","Brás":"BRÁ","Pari":"PAR","Barra Funda":"BFU","Perdizes":"PER",
 "Jardim Paulista":"JDP","Pinheiros":"PIN","Itaim Bibi":"IBI","Alto de Pinheiros":"API","Lapa":"LAP",
 "Vila Leopoldina":"VLE","Jaguaré":"JGR","Butantã":"BUT","Morumbi":"MOR","Vila Sônia":"VSO",
 "Rio Pequeno":"RPE","Raposo Tavares":"RTA","Jaguara":"JGA","Vila Mariana":"VMA","Moema":"MOE",
 "Saúde":"SAU","Campo Belo":"CBE","Santo Amaro":"SAM","Jabaquara":"JAB","Cursino":"CUR","Ipiranga":"IPI",
 "Sacomã":"SAC","Vila Andrade":"VAN","Campo Grande":"CGR","Cidade Ademar":"CAD","Pedreira":"PED",
 "Socorro":"SOC","Jardim São Luís":"JSL","Campo Limpo":"CLI","Capão Redondo":"CRE","Jardim Ângela":"JAN",
 "Cidade Dutra":"CDU","Grajaú":"GRA","Parelheiros":"PLH","Marsilac":"MAR","Santana":"SAN",
 "Casa Verde":"CVE","Limão":"LIM","Vila Guilherme":"VGU","Vila Maria":"VMR","Tucuruvi":"TUC",
 "Mandaqui":"MAN","Vila Medeiros":"VME","Jaçanã":"JAÇ","Tremembé":"TRE","Cachoeirinha":"CAC",
 "Freguesia do Ó":"FÓ","Brasilândia":"BRL","Pirituba":"PIR","São Domingos":"SDO","Jaraguá":"JRG",
 "Perus":"PRS","Anhanguera":"ANH","Mooca":"MOO","Belém":"BEL","Tatuapé":"TAT","Água Rasa":"ÁRA",
 "Vila Prudente":"VPR","São Lucas":"SLU","Carrão":"CAR","Vila Formosa":"VFO","Aricanduva":"ARI",
 "Penha":"PEN","Vila Matilde":"VMT","Cangaíba":"CAN","Ponte Rasa":"PRA","Artur Alvim":"AAL",
 "Cidade Líder":"CLD","Sapopemba":"SAP","São Rafael":"SRA","Parque do Carmo":"PCA","Itaquera":"ITQ",
 "José Bonifácio":"JBO","São Mateus":"SMA","Iguatemi":"IGU","Cidade Tiradentes":"CTI","Guaianases":"GUA",
 "Lajeado":"LAJ","Ermelino Matarazzo":"EMA","Vila Jacuí":"VJA","São Miguel":"SMI","Jardim Helena":"JHE",
 "Vila Curuçá":"VCU","Itaim Paulista":"IPA",
}
assert len(set(AB.values())) == 96

# ---------- Layout manual (coluna, linha), oeste->leste, norte->sul ----------
GRID = """
r0: PRS3 TRE9 JAÇ10
r1: ANH2 JRG3 BRL5 CAC6 MAN8 TUC9 VME10
r2: PIR3 SDO4 FÓ5 LIM6 CVE7 SAN8 VGU9 VMR10 CAN12 EMA13 VJA14 SMI15 JHE16
r3: JGA3 VLE4 LAP5 BFU6 SCE7 BRE8 PAR9 BEL10 TAT11 PEN12 VMT13 PRA14 VCU15 IPA16
r4: JGR3 API4 PER5 CON6 REP7 SÉ8 BRÁ9 MOO10 ÁRA11 CAR12 AAL13 ITQ14 GUA15 LAJ16
r5: RPE2 BUT3 PIN4 JDP5 BVI6 LIB7 CBC8 IPI9 VPR10 VFO11 ARI12 CLD13 PCA14 JBO15 CTI16
r6: RTA1 VSO2 MOR3 IBI4 MOE5 VMA6 CUR7 SAC8 SLU10 SAP12 SMA13 SRA14 IGU15
r7: CLI1 VAN2 SAM3 CBE4 JAB5 SAU6
r8: CRE1 JSL2 SOC3 CGR4 CAD5
r9: JAN1 CDU3 PED5
r10: GRA3
r11: PLH2
r12: MAR3
"""
import re
code2name = {v: k for k, v in AB.items()}
pos = {}
for line in GRID.strip().splitlines():
    row, cells = line.split(":")
    r = int(row[1:])
    for tok in cells.split():
        m = re.match(r"(.+?)(\d+)$", tok)
        pos[code2name[m.group(1)]] = (int(m.group(2)), r)
assert len(pos) == 96 and len(set(pos.values())) == 96, (len(pos), len(set(pos.values())))
W = max(p[0] for p in pos.values()) + 1; H = max(p[1] for p in pos.values()) + 1

# ---------- Dados (classe 5 = maior ... 1 = menor) ----------
def tiers(spec, default=1):
    out = {n: default for n in C}
    for t, names in spec.items():
        for n in names:
            assert n in C, n
            out[n] = t
    return out

# 1) Oferta de Airbnb (anúncios ativos). Medido: Itaim Bibi 4.382 (10,3%), top-3 Itaim/República/Jd Paulista (Inside Airbnb jun/26)
airbnb = tiers({
 5: ["Itaim Bibi","República","Jardim Paulista","Pinheiros","Bela Vista","Consolação"],
 4: ["Vila Mariana","Moema","Santa Cecília","Perdizes","Sé","Liberdade","Santo Amaro","Campo Belo"],
 3: ["Saúde","Butantã","Vila Andrade","Lapa","Barra Funda","Alto de Pinheiros","Morumbi","Bom Retiro","Cambuci",
     "Mooca","Tatuapé","Santana","Brás","Ipiranga","Vila Leopoldina","Jabaquara","Vila Sônia"],
 2: ["Belém","Água Rasa","Vila Prudente","Cursino","Sacomã","Casa Verde","Vila Guilherme","Pari","Rio Pequeno","Jaguaré",
     "Campo Grande","Socorro","Tucuruvi","Mandaqui","Penha","Carrão","Vila Formosa","Freguesia do Ó","Limão",
     "Cidade Ademar","Raposo Tavares","Vila Maria","São Lucas","Jardim São Luís","Campo Limpo"],
})
airbnb_measured = {"Itaim Bibi","República","Jardim Paulista"}

# 2) Diária média do Airbnb. Medido (mediana de mercado, US$->R$): Itaim ~590, Pinheiros ~520, Jd Paulista ~490, Moema ~445, Consolação ~400
diaria = tiers({
 5: ["Itaim Bibi","Pinheiros","Jardim Paulista"],
 4: ["Moema","Consolação","Alto de Pinheiros","Campo Belo","Santo Amaro","Vila Mariana","Perdizes","Morumbi"],
 3: ["Bela Vista","Santa Cecília","Vila Andrade","Butantã","Saúde","Lapa","Barra Funda","Vila Leopoldina","Vila Sônia",
     "Tatuapé","República","Liberdade"],
 2: ["Sé","Mooca","Ipiranga","Santana","Jabaquara","Cambuci","Bom Retiro","Brás","Água Rasa","Belém","Cursino",
     "Rio Pequeno","Jaguaré","Casa Verde","Campo Grande","Socorro","Vila Prudente","Tucuruvi","Mandaqui","Carrão",
     "Vila Formosa","Penha"],
})
diaria_measured = {"Itaim Bibi","Pinheiros","Jardim Paulista","Moema","Consolação"}

# 3) Oferta de imóveis novos (lançamentos residenciais). Medido: V. Mariana 4.748, Mooca 4.600+, Barra Funda 3.484 (2024),
#    Saúde 3.408, Moema 3.020, Pinheiros 2.785, Perdizes 617
# Base: periferia 2 (lançamentos econômicos pontuais), extremo sul 1; depois sobe para 3, 4, 5
base = {n: (1 if n in ("Marsilac","Parelheiros") else 2) for n in C}
for t, names in [(3, ["Itaim Bibi","Jardim Paulista","Bela Vista","Consolação","Santa Cecília","Água Rasa","Vila Prudente",
                      "Cambuci","Liberdade","República","Brás","Santana","Jabaquara","Cursino","Sacomã","Vila Sônia",
                      "Campo Grande","Penha","Carrão","Casa Verde","Alto de Pinheiros","Morumbi","Sé","Bom Retiro",
                      "Vila Formosa","São Lucas","Perdizes"]),
                 (4, ["Pinheiros","Tatuapé","Santo Amaro","Campo Belo","Butantã","Vila Leopoldina","Ipiranga",
                      "Lapa","Belém","Vila Andrade"]),
                 (5, ["Vila Mariana","Mooca","Saúde","Barra Funda","Moema"])]:
    for n in names:
        assert n in C, n
        base[n] = t
lanc = base
lanc_measured = {"Vila Mariana","Mooca","Barra Funda","Saúde","Moema","Pinheiros","Perdizes"}

# ---------- Cores: verde (5) -> vermelho (1) ----------
COL = {5:"#1a9850", 4:"#91cf60", 3:"#fee08b", 2:"#fc8d59", 1:"#d73027"}
TXT = {5:"#ffffff", 4:"#1c1b19", 3:"#1c1b19", 2:"#1c1b19", 1:"#ffffff"}

def svg(values, measured, tile=29, gap=2):
    w, h = W * tile, H * tile
    out = [f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg" '
           f'font-family="Inter, Liberation Sans, sans-serif">']
    for n, (x, y) in pos.items():
        v = values[n]; px, py = x * tile, y * tile; s = tile - gap
        out.append(f'<g><title>{n}</title><rect x="{px}" y="{py}" width="{s}" height="{s}" rx="4" fill="{COL[v]}"/>')
        out.append(f'<text x="{px + s/2}" y="{py + s/2 + 3.2}" text-anchor="middle" font-size="9" font-weight="700" '
                   f'fill="{TXT[v]}">{AB[n]}</text>')
        if n in measured:  # marca de dado medido
            out.append(f'<circle cx="{px + s - 4.5}" cy="{py + 4.5}" r="2.6" fill="#1c1b19" stroke="#fff" stroke-width="1"/>')
        out.append('</g>')
    out.append('</svg>')
    return "\n".join(out)

maps = {
    "airbnb": svg(airbnb, airbnb_measured),
    "diaria": svg(diaria, diaria_measured),
    "lanc": svg(lanc, lanc_measured),
}
json.dump({"AB": AB, "W": W, "H": H, "maps": maps,
           "counts": {k: {t: sum(1 for v in d.values() if v == t) for t in range(1, 6)}
                      for k, d in (("airbnb", airbnb), ("diaria", diaria), ("lanc", lanc))}},
          open("maps.json", "w"), ensure_ascii=False)
print("grid", W, "x", H)
