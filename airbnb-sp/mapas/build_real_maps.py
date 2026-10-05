"""Gera mapas coropléticos reais dos 96 distritos de SP (malha GeoSampa) em SVG.

Para cada indicador: mapa da cidade inteira + zoom do centro expandido com nomes.
Classes (5 = maior, verde ... 1 = menor, vermelho) vêm de build_maps.py.
"""
import json, math, unicodedata
from shapely.geometry import shape, box
from shapely import affinity

import build_maps as bm  # reaproveita classes, marcações de dado medido e nomes

# Malha oficial (GeoSampa) via https://github.com/codigourbano/distritos-sp — clone e ajuste o caminho
GEO = "/home/user/codigourbano/distritos-sp/distritos-sp.geojson"
COL = {5: "#1a9850", 4: "#91cf60", 3: "#fee08b", 2: "#fc8d59", 1: "#d73027"}
TXT = {5: "#ffffff", 4: "#1c1b19", 3: "#1c1b19", 2: "#1c1b19", 1: "#ffffff"}
K = math.cos(math.radians(23.6))  # correção de escala da longitude


def norm(s):
    return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().upper()


name_by_norm = {norm(n): n for n in bm.C}
geoms = {}
for f in json.load(open(GEO))["features"]:
    n = name_by_norm[norm(f["properties"]["ds_nome"])]
    geoms[n] = shape(f["geometry"])
assert len(geoms) == 96

# Rótulos curtos para o zoom (nomes longos quebram em 2 linhas)
SHORT = {"Jardim Paulista": "Jardim\nPaulista", "Alto de Pinheiros": "Alto de\nPinheiros", "Vila Leopoldina": "Vila\nLeopoldina",
         "Vila Mariana": "Vila\nMariana", "Santa Cecília": "Santa\nCecília", "Barra Funda": "Barra\nFunda",
         "Bela Vista": "Bela\nVista", "Bom Retiro": "Bom\nRetiro", "Itaim Bibi": "Itaim\nBibi", "Campo Belo": "Campo\nBelo",
         "Santo Amaro": "Santo\nAmaro", "Vila Andrade": "Vila\nAndrade", "Vila Sônia": "Vila\nSônia", "Água Rasa": "Água\nRasa",
         "Vila Prudente": "Vila\nPrudente", "Vila Guilherme": "Vila\nGuilherme", "Casa Verde": "Casa\nVerde",
         "Rio Pequeno": "Rio\nPequeno", "Vila Formosa": "Vila\nFormosa", "São Lucas": "São\nLucas",
         "Freguesia do Ó": "Freguesia\ndo Ó", "Vila Maria": "Vila\nMaria", "Campo Grande": "Campo\nGrande",
         "Cidade Ademar": "Cidade\nAdemar", "Jardim São Luís": "Jardim\nSão Luís", "Campo Limpo": "Campo\nLimpo"}


LABEL_DXY = {"República": (-6, -9), "Sé": (5, 4), "Consolação": (-10, 4), "Liberdade": (2, 4), "Bela Vista": (-2, 3)}


def project(g, bounds, width):
    """Projeta (lon, lat) para pixels dentro de 'bounds', com largura 'width'."""
    minx, miny, maxx, maxy = bounds
    sx = width / ((maxx - minx) * K)
    g = affinity.translate(g, -minx, -maxy)
    g = affinity.scale(g, xfact=K * sx, yfact=-sx, origin=(0, 0))
    return g, (maxy - miny) * sx


def path_d(g):
    polys = [g] if g.geom_type == "Polygon" else list(g.geoms)
    out = []
    for p in polys:
        for ring in [p.exterior, *p.interiors]:
            pts = list(ring.coords)
            out.append("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z")
    return "".join(out)


def svg_map(values, measured, bounds, width, labels=False, tol=0.0012, frame=None):
    clip = box(*bounds)
    parts, lbls = [], []
    height = None
    for n, g in geoms.items():
        gg = g.simplify(tol, preserve_topology=True)
        if labels:
            gg = gg.intersection(clip)
            if gg.is_empty:
                continue
        pg, height = project(gg, bounds, width)
        v = values[n]
        parts.append(f'<path d="{path_d(pg)}" fill="{COL[v]}" stroke="#ffffff" stroke-width="{0.9 if labels else 0.5}"><title>{n}</title></path>')
        if labels:
            area_px = pg.area
            inside = g.intersection(clip).area / g.area
            if area_px < 700 or inside < 0.45:  # pequeno demais ou quase fora do zoom
                continue
            pt = g.intersection(clip).representative_point()
            pp, _ = project(pt, bounds, width)
            dx, dy = LABEL_DXY.get(n, (0, 0))
            pp = type(pp)(pp.x + dx, pp.y + dy)
            txt = SHORT.get(n, n).split("\n")
            mark = "● " if n in measured else ""
            y0 = pp.y - (len(txt) - 1) * 5.5
            spans = "".join(f'<tspan x="{pp.x:.1f}" y="{y0 + i*11 + 3.5:.1f}">{(mark if i == 0 else "") + t}</tspan>' for i, t in enumerate(txt))
            lbls.append(f'<text text-anchor="middle" font-size="9.5" font-weight="700" fill="{TXT[v]}">{spans}</text>')
    if frame is not None:  # retângulo do zoom no mapa da cidade
        fb = box(*frame)
        pf, _ = project(fb, bounds, width)
        x0, y0, x1, y1 = pf.bounds
        parts.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{x1-x0:.1f}" height="{y1-y0:.1f}" fill="none" stroke="#1c1b19" stroke-width="1.6" stroke-dasharray="4 3"/>')
    if not labels:  # marca dos dados medidos no mapa da cidade
        for n in measured:
            pt = geoms[n].representative_point()
            pp, _ = project(pt, bounds, width)
            parts.append(f'<circle cx="{pp.x:.1f}" cy="{pp.y:.1f}" r="2.4" fill="#1c1b19" stroke="#fff" stroke-width="0.8"/>')
    return (f'<svg viewBox="0 0 {width} {height:.0f}" width="{width}" height="{height:.0f}" xmlns="http://www.w3.org/2000/svg" '
            f'font-family="Inter, Liberation Sans, sans-serif">' + "".join(parts) + "".join(lbls) + "</svg>")


from shapely.ops import unary_union
city = unary_union(list(geoms.values()))
CITY = city.bounds
ZOOM = (-46.765, -23.655, -46.570, -23.505)  # centro expandido (oeste, sul, leste, norte)

DATA = {"airbnb": (bm.airbnb, bm.airbnb_measured), "diaria": (bm.diaria, bm.diaria_measured), "lanc": (bm.lanc, bm.lanc_measured)}
out = {}
for k, (vals, meas) in DATA.items():
    out[k] = {"city": svg_map(vals, meas, CITY, 300, frame=ZOOM),
              "zoom": svg_map(vals, meas, ZOOM, 470, labels=True, tol=0.0004)}
json.dump(out, open("real_maps.json", "w"), ensure_ascii=False)
print({k: (len(v["city"]) // 1024, len(v["zoom"]) // 1024) for k, v in out.items()}, "KB")
