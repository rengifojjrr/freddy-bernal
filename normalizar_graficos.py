#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
normalizar_graficos.py — Convierte la salida del flujo de extraccion de
graficos en graficos.json, el archivo que build.py consume.

Los diez graficos del informe original solo existen como PNG rasterizado:
ni el DOCX ni el XLSX contienen sus series como numeros. Cada grafico se
transcribio leyendo la imagen y despues se verifico, cifra a cifra, contra
el texto del informe y contra las hojas de datos de la matriz.

    python3 normalizar_graficos.py <journal.jsonl>

Escribe graficos.json y graficos_trazabilidad.json (la corroboracion de
cada cifra, con su cita), e imprime un informe de control.
"""

import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))

# Ubicacion y tipo de cada grafico, establecidos cruzando los SHA1 de las
# imagenes del DOCX con las del XLSX y su posicion en el documento.
CHARTS = [
    {"id": "g1",  "tipo": "tiles+barh",       "modulo": None,  "punto": None},
    {"id": "g2",  "tipo": "barh",             "modulo": "M01", "punto": 1},
    {"id": "g3",  "tipo": "barh",             "modulo": "M12", "punto": 9},
    {"id": "g4",  "tipo": "panelesConBanda",  "modulo": "M12", "punto": 7},
    {"id": "g5",  "tipo": "divergente",       "modulo": "M13", "punto": 8},
    {"id": "g6",  "tipo": "barhDoble",        "modulo": "M13", "punto": 6},
    {"id": "g7",  "tipo": "barhDoble",        "modulo": "M13", "punto": 7},
    {"id": "g8",  "tipo": "barh+composicion", "modulo": "M13", "punto": 1},
    {"id": "g9",  "tipo": "apiladaPorModulo", "modulo": None,  "punto": None},
    {"id": "g10", "tipo": "barh",             "modulo": "M12", "punto": 13},
]
META = {c["id"]: c for c in CHARTS}


def leer_journal(ruta):
    """Extrae de journal.jsonl la ultima extraccion y la ultima verificacion
    de cada grafico."""
    extraidos, verificados = {}, {}
    with open(ruta, encoding="utf-8") as fh:
        for linea in fh:
            linea = linea.strip()
            if not linea:
                continue
            try:
                d = json.loads(linea)
            except ValueError:
                continue
            r = d.get("result")
            if not isinstance(r, dict):
                continue
            gid = r.get("id")
            if not gid:
                continue
            if "veredicto" in r:
                verificados[gid] = r
            elif "paneles" in r:
                extraidos[gid] = r
    return extraidos, verificados


def datos_finales(ver, ext):
    """La verificacion devuelve el objeto corregido serializado. Si no se
    puede leer, se cae a la extraccion original."""
    crudo = (ver or {}).get("datos_finales")
    if crudo:
        if isinstance(crudo, dict):
            return crudo, "verificado"
        try:
            obj = json.loads(crudo)
            if isinstance(obj, dict) and obj.get("paneles"):
                return obj, "verificado"
        except (ValueError, TypeError):
            pass
    return ext, "sin verificar"


def normalizar(gid, d):
    m = META[gid]
    paneles = []
    for p in (d.get("paneles") or []):
        barras = []
        for b in (p.get("barras") or []):
            try:
                v = float(b.get("valor"))
            except (TypeError, ValueError):
                v = 0.0
            barras.append({
                "cat": (b.get("cat") or "").strip(),
                "valor": v,
                "etiqueta": (b.get("etiqueta_valor") or b.get("etiqueta") or "").strip(),
                "detalle": (b.get("detalle") or "").strip(),
                "destaca": (b.get("destaca") or "").strip().upper()[:1],
            })
        panel = {
            "nombre": (p.get("nombre") or "").strip(),
            "unidad": (p.get("unidad") or "").strip(),
            "barras": barras,
        }
        banda = p.get("banda")
        if isinstance(banda, dict) and banda.get("min") is not None:
            panel["banda"] = {
                "min": float(banda.get("min") or 0),
                "max": float(banda.get("max") or 0),
                "etiqueta": (banda.get("etiqueta") or "").strip(),
            }
        paneles.append(panel)

    tiles = []
    for t in (d.get("tiles") or []):
        tiles.append({
            "valor": (t.get("valor") or "").strip(),
            "etiqueta": (t.get("etiqueta") or "").strip(),
            "detalle": (t.get("detalle") or "").strip(),
        })

    return {
        "id": gid,
        "tipo": m["tipo"],
        "modulo": m["modulo"],
        "punto": m["punto"],
        "titulo": (d.get("titulo_en_imagen") or "").strip(),
        "subtitulo": (d.get("subtitulo_en_imagen") or "").strip(),
        "nota": (d.get("nota_en_imagen") or "").strip(),
        "eje": (d.get("eje_valor") or "").strip(),
        "tiles": tiles,
        "paneles": paneles,
    }


def main():
    ruta = sys.argv[1] if len(sys.argv) > 1 else None
    if not ruta or not os.path.exists(ruta):
        sys.exit("uso: normalizar_graficos.py <journal.jsonl>")

    ext, ver = leer_journal(ruta)
    salida, traza = [], []

    print("%-5s %-22s %-8s %-6s %s" % ("id", "tipo", "origen", "barras", "veredicto"))
    print("-" * 78)

    for c in CHARTS:
        gid = c["id"]
        if gid not in ext and gid not in ver:
            print("%-5s FALTA — no hay ni extraccion ni verificacion" % gid)
            continue
        d, origen = datos_finales(ver.get(gid), ext.get(gid))
        if not d:
            print("%-5s FALTA — sin datos utilizables" % gid)
            continue
        g = normalizar(gid, d)
        nb = sum(len(p["barras"]) for p in g["paneles"])
        v = ver.get(gid) or {}
        print("%-5s %-22s %-8s %-6d %s (%d correcciones)" % (
            gid, g["tipo"], origen, nb, v.get("veredicto", "—"), len(v.get("correcciones") or [])))
        salida.append(g)

        traza.append({
            "id": gid,
            "titulo": g["titulo"],
            "veredicto": v.get("veredicto", "SIN VERIFICAR"),
            "correcciones": v.get("correcciones") or [],
            "corroboracion": v.get("corroboracion") or [],
            "observaciones": (ext.get(gid) or {}).get("observaciones", ""),
        })

    json.dump(salida, open(os.path.join(AQUI, "graficos.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    json.dump(traza, open(os.path.join(AQUI, "graficos_trazabilidad.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    print("-" * 78)
    print("graficos.json escrito —", len(salida), "de", len(CHARTS), "graficos")
    sin_fuente = 0
    for t in traza:
        for c in t["corroboracion"]:
            f = (c.get("fuente") or "").upper()
            if "NO APARECE" in f or "SOLO LEGIBLE" in f:
                sin_fuente += 1
    total_cif = sum(len(t["corroboracion"]) for t in traza)
    print("cifras corroboradas contra el texto:", total_cif - sin_fuente, "de", total_cif)
    if sin_fuente:
        print("cifras que solo constan en la imagen:", sin_fuente,
              "— ver graficos_trazabilidad.json")


if __name__ == "__main__":
    main()
