#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
muestrear_colores.py — Lee el color real de cada barra en los PNG originales
de los graficos.

El color no es un dato que se pueda deducir del texto del informe, y pedirle
a un modelo que lo clasifique "a ojo" es justo el tipo de suposicion que este
encargo no admite. Aqui se mide: se detectan las barras por bandas de color
uniforme y se asigna cada una al color de la paleta mas cercano.

    python3 muestrear_colores.py graficos_png/

Escribe colores_graficos.json: {gID: [color, color, ...]} en el orden en que
las barras aparecen en la imagen, de arriba abajo.
"""

import json
import os
import sys
from collections import Counter

from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))

# Paleta del informe. El nombre es el que build.py traduce a variable CSS.
PALETA = {
    "blue":   (0x2a, 0x78, 0xd6),
    "orange": (0xeb, 0x68, 0x34),
    "aqua":   (0x1b, 0xaf, 0x7a),
    "red":    (0xd0, 0x3b, 0x3b),
    "dim":    (0xb9, 0xbe, 0xc7),
    "base":   (0xc3, 0xc2, 0xb7),
    "navy":   (0x1d, 0x20, 0x27),
}

BLANCO = (255, 255, 255)


def dist(a, b):
    return sum((a[i] - b[i]) ** 2 for i in range(3))


def clasificar(rgb, tolerancia=2600):
    """Color de la paleta mas cercano, o None si no se parece a ninguno."""
    mejor, d = None, None
    for nombre, ref in PALETA.items():
        dd = dist(rgb, ref)
        if d is None or dd < d:
            mejor, d = nombre, dd
    return mejor if d <= tolerancia else None


def barras_de(ruta, min_ancho=2):
    """Detecta las barras: rachas horizontales de un color de la paleta que se
    repiten en filas consecutivas. Recoge TODAS las rachas de cada fila, para
    no perder ni las barras cortas ni los segmentos de una barra apilada.
    Devuelve [{y, x, ancho, alto, rgb, color}] ordenado por y y luego por x."""
    im = Image.open(ruta).convert("RGB")
    W, H = im.size
    px = im.load()

    # rachas por fila
    por_fila = []
    for y in range(H):
        rachas = []
        x = 0
        while x < W:
            c = px[x, y]
            if c[0] > 246 and c[1] > 246 and c[2] > 246:
                x += 1
                continue
            x0 = x
            while x < W and px[x, y] == c:
                x += 1
            ancho = x - x0
            if ancho >= min_ancho:
                nombre = clasificar(c)
                if nombre:
                    rachas.append((x0, ancho, c, nombre))
        por_fila.append(rachas)

    # unir rachas equivalentes en filas consecutivas
    abiertas, cerradas = [], []
    for y in range(H):
        usadas = set()
        siguientes = []
        for b in abiertas:
            enc = None
            for i, (x0, ancho, c, nombre) in enumerate(por_fila[y]):
                if i in usadas:
                    continue
                if c == b["c"] and abs(x0 - b["x0"]) <= 2 and abs(ancho - b["ancho"]) <= 2:
                    enc = i
                    break
            if enc is None:
                cerradas.append(b)
            else:
                usadas.add(enc)
                b["y1"] = y
                b["n"] += 1
                siguientes.append(b)
        for i, (x0, ancho, c, nombre) in enumerate(por_fila[y]):
            if i in usadas:
                continue
            siguientes.append({"y0": y, "y1": y, "x0": x0, "ancho": ancho,
                               "c": c, "nombre": nombre, "n": 1})
        abiertas = siguientes
    cerradas.extend(abiertas)

    salida = []
    for b in cerradas:
        alto = b["y1"] - b["y0"] + 1
        if alto < 8:            # descarta reglas, ejes y bordes finos
            continue
        if b["ancho"] > W * 0.97:
            continue
        salida.append({
            "y": (b["y0"] + b["y1"]) // 2,
            "x": b["x0"],
            "ancho": b["ancho"],
            "alto": alto,
            "rgb": "#%02x%02x%02x" % b["c"],
            "color": b["nombre"],
        })
    salida.sort(key=lambda d: (d["y"], d["x"]))
    return salida, (W, H)


def main():
    carpeta = sys.argv[1] if len(sys.argv) > 1 else os.path.join(AQUI, "graficos_png")
    res = {}
    for gid in ["g%d" % i for i in range(1, 11)]:
        ruta = os.path.join(carpeta, gid + ".png")
        if not os.path.exists(ruta):
            print(gid, "— falta la imagen")
            continue
        barras, (W, H) = barras_de(ruta)
        res[gid] = barras
        cuenta = Counter(b["color"] for b in barras)
        print("%-4s %3d barras  %s" % (gid, len(barras), dict(cuenta)))

    json.dump(res, open(os.path.join(AQUI, "colores_graficos.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\ncolores_graficos.json escrito")


if __name__ == "__main__":
    main()


# ==========================================================================
#  Emparejado con graficos.json
# ==========================================================================

def _modal(vals):
    h = {}
    for v in vals:
        h[v] = h.get(v, 0) + 1
    return max(h, key=lambda k: (h[k], k))


def _es_muestra_leyenda(b):
    return b["ancho"] <= 32 and abs(b["ancho"] - b["alto"]) <= 8


def _horizontales(cand, esperado=None):
    """Barras horizontales: comparten borde (izquierdo o derecho) y, dentro de
    cada grupo, un mismo grosor. Un grafico puede tener dos grupos con grosores
    distintos (dos paneles), asi que el numero de barras esperado decide cuales
    se aceptan; los trazos de texto quedan fuera por ser mas finos."""
    bruto = {}
    for b in cand:
        bruto.setdefault(("i", b["x"] // 3), []).append(b)
        bruto.setdefault(("d", (b["x"] + b["ancho"]) // 3), []).append(b)

    grupos = []
    for _, miembros in bruto.items():
        if len(miembros) < 2:
            continue
        grosor = _modal([m["alto"] for m in miembros])
        if grosor < 15:
            continue
        limpios = [m for m in miembros
                   if abs(m["alto"] - grosor) <= 3 and not _es_muestra_leyenda(m)]
        if len(limpios) >= 2:
            grupos.append((grosor, limpios))

    # los grupos mas gruesos son las barras; los finos, restos de tipografia
    grupos.sort(key=lambda g: (-g[0], -len(g[1])))

    def unir(sel):
        vistos, out = set(), []
        for _, miembros in sel:
            for m in miembros:
                k = (m["y"], m["x"])
                if k not in vistos:
                    vistos.add(k)
                    out.append(m)
        return out

    if esperado:
        sel = []
        for g in grupos:
            if len(unir(sel + [g])) <= esperado:
                sel.append(g)
            if len(unir(sel)) == esperado:
                return unir(sel)
    return unir(grupos)


def _verticales(cand):
    """Barras verticales (columnas): comparten anchura y linea de base."""
    # una columna es ancha; los trazos de la tipografia no
    aptos = [b for b in cand
             if b["alto"] >= 15 and b["ancho"] >= 20 and not _es_muestra_leyenda(b)]
    if len(aptos) < 2:
        return []
    anchura = _modal([b["ancho"] for b in aptos])
    col = [b for b in aptos if abs(b["ancho"] - anchura) <= 3]
    if len(col) < 2:
        return []
    base = _modal([(b["y"] + b["alto"] // 2) // 6 for b in col])
    col = [b for b in col if abs((b["y"] + b["alto"] // 2) // 6 - base) <= 1]
    return col


def filtrar_barras(det, esperado=None):
    """Separa las barras reales de los trazos de texto y de las muestras de
    leyenda. Prueba la lectura horizontal y la vertical, y se queda con la que
    reproduce el numero de barras esperado."""
    cand = [b for b in det if b["alto"] >= 8 and b["ancho"] >= 2]
    if not cand:
        return [], "—"

    h = _horizontales(cand, esperado)
    v = _verticales(cand)
    if esperado is not None:
        if len(h) == esperado:
            return sorted(h, key=lambda b: (b["y"], b["x"])), "horizontal"
        if len(v) == esperado:
            return sorted(v, key=lambda b: (b["x"], b["y"])), "vertical"
    if len(v) > len(h):
        return sorted(v, key=lambda b: (b["x"], b["y"])), "vertical"
    return sorted(h, key=lambda b: (b["y"], b["x"])), "horizontal"


def agrupar_por_panel(barras, tipo, n_paneles, orientacion="horizontal"):
    """Reparte las barras detectadas entre los paneles del grafico."""
    if not barras:
        return []
    if tipo == "divergente" or n_paneles <= 1:
        return [sorted(barras, key=lambda b: b["y"])]
    if tipo == "panelesConBanda":
        # en el original los tres paneles van uno al lado del otro
        clave = (lambda b: b["x"]) if orientacion == "vertical" else (lambda b: b["y"])
        return [[b] for b in sorted(barras, key=clave)][:n_paneles]
    # paneles en columnas: agrupar por borde izquierdo
    xs = sorted({b["x"] // 3 for b in barras})
    grupos, actual = [], [xs[0]]
    for v in xs[1:]:
        if v - actual[-1] <= 4:
            actual.append(v)
        else:
            grupos.append(actual)
            actual = [v]
    grupos.append(actual)
    cols = []
    for g in grupos:
        s = set(g)
        cols.append(sorted([b for b in barras if (b["x"] // 3) in s], key=lambda b: b["y"]))
    cols.sort(key=lambda c: min(b["x"] for b in c))
    return cols


def aplicar(graficos_p="graficos.json", colores_p="colores_graficos.json"):
    graficos = json.load(open(os.path.join(AQUI, graficos_p), encoding="utf-8"))
    crudos = json.load(open(os.path.join(AQUI, colores_p), encoding="utf-8"))
    avisos = []

    print()
    print("%-5s %-22s %-9s %-9s %s" % ("id", "tipo", "en datos", "en imagen", "resultado"))
    print("-" * 78)

    for g in graficos:
        gid = g["id"]
        if gid == "g9":
            print("%-5s %-22s %-9s %-9s %s" % (gid, g["tipo"], "-", "-",
                  "no aplica · el color lo fija la prioridad"))
            continue
        n_datos = sum(len(p["barras"]) for p in g["paneles"])
        visibles_tot = sum(1 for p in g["paneles"] for b in p["barras"]
                           if abs(b["valor"]) > 1e-9)
        det, orient = filtrar_barras(crudos.get(gid, []), visibles_tot)
        cols = agrupar_por_panel(det, g["tipo"], len(g["paneles"]), orient)
        n_img = sum(len(c) for c in cols)

        if len(cols) != len(g["paneles"]):
            avisos.append("%s: %d paneles en la imagen, %d en los datos"
                          % (gid, len(cols), len(g["paneles"])))
            print("%-5s %-22s %-9d %-9d SIN APLICAR (paneles)" % (gid, g["tipo"], n_datos, n_img))
            continue

        ok, aplicadas = True, 0
        for panel, col in zip(g["paneles"], cols):
            barras = panel["barras"]
            # las barras de valor cero no dibujan rectangulo
            visibles = [b for b in barras if abs(b["valor"]) > 1e-9]
            if len(col) != len(visibles):
                ok = False
                avisos.append("%s · panel «%s»: %d barras visibles en los datos, %d en la imagen"
                              % (gid, panel["nombre"] or "—", len(visibles), len(col)))
                break
            # comprobacion: el orden de anchos debe seguir al de |valor|
            pares = list(zip(visibles, col))
            por_valor = sorted(range(len(pares)), key=lambda i: abs(pares[i][0]["valor"]))
            por_ancho = sorted(range(len(pares)), key=lambda i: pares[i][1]["ancho"])
            coincide = sum(1 for a, b in zip(por_valor, por_ancho) if a == b)
            if len(pares) > 2 and coincide < len(pares) * 0.6:
                ok = False
                avisos.append("%s · panel «%s»: el orden de anchos no sigue al de los valores (%d/%d)"
                              % (gid, panel["nombre"] or "—", coincide, len(pares)))
                break
            for b, d in pares:
                b["color"] = d["color"]
                aplicadas += 1
            for b in barras:
                if "color" not in b:
                    b["color"] = "base"

        print("%-5s %-22s %-9d %-9d %s" % (
            gid, g["tipo"], n_datos, n_img,
            ("%d colores aplicados · %s" % (aplicadas, orient)) if ok else "SIN APLICAR"))

    json.dump(graficos, open(os.path.join(AQUI, graficos_p), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("-" * 78)
    if avisos:
        print("AVISOS:")
        for a in avisos:
            print("  ·", a)
    else:
        print("todos los graficos emparejados sin discrepancias")
