#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extraer_contenido.py — Construye contenido.json y capturas/ a partir de los dos
documentos originales del encargo:

    Diagnostico_Digital_360_Freddy_Bernal.docx   (el informe narrativo, 156 pp.)
    Matriz_Diagnostico_360_Freddy_Bernal.xlsx    (la matriz de datos)

No reescribe, no resume y no interpreta: transcribe. Todo texto que llega a
contenido.json es literal respecto del original. Lo unico que este script
"decide" es la ESTRUCTURA (que parrafo es un hallazgo y cual es una accion),
apoyandose en marcas tipograficas que el propio documento ya trae.

Solo biblioteca estandar. Uso:

    python3 extraer_contenido.py informe.docx matriz.xlsx

Salida: contenido.json + capturas/*.png + graficos_png/*.png
"""

import base64
import json
import os
import re
import struct
import sys
import unicodedata
import zipfile
import hashlib
import xml.etree.ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
S = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

AQUI = os.path.dirname(os.path.abspath(__file__))


# --------------------------------------------------------------------------
# 1. Lectura del .docx  ->  lista plana de bloques
# --------------------------------------------------------------------------

def leer_docx(ruta):
    """Devuelve (bloques, media) — media es {nombre: bytes}."""
    with zipfile.ZipFile(ruta) as z:
        doc = ET.fromstring(z.read("word/document.xml"))
        rels = ET.fromstring(z.read("word/_rels/document.xml.rels"))
        media = {
            n.split("/")[-1]: z.read(n)
            for n in z.namelist()
            if n.startswith("word/media/")
        }

    rel_map = {}
    for rel in rels:
        rel_map[rel.get("Id")] = rel.get("Target")

    body = doc.find(W + "body")
    bloques = []
    for hijo in body:
        if hijo.tag == W + "p":
            bloques.append(_parrafo(hijo, rel_map))
        elif hijo.tag == W + "tbl":
            bloques.append(_tabla(hijo))
    return [b for b in bloques if b], media


def _es_negrita(run):
    """Un run esta en negrita si su rPr trae <w:b/> sin val="0"/"false"."""
    rpr = run.find(W + "rPr")
    if rpr is None:
        return False
    b = rpr.find(W + "b")
    if b is None:
        return False
    return b.get(W + "val") not in ("0", "false")


def _texto_de(nodo):
    """Todo el texto de un nodo, en orden, respetando tabuladores y saltos."""
    partes = []
    for e in nodo.iter():
        if e.tag == W + "t":
            partes.append(e.text or "")
        elif e.tag in (W + "tab", W + "br"):
            partes.append(" ")
    return "".join(partes)


def _parrafo(p, rel_map):
    imagenes = [
        rel_map[e.get(R + "embed")].split("/")[-1]
        for e in p.iter("{http://schemas.openxmlformats.org/drawingml/2006/main}blip")
        if e.get(R + "embed") in rel_map
    ]

    # runs, con su marca de negrita, incluidos los que van dentro de hiperenlaces
    runs = []
    for run in p.iter(W + "r"):
        t = _texto_de(run)
        if t:
            runs.append({"t": t, "b": _es_negrita(run)})

    texto = "".join(r["t"] for r in runs)

    if imagenes:
        return {"tipo": "imagen", "imagenes": imagenes, "texto": texto}
    if not texto.strip():
        return None

    ppr = p.find(W + "pPr")
    estilo = "Normal"
    numerada = False
    if ppr is not None:
        st = ppr.find(W + "pStyle")
        if st is not None:
            estilo = st.get(W + "val") or "Normal"
        if ppr.find(W + "numPr") is not None:
            numerada = True

    tipo = {"Heading1": "h1", "Heading2": "h2", "Heading3": "h3"}.get(estilo)
    if tipo is None:
        tipo = "li" if numerada else "p"

    # prefijo en negrita: la "versalita" de apertura del parrafo
    lead = ""
    for r in runs:
        if r["b"]:
            lead += r["t"]
        else:
            break

    return {"tipo": tipo, "texto": texto, "lead": lead}


def _tabla(tbl):
    filas = []
    for tr in tbl.findall(W + "tr"):
        filas.append([_texto_de(tc).strip() for tc in tr.findall(W + "tc")])
    return {"tipo": "tabla", "filas": filas}


# --------------------------------------------------------------------------
# 2. Lectura del .xlsx  ->  hojas como listas de filas
# --------------------------------------------------------------------------

def leer_xlsx(ruta):
    """Devuelve ({nombre_hoja: [[celda,...],...]}, media)."""
    with zipfile.ZipFile(ruta) as z:
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        rel_map = {r.get("Id"): r.get("Target") for r in rels}

        compartidas = []
        if "xl/sharedStrings.xml" in z.namelist():
            sst = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in sst.findall(S + "si"):
                compartidas.append("".join(t.text or "" for t in si.iter(S + "t")))

        media = {
            n.split("/")[-1]: z.read(n)
            for n in z.namelist()
            if n.startswith("xl/media/")
        }

        hojas = {}
        for sh in wb.find(S + "sheets"):
            destino = rel_map[sh.get(R + "id")]
            if not destino.startswith("xl/"):
                destino = "xl/" + destino.lstrip("/")
            hojas[sh.get("name")] = _hoja(
                ET.fromstring(z.read(destino)), compartidas
            )
    return hojas, media


def _col(ref):
    """'BC12' -> indice 0-based de columna."""
    n = 0
    for ch in ref:
        if ch.isalpha():
            n = n * 26 + (ord(ch.upper()) - 64)
        else:
            break
    return n - 1


def _hoja(ws, compartidas):
    filas = []
    data = ws.find(S + "sheetData")
    if data is None:
        return filas
    for row in data.findall(S + "row"):
        celdas = []
        for c in row.findall(S + "c"):
            i = _col(c.get("r", "A1"))
            while len(celdas) <= i:
                celdas.append("")
            t = c.get("t")
            if t == "s":
                v = c.find(S + "v")
                val = compartidas[int(v.text)] if v is not None else ""
            elif t == "inlineStr":
                is_ = c.find(S + "is")
                val = "".join(x.text or "" for x in is_.iter(S + "t")) if is_ is not None else ""
            else:
                v = c.find(S + "v")
                val = v.text if v is not None and v.text else ""
            celdas[i] = val
        filas.append(celdas)
    return filas


def celda(filas, r, c):
    if r < len(filas) and c < len(filas[r]):
        return (filas[r][c] or "").strip()
    return ""


# --------------------------------------------------------------------------
# 3. Utilidades
# --------------------------------------------------------------------------

def dim_png(datos):
    w, h = struct.unpack(">II", datos[16:24])
    return w, h


def limpiar(s):
    """Normaliza el espaciado interno sin tocar el contenido."""
    return re.sub(r"[ \t ]+", " ", (s or "")).strip()


def parrafo(b):
    """Bloque de parrafo -> {t, lead}. 't' es SIEMPRE el texto integro."""
    t = limpiar(b["texto"])
    lead = limpiar(b.get("lead", ""))
    # Un lead que abarca todo el parrafo no es una entradilla.
    if lead and lead == t:
        lead = ""
    # El lead debe ser prefijo real del texto ya normalizado.
    if lead and not t.startswith(lead):
        lead = lead if t.startswith(lead.rstrip()) else ""
        if lead:
            lead = lead.rstrip()
    return {"t": t, "lead": lead}


def tabla(b):
    filas = [[limpiar(c) for c in f] for f in b["filas"]]
    if not filas:
        return None
    return {"headers": filas[0], "rows": filas[1:]}


# --------------------------------------------------------------------------
# 4. Troceado del informe en secciones
# --------------------------------------------------------------------------

def secciones(bloques):
    """Divide por h1. Devuelve [(titulo, [bloques]), ...] y la portada."""
    idx = [i for i, b in enumerate(bloques) if b["tipo"] == "h1"]
    portada = bloques[: idx[0]]
    fuera = []
    for k, i in enumerate(idx):
        fin = idx[k + 1] if k + 1 < len(idx) else len(bloques)
        fuera.append((limpiar(bloques[i]["texto"]), bloques[i + 1: fin]))
    return portada, fuera


RE_MODULO = re.compile(r"^(M\d\d)\s*—\s*(.+)$")
RE_PUNTO = re.compile(r"^(\d+)\.\s+(.+)$")
RE_ESTADO = re.compile(r"^ESTADO\s+(.+?)\s+PRIORIDAD\s+(.+?)\s*$")
RE_ACCION = re.compile(r"^ACCIÓN\s+(.+)$", re.S)
RE_FUENTE = re.compile(r"^FUENTE\s+(.+)$", re.S)
RE_VALORACION = re.compile(r"^VALORACIÓN\s+(.+)$", re.S)
RE_FIGURA = re.compile(r"^Figura\s+(\d+)\.\s+(.+)$", re.S)


def construir_modulo(mid, titulo, bloques, media, capturas, graficos_png):
    """Un modulo: cabecera + N puntos."""
    mod = {
        "id": mid,
        "titulo": titulo,
        "estado_modulo": "",
        "alcance": "",
        "fuente": "",
        "calificacion": "",
        "resumen": [],
        "puntos": [],
    }

    # --- cabecera: hasta el primer h2 ---
    i = 0
    while i < len(bloques) and bloques[i]["tipo"] != "h2":
        b = bloques[i]
        if b["tipo"] == "tabla":
            f = tabla(b)
            # tabla de ficha: cabeceras "Alcance del analisis" / "Estado"
            if f and f["rows"] and len(f["rows"][0]) >= 2:
                mod["alcance"] = f["rows"][0][0]
                mod["estado_modulo"] = f["rows"][0][1]
        elif b["tipo"] in ("p", "li"):
            t = limpiar(b["texto"])
            m = RE_FUENTE.match(t)
            if m:
                mod["fuente"] = limpiar(m.group(1))
                i += 1
                continue
            m = RE_VALORACION.match(t)
            if m:
                mod["calificacion"] = limpiar(m.group(1))
                i += 1
                continue
            mod["resumen"].append(parrafo(b))
        i += 1

    # --- puntos ---
    while i < len(bloques):
        if bloques[i]["tipo"] != "h2":
            i += 1
            continue
        m = RE_PUNTO.match(limpiar(bloques[i]["texto"]))
        cab = limpiar(bloques[i]["texto"])
        n = int(m.group(1)) if m else len(mod["puntos"]) + 1
        enunciado = limpiar(m.group(2)) if m else cab

        j = i + 1
        while j < len(bloques) and bloques[j]["tipo"] != "h2":
            j += 1

        pt = {
            "n": n,
            "punto": enunciado,
            "estado": "",
            "prioridad": "",
            "hallazgo": [],
            "accion": "",
        }

        cuerpo = bloques[i + 1: j]
        k = 0
        while k < len(cuerpo):
            b = cuerpo[k]
            if b["tipo"] == "tabla":
                f = tabla(b)
                if f:
                    pt.setdefault("tabla", f)
            elif b["tipo"] == "imagen":
                arch = b["imagenes"][0]
                pie = ""
                nfig = None
                if k + 1 < len(cuerpo) and cuerpo[k + 1]["tipo"] == "p":
                    mf = RE_FIGURA.match(limpiar(cuerpo[k + 1]["texto"]))
                    if mf:
                        nfig = int(mf.group(1))
                        pie = limpiar(mf.group(2))
                        k += 1  # el pie se consume, no es hallazgo
                if nfig is not None:
                    datos = media[arch]
                    w, h = dim_png(datos)
                    nombre = "figura-%02d.png" % nfig
                    capturas.append({
                        "figura": nfig,
                        "modulo": mid,
                        "punto": n,
                        "archivo": nombre,
                        "ancho": w,
                        "alto": h,
                        "pie": pie,
                    })
                    open(os.path.join(AQUI, "capturas", nombre), "wb").write(datos)
                else:
                    # imagen sin pie de figura = grafico rasterizado
                    graficos_png.append({
                        "modulo": mid, "punto": n,
                        "sha": hashlib.sha1(media[arch]).hexdigest()[:12],
                    })
            else:
                t = limpiar(b["texto"])
                me = RE_ESTADO.match(t)
                if me:
                    pt["estado"] = limpiar(me.group(1))
                    pt["prioridad"] = limpiar(me.group(2))
                    k += 1
                    continue
                ma = RE_ACCION.match(t)
                if ma:
                    pt["accion"] = limpiar(ma.group(1))
                    k += 1
                    continue
                pt["hallazgo"].append(parrafo(b))
            k += 1

        mod["puntos"].append(pt)
        i = j

    return mod


# --------------------------------------------------------------------------
# 5. Montaje de contenido.json
# --------------------------------------------------------------------------

def main():
    docx = sys.argv[1] if len(sys.argv) > 1 else os.path.join(AQUI, "informe.docx")
    xlsx = sys.argv[2] if len(sys.argv) > 2 else os.path.join(AQUI, "matriz.xlsx")

    os.makedirs(os.path.join(AQUI, "capturas"), exist_ok=True)
    os.makedirs(os.path.join(AQUI, "graficos_png"), exist_ok=True)

    bloques, media = leer_docx(docx)
    hojas, media_x = leer_xlsx(xlsx)

    portada_b, secs = secciones(bloques)
    por_titulo = {t: b for t, b in secs}

    # ---------------- portada ----------------
    ptxt = [limpiar(b["texto"]) for b in portada_b if b["tipo"] in ("p", "li")]
    portada = {"lineas": ptxt}
    campos = {}
    for l in ptxt:
        mm = re.match(r"^(CLIENTE|BASE CONTRACTUAL|ALCANCE|FUENTES|DOCUMENTO)\s+(.+)$", l)
        if mm:
            campos[mm.group(1)] = limpiar(mm.group(2))
    portada["campos"] = campos
    portada["titulo"] = ptxt[0] if ptxt else ""
    portada["subtitulo"] = ptxt[1] if len(ptxt) > 1 else ""
    portada["sujeto"] = ptxt[2] if len(ptxt) > 2 else ""
    portada["cargo"] = ptxt[3] if len(ptxt) > 3 else ""
    portada["descripcion"] = [l for l in ptxt if l not in campos.values()
                              and not re.match(r"^(CLIENTE|BASE CONTRACTUAL|ALCANCE|FUENTES|DOCUMENTO)\s", l)][4:]

    # ---------------- como leer ----------------
    como_leer = []
    for b in por_titulo.get("Cómo leer este documento", []):
        if b["tipo"] == "h2":
            como_leer.append([limpiar(b["texto"]), []])
        elif b["tipo"] in ("p", "li") and como_leer:
            como_leer[-1][1].append(parrafo(b))

    # ---------------- resumen ejecutivo ----------------
    rb = por_titulo.get("Resumen ejecutivo consolidado", [])
    resumen = {"intro": None, "hallazgos": [], "calificaciones": [],
               "calificaciones_headers": [], "cierre": []}
    pend = None
    vistos_h2 = False
    for b in rb:
        if b["tipo"] == "h2":
            vistos_h2 = True
            continue
        if b["tipo"] == "tabla":
            f = tabla(b)
            if f:
                resumen["calificaciones_headers"] = f["headers"]
                resumen["calificaciones"] = f["rows"]
            continue
        if b["tipo"] == "imagen":
            continue
        t = limpiar(b["texto"])
        mh = re.match(r"^(\d)\.\s+(.+)$", t)
        if mh and not vistos_h2:
            pend = [limpiar(mh.group(2)), None]
            resumen["hallazgos"].append(pend)
        elif pend is not None and pend[1] is None and not vistos_h2:
            pend[1] = parrafo(b)
            pend = None
        elif resumen["intro"] is None and not vistos_h2:
            resumen["intro"] = parrafo(b)
        else:
            resumen["cierre"].append(parrafo(b))

    # ---------------- intros de seccion y tabla-resumen de modulos ----------------
    intros = {}
    tabla_modulos = None
    for clave, titulo_h1 in (("indice_modulos", "Los 21 módulos de análisis"),
                             ("cuerpo", "Los 21 módulos, punto por punto")):
        for b in por_titulo.get(titulo_h1, []):
            if b["tipo"] in ("p", "li") and clave not in intros:
                intros[clave] = parrafo(b)
            elif b["tipo"] == "tabla" and tabla_modulos is None:
                tabla_modulos = tabla(b)

    # ---------------- modulos ----------------
    capturas, graficos_png = [], []
    modulos = []
    for t, bl in secs:
        m = RE_MODULO.match(t)
        if m:
            modulos.append(construir_modulo(
                m.group(1), limpiar(m.group(2)), bl, media, capturas, graficos_png))

    # tabla-resumen de modulos, desde la hoja 1 de la matriz
    hoja_mod = hojas.get("1. Módulos", [])
    meta_mod = {}
    for r in range(4, len(hoja_mod)):
        mid = celda(hoja_mod, r, 0)
        if RE_MODULO.match(mid + " — x") or re.match(r"^M\d\d$", mid):
            meta_mod[mid] = {
                "puntos": celda(hoja_mod, r, 2),
                "pct": celda(hoja_mod, r, 3),
                "criticos": celda(hoja_mod, r, 4),
                "alta": celda(hoja_mod, r, 5),
                "estado": celda(hoja_mod, r, 6),
                "alcance": celda(hoja_mod, r, 7),
            }
    for mod in modulos:
        mm = meta_mod.get(mod["id"], {})
        if mm:
            if not mod["alcance"]:
                mod["alcance"] = mm["alcance"]
            if not mod["estado_modulo"]:
                mod["estado_modulo"] = mm["estado"]

    # ---------------- plan a 90 dias ----------------
    pb = por_titulo.get("Plan de acción consolidado — hoja de ruta a 90 días", [])
    plan, bloque, pendiente = [], None, None
    intro_plan = None
    for b in pb:
        if b["tipo"] == "h2":
            bloque = [limpiar(b["texto"]), None, []]
            plan.append(bloque)
            pendiente = None
            continue
        if b["tipo"] not in ("p", "li"):
            continue
        t = limpiar(b["texto"])
        if bloque is None:
            if intro_plan is None:
                intro_plan = parrafo(b)
            continue
        ma = re.match(r"^(\d{2})\s+(.+?)\s*\[([^\]]+)\]\s*$", t)
        if ma:
            pendiente = [limpiar(ma.group(2)), limpiar(ma.group(3)), None,
                         int(ma.group(1))]
            bloque[2].append(pendiente)
        elif pendiente is not None and pendiente[2] is None:
            pendiente[2] = parrafo(b)
            pendiente = None
        elif bloque[1] is None:
            bloque[1] = parrafo(b)

    # ---------------- fase de profundizacion ----------------
    vb = por_titulo.get("Fase de profundización — qué desbloquea cada acceso", [])
    vacios = {"intro": None, "categorias": []}
    for b in vb:
        if b["tipo"] == "h2":
            vacios["categorias"].append([limpiar(b["texto"]), []])
        elif b["tipo"] in ("p", "li"):
            if vacios["categorias"]:
                vacios["categorias"][-1][1].append(parrafo(b))
            elif vacios["intro"] is None:
                vacios["intro"] = parrafo(b)

    # ---------------- fuentes ----------------
    fb = por_titulo.get("Anexo A — Fuentes consolidadas", [])
    fuentes = {"documentos": [], "documentos_headers": [],
               "grupos": []}
    grupo = None
    for b in fb:
        if b["tipo"] == "h2":
            grupo = [limpiar(b["texto"]), []]
            fuentes["grupos"].append(grupo)
        elif b["tipo"] == "tabla":
            f = tabla(b)
            if f:
                fuentes["documentos_headers"] = f["headers"]
                fuentes["documentos"] = f["rows"]
        elif b["tipo"] in ("p", "li") and grupo is not None:
            grupo[1].append(parrafo(b))

    # ---------------- nota metodologica ----------------
    nb = por_titulo.get("Anexo B — Nota metodológica y trazabilidad", [])
    nota = [parrafo(b) for b in nb if b["tipo"] in ("p", "li")]

    # ---------------- graficos (datos verificados aparte) ----------------
    ruta_g = os.path.join(AQUI, "graficos.json")
    graficos = json.load(open(ruta_g, encoding="utf-8")) if os.path.exists(ruta_g) else []

    # ---------------- recuentos ----------------
    n_puntos = sum(len(m["puntos"]) for m in modulos)
    n_tablas = sum(1 for m in modulos for p in m["puntos"] if "tabla" in p)
    n_acciones = sum(len(b[2]) for b in plan)

    meta = {
        "titulo": portada.get("titulo", ""),
        "subtitulo": portada.get("subtitulo", ""),
        "sujeto": portada.get("sujeto", ""),
        "cargo": portada.get("cargo", ""),
        "cliente": campos.get("CLIENTE", ""),
        "base_contractual": campos.get("BASE CONTRACTUAL", ""),
        "alcance": campos.get("ALCANCE", ""),
        "fuentes": campos.get("FUENTES", ""),
        "documento": campos.get("DOCUMENTO", ""),
        "total_modulos": len(modulos),
        "total_puntos": n_puntos,
        "total_tablas": n_tablas,
        "total_capturas": len(capturas),
        "total_acciones": n_acciones,
        "total_graficos": len(graficos),
    }

    contenido = {
        "meta": meta,
        "portada": portada,
        "como_leer": como_leer,
        "resumen": resumen,
        "modulos": modulos,
        "modulos_meta": meta_mod,
        "tabla_modulos": tabla_modulos,
        "intros": intros,
        "plan_intro": intro_plan,
        "plan": plan,
        "vacios": vacios,
        "fuentes": fuentes,
        "nota": nota,
        "capturas": capturas,
        "graficos": graficos,
    }

    salida = os.path.join(AQUI, "contenido.json")
    with open(salida, "w", encoding="utf-8") as fh:
        json.dump(contenido, fh, ensure_ascii=False, indent=1)

    # ---------------- informe de control ----------------
    print("contenido.json escrito en", salida)
    print("  modulos          ", len(modulos))
    print("  puntos           ", n_puntos)
    print("  tablas de punto  ", n_tablas)
    print("  capturas         ", len(capturas))
    print("  graficos (datos) ", len(graficos))
    print("  bloques del plan ", len(plan), "· acciones", n_acciones)
    print("  bloques de vacios", len(vacios["categorias"]))
    print("  secciones cómo leer", len(como_leer))
    print("  hallazgos resumen  ", len(resumen["hallazgos"]))
    print("  filas calificación ", len(resumen["calificaciones"]))

    faltan = [(m["id"], p["n"]) for m in modulos for p in m["puntos"]
              if not p["estado"] or not p["prioridad"] or not p["accion"]
              or not p["hallazgo"]]
    if faltan:
        print("  AVISO — puntos incompletos:", faltan[:20])
    else:
        print("  todos los puntos traen estado, prioridad, hallazgo y acción")

    estados = {}
    prioridades = {}
    for m in modulos:
        for p in m["puntos"]:
            estados[p["estado"]] = estados.get(p["estado"], 0) + 1
            prioridades[p["prioridad"]] = prioridades.get(p["prioridad"], 0) + 1
    print("  estados     ", estados)
    print("  prioridades ", prioridades)


if __name__ == "__main__":
    main()
