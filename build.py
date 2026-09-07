#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build.py — Genera informe.html: un unico archivo autocontenido que se abre
haciendo doble clic, sin servidor y sin conexion.

    python3 build.py

Entrada:  contenido.json · capturas/*.png · graficos.json
Salida:   informe.html

El JSON va incrustado en <script type="application/json">, las capturas como
data URI en base64, y el CSS y el JS en linea. Cero dependencias externas.

Nada del texto del informe se reescribe aqui: build.py solo pinta.
"""

import base64
import datetime
import json
import os
import struct
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))

# Servidor de las ediciones del equipo. La clave "anon" es publica por diseno:
# no da permiso de escritura. Las tablas no admiten escritura directa —lo
# comprobamos— y todo lo que se guarda pasa por la funcion fb360, que valida
# el token del enlace de edicion antes de tocar nada.
SERVIDOR = {
    "url": "https://vajbsfgojtunamhrzrpf.supabase.co",
    "anon": ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
             "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZhamJzZmdvanR1bmFtaHJ6cnBmIiwicm9sZSI6"
             "ImFub24iLCJpYXQiOjE3ODQzMDczODMsImV4cCI6MjA5OTg4MzM4M30."
             "MuBFoms41X2mFl7q07H0MByEhNsPO239BcXZJNLHDnc"),
    "deposito": "https://vajbsfgojtunamhrzrpf.supabase.co/storage/v1/object/public/fb360/",
}


# ==========================================================================
#  CSS
# ==========================================================================

CSS = r"""
/* ---------- tokens: paleta validada para daltonismo ---------- */
:root{
  --blue:#2a78d6; --orange:#eb6834; --aqua:#1baf7a; --red:#d03b3b; --dim:#b9bec7;
  --navy:#1d2027; --ink:#0b0b0b; --ink2:#52514e; --muted:#898781;
  --grid:#e1e0d9; --base:#c3c2b7; --surface:#ffffff; --plane:#f7f8fa;

  --verde:#1d6f42; --dorado:#9a6b00; --marino:#1d2027; --gris:#6b6b6b;

  --bg:var(--plane);
  --card:var(--surface);
  --texto:var(--ink);
  --texto2:var(--ink2);
  --linea:var(--grid);
  --linea2:var(--base);
  --sombra:0 1px 2px rgba(11,11,11,.04);
  --tinte:#f2f4f7;
  --barra-base:#c8ccd3;
  --banda:#eef1f5;

  --sobre-color:#ffffff;

  --r:3px;
  --lectura:70ch;
  --sidebar:288px;
  --topbar:60px;
}

/* modo oscuro: juego de tonos propio, no una inversion */
:root:not([data-theme="light"]){
  @media (prefers-color-scheme: dark){
    color-scheme:dark;
  }
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --blue:#6aa6ee; --orange:#f28a5f; --aqua:#3fcb99; --red:#e86a6a; --dim:#6a707a;
    --ink:#e9e7e2; --ink2:#b0aea8; --muted:#84827d;
    --grid:#282c33; --base:#3b414a; --surface:#15181c; --plane:#0d0f12;
    --verde:#4fbc82; --dorado:#d8a63c; --marino:#a8bdd8; --gris:#8c8c8c;
    --bg:var(--plane); --card:var(--surface);
    --texto:var(--ink); --texto2:var(--ink2);
    --linea:var(--grid); --linea2:var(--base);
    --sombra:0 1px 2px rgba(0,0,0,.35);
    --tinte:#1b1f25;
    --barra-base:#454b55;
    --banda:#1d222a;
    --sobre-color:#0d0f12;
    color-scheme:dark;
  }
}
:root[data-theme="dark"]{
  --blue:#6aa6ee; --orange:#f28a5f; --aqua:#3fcb99; --red:#e86a6a; --dim:#6a707a;
  --ink:#e9e7e2; --ink2:#b0aea8; --muted:#84827d;
  --grid:#282c33; --base:#3b414a; --surface:#15181c; --plane:#0d0f12;
  --verde:#4fbc82; --dorado:#d8a63c; --marino:#a8bdd8; --gris:#8c8c8c;
  --bg:var(--plane); --card:var(--surface);
  --texto:var(--ink); --texto2:var(--ink2);
  --linea:var(--grid); --linea2:var(--base);
  --sombra:0 1px 2px rgba(0,0,0,.35);
  --tinte:#1b1f25;
  --barra-base:#454b55;
  --banda:#1d222a;
  --sobre-color:#0d0f12;
  color-scheme:dark;
}

/* ---------- base ---------- */
*,*::before,*::after{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0; padding-top:var(--topbar);
  background:var(--bg); color:var(--texto);
  font-family:system-ui,-apple-system,"Segoe UI",sans-serif;
  font-size:15.5px; line-height:1.65;
  overflow-x:hidden;
}
h1,h2,h3,h4{margin:0; font-weight:600; line-height:1.25; letter-spacing:-.011em}
p{margin:0}
a{color:var(--blue)}
img{max-width:100%}
[hidden]{display:none !important}
button,input{font:inherit; color:inherit}

.saltar{
  position:absolute; left:-9999px; top:0; z-index:200;
  background:var(--card); color:var(--texto); padding:10px 16px;
  border:1px solid var(--linea2); border-radius:var(--r);
}
.saltar:focus{left:12px; top:12px}

:focus-visible{outline:2px solid var(--blue); outline-offset:2px; border-radius:2px}

/* ---------- barra superior ---------- */
.topbar{
  position:fixed; top:0; left:0; right:0; z-index:60;
  display:flex; align-items:center; gap:14px;
  height:var(--topbar); padding:0 18px;
  background:var(--card); border-bottom:1px solid var(--linea);
}
.marca{display:flex; flex-direction:column; line-height:1.15; flex:none}
.marca b{font-size:13px; font-weight:650; letter-spacing:.02em}
.marca span{font-size:11px; color:var(--muted)}

.buscador{position:relative; flex:1 1 auto; max-width:460px; min-width:0}
.buscador input{
  width:100%; padding:9px 32px 9px 34px;
  background:var(--bg); color:var(--texto);
  border:1px solid var(--linea2); border-radius:var(--r);
  font-size:14px;
}
.buscador input::placeholder{color:var(--muted)}
.buscador .lupa{
  position:absolute; left:10px; top:50%; transform:translateY(-50%);
  width:14px; height:14px; opacity:.5; pointer-events:none;
}
.buscador .limpiar{
  position:absolute; right:6px; top:50%; transform:translateY(-50%);
  border:0; background:none; cursor:pointer; color:var(--muted);
  font-size:16px; line-height:1; padding:4px 6px; border-radius:var(--r);
}
.buscador .limpiar:hover{color:var(--texto)}

.contador{
  font-size:12px; color:var(--texto2); white-space:nowrap;
  font-variant-numeric:tabular-nums; flex:none;
}
.contador b{color:var(--texto); font-weight:650}

.acciones{display:flex; gap:6px; margin-left:auto; flex:none}
.btn{
  display:inline-flex; align-items:center; gap:6px;
  padding:6px 11px; font-size:12.5px;
  background:var(--card); color:var(--texto2);
  border:1px solid var(--linea2); border-radius:var(--r);
  cursor:pointer; white-space:nowrap;
}
.btn:hover{border-color:var(--muted); color:var(--texto)}
.btn[aria-pressed="true"]{background:var(--tinte); color:var(--texto); border-color:var(--muted)}
.btn svg{width:14px; height:14px; flex:none}
#btn-editar{
  background:var(--aqua); border-color:var(--aqua); color:#07281c; font-weight:650;
  margin-left:auto;
}
#btn-editar:hover{border-color:var(--aqua); color:#07281c; filter:brightness(1.05)}
#btn-editar[aria-pressed="true"]{
  background:var(--card); color:var(--texto); border-color:var(--muted); font-weight:500;
}
.topbar #btn-editar ~ .acciones{margin-left:0}


/* ---------- estructura ---------- */
.shell{display:flex; align-items:flex-start}

.sidebar{
  position:sticky; top:var(--topbar); flex:none;
  width:var(--sidebar); height:calc(100vh - var(--topbar));
  overflow-y:auto; overscroll-behavior:contain;
  background:var(--card); border-right:1px solid var(--linea);
  padding:20px 0 60px;
}
.nav-grupo{margin-bottom:22px}
.nav-titulo{
  padding:0 20px 7px; font-size:10.5px; font-weight:650;
  letter-spacing:.09em; text-transform:uppercase; color:var(--muted);
}
.nav-a{
  display:flex; align-items:baseline; gap:9px;
  padding:6px 20px; font-size:13px; color:var(--texto2);
  text-decoration:none; border-left:2px solid transparent;
}
.nav-a:hover{background:var(--tinte); color:var(--texto)}
.nav-a.activo{border-left-color:var(--blue); color:var(--texto); font-weight:600; background:var(--tinte)}
.nav-a .id{
  flex:none; font-size:11px; font-weight:650; color:var(--muted);
  font-variant-numeric:tabular-nums; width:26px;
}
.nav-a.activo .id{color:var(--blue)}
.nav-a .tx{
  flex:1; min-width:0; text-transform:none;
  display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical;
  overflow:hidden; line-height:1.35;
}
.nav-a .crit{
  flex:none; font-size:10px; font-weight:700; color:var(--sobre-color); background:var(--red);
  border-radius:9px; padding:1px 6px; line-height:1.5;
  font-variant-numeric:tabular-nums;
}

main{flex:1 1 auto; min-width:0; padding:0 0 120px}
.seccion{padding:56px 40px 8px; scroll-margin-top:calc(var(--topbar) + 12px)}
.seccion + .seccion{border-top:1px solid var(--linea)}
.seccion-cab{margin-bottom:32px; padding-bottom:16px; border-bottom:1px solid var(--linea2)}
.seccion-cab h2{font-size:25px; letter-spacing:-.024em; text-wrap:balance}
.seccion-cab .sub{margin-top:8px; font-size:14px; color:var(--texto2); max-width:var(--lectura)}
.eyebrow{
  font-size:10.5px; font-weight:650; letter-spacing:.09em;
  text-transform:uppercase; color:var(--muted); margin-bottom:7px;
}

.prosa{max-width:var(--lectura)}
.prosa p{margin:0 0 .85em}
.prosa p:last-child{margin-bottom:0}
.lead{font-weight:650; color:var(--texto)}

/* ---------- portada ---------- */
.portada{padding:52px 40px 8px}
.portada h1{font-size:34px; letter-spacing:-.028em; line-height:1.1}
.portada .sub{font-size:17px; color:var(--texto2); margin-top:6px; font-weight:400}
.portada .sujeto{margin-top:22px; font-size:19px; font-weight:600}
.portada .cargo{font-size:14px; color:var(--texto2); margin-top:2px}
.ficha{
  margin-top:26px; display:grid; gap:0;
  grid-template-columns:max-content 1fr;
  border-top:1px solid var(--linea); max-width:820px;
}
.ficha dt{
  padding:9px 22px 9px 0; font-size:10.5px; font-weight:650;
  letter-spacing:.09em; text-transform:uppercase; color:var(--muted);
  border-bottom:1px solid var(--linea); white-space:nowrap;
}
.ficha dd{
  margin:0; padding:9px 0; font-size:13.5px; color:var(--texto2);
  border-bottom:1px solid var(--linea);
}

.cifras{
  display:grid; gap:1px; margin:30px 0 6px;
  grid-template-columns:repeat(auto-fit,minmax(132px,1fr));
  background:var(--linea); border:1px solid var(--linea);
  border-radius:var(--r); overflow:hidden;
}
.cifra{background:var(--card); padding:15px 16px}
.cifra b{display:block; font-size:25px; font-weight:650; letter-spacing:-.025em; font-variant-numeric:tabular-nums}
.cifra span{display:block; font-size:11px; color:var(--muted); margin-top:2px; letter-spacing:.02em}

/* ---------- hallazgos del resumen ---------- */
.hallazgos{display:grid; gap:1px; background:var(--linea); border:1px solid var(--linea); border-radius:var(--r); overflow:hidden}
.hallazgo{background:var(--card); padding:20px 22px; display:flex; gap:16px}
.hallazgo .num{
  flex:none; width:26px; height:26px; border-radius:50%;
  background:var(--tinte); border:1px solid var(--linea2); color:var(--texto2);
  display:flex; align-items:center; justify-content:center;
  font-size:12px; font-weight:650; font-variant-numeric:tabular-nums;
}
.hallazgo h3{font-size:15.5px; margin-bottom:6px}
.hallazgo p{font-size:14px; color:var(--texto2); max-width:var(--lectura)}

/* ---------- tablas ---------- */
.tabla-caja{overflow-x:auto; margin:14px 0; border:1px solid var(--linea); border-radius:var(--r); background:var(--card)}
table{border-collapse:collapse; width:100%; font-size:13px}
thead th{
  text-align:left; padding:9px 13px; font-size:10.5px; font-weight:650;
  letter-spacing:.07em; text-transform:uppercase; color:var(--muted);
  border-bottom:1px solid var(--linea2); white-space:nowrap; background:var(--card);
}
tbody td{padding:9px 13px; border-bottom:1px solid var(--linea); vertical-align:top; color:var(--texto2)}
tbody tr:last-child td{border-bottom:0}
tbody td:first-child{color:var(--texto); font-weight:500}
tbody tr.total td{font-weight:650; color:var(--texto); background:var(--tinte)}

/* tabla-resumen de modulos */
.t-modulos tbody tr{cursor:pointer}
.t-modulos tbody tr:hover{background:var(--tinte)}
.t-modulos td.n{font-variant-numeric:tabular-nums; text-align:right; white-space:nowrap}
.t-modulos td.alc{font-size:12px; color:var(--muted)}
.pill{
  display:inline-block; min-width:20px; text-align:center;
  padding:1px 6px; border-radius:9px; font-size:11px; font-weight:650;
  font-variant-numeric:tabular-nums;
}
.pill.c{background:var(--red); color:var(--sobre-color)}
.pill.a{background:var(--orange); color:var(--sobre-color)}
.pill.cero{background:transparent; color:var(--muted); font-weight:400}

/* ---------- modulo ---------- */
.modulo{margin:0 0 68px; scroll-margin-top:calc(var(--topbar) + 12px)}
.modulo-cab{padding-bottom:18px; border-bottom:2px solid var(--texto); margin-bottom:24px}
.modulo-cab .id{
  font-size:11px; font-weight:700; letter-spacing:.12em; color:var(--blue);
}
.modulo-cab h2{font-size:22px; margin-top:6px; letter-spacing:-.022em; text-wrap:balance}
.modulo-cifras{display:flex; flex-wrap:wrap; gap:7px; margin-top:14px}
.mp{
  display:inline-flex; align-items:baseline; gap:6px;
  padding:3px 10px; border-radius:12px; font-size:11.5px;
  background:var(--tinte); color:var(--texto2); border:1px solid var(--linea);
  font-variant-numeric:tabular-nums; white-space:nowrap;
}
.mp b{font-weight:700; color:var(--texto)}
.mp.c{border-color:var(--red); color:var(--red)} .mp.c b{color:var(--red)}
.mp.a{border-color:var(--orange); color:var(--orange)} .mp.a b{color:var(--orange)}
.modulo-meta{
  display:grid; gap:9px 22px; margin-top:16px; font-size:12.5px; color:var(--texto2);
  grid-template-columns:max-content 1fr; align-items:baseline;
}
.modulo-meta dt{
  font-size:10px; font-weight:650; letter-spacing:.09em;
  text-transform:uppercase; color:var(--muted); white-space:nowrap;
}
.modulo-meta dd{margin:0}
.modulo-resumen{margin:20px 0 30px}

/* pasar al modulo anterior o siguiente sin volver al indice */
.modulo-pasos{
  display:flex; gap:10px; margin-top:26px; padding-top:18px;
  border-top:1px solid var(--linea);
}
.paso{
  flex:1 1 0; min-width:0; display:flex; flex-direction:column; gap:3px;
  padding:12px 14px; text-decoration:none; border-radius:var(--r);
  border:1px solid var(--linea2); background:var(--card); color:var(--texto);
}
.paso:hover{border-color:var(--muted); background:var(--tinte)}
.paso span{font-size:10px; font-weight:650; letter-spacing:.09em; text-transform:uppercase; color:var(--muted)}
.paso b{font-size:13px; font-weight:600; line-height:1.3;
  display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden}
.paso.sig{text-align:right}
.paso.vacio{visibility:hidden}

/* ---------- punto ---------- */
.punto{
  position:relative;
  background:var(--card); border:1px solid var(--linea); border-radius:var(--r);
  margin-bottom:18px; box-shadow:var(--sombra);
  scroll-margin-top:calc(var(--topbar) + 12px);
}
/* los 37 puntos criticos se localizan sin leer: un filo rojo en el borde */
.punto[data-prioridad="CRÍTICA"]{border-left:3px solid var(--red)}
.punto[data-prioridad="CRÍTICA"] .punto-cab{padding-left:17px}
.punto-cab{
  display:flex; gap:14px; align-items:flex-start;
  padding:16px 20px; width:100%; text-align:left;
  background:none; border:0; cursor:default;
}
.compacto .punto-cab, .punto.plegado .punto-cab{cursor:pointer}
.punto-n{
  flex:none; font-size:12px; font-weight:650; color:var(--muted);
  font-variant-numeric:tabular-nums; padding-top:2px; min-width:22px;
}
.punto-tit{flex:1; min-width:0}
.punto-tit h3{font-size:15.5px; letter-spacing:-.008em}
.distintivos{display:flex; flex-wrap:wrap; gap:6px; margin-top:9px}
.chev{
  flex:none; width:16px; height:16px; margin-top:4px; opacity:0;
  transition:transform .12s ease; color:var(--muted);
}
.compacto .chev, .punto.plegado .chev{opacity:1}
.punto.abierto .chev{transform:rotate(90deg)}

.badge{
  display:inline-flex; align-items:center; gap:5px;
  padding:2px 8px; border-radius:var(--r);
  font-size:10.5px; font-weight:650; letter-spacing:.05em; text-transform:uppercase;
  border:1px solid currentColor; white-space:nowrap; text-decoration:none;
}
.badge::before{content:""; width:5px; height:5px; border-radius:50%; background:currentColor; flex:none}
.badge.p-critica{color:var(--red)}
.badge.p-alta{color:var(--orange)}
.badge.p-media{color:var(--blue)}
.badge.p-baja{color:var(--aqua)}
.badge.p-info{color:var(--dim)}
.badge.e-verde{color:var(--verde)}
.badge.e-marino{color:var(--marino)}
.badge.e-dorado{color:var(--dorado)}
.badge.e-gris{color:var(--gris)}
a.badge:hover{background:var(--tinte)}

.punto-cuerpo{padding:0 20px 18px 56px}
.compacto .punto:not(.abierto) .punto-cuerpo{display:none}
.punto.plegado:not(.abierto) .punto-cuerpo{display:none}

.accion{
  margin-top:16px; padding:13px 16px;
  background:var(--tinte); border-left:3px solid var(--blue);
  border-radius:0 var(--r) var(--r) 0;
}
.accion .et{
  font-size:10px; font-weight:700; letter-spacing:.11em;
  text-transform:uppercase; color:var(--blue); display:block; margin-bottom:4px;
}
.accion p{font-size:13.5px; color:var(--texto2); max-width:var(--lectura)}

/* ---------- figuras ---------- */
figure{margin:16px 0; break-inside:avoid}
figure img{
  display:block; width:100%; height:auto; cursor:zoom-in;
  border:1px solid var(--linea); border-radius:var(--r); background:var(--bg);
}
figcaption{margin-top:7px; font-size:12px; color:var(--muted); max-width:var(--lectura)}
figcaption b{color:var(--texto2); font-weight:650}

/* ---------- graficos ---------- */
.gr{margin:20px 0; break-inside:avoid}
.gr-cab{margin-bottom:10px}
.gr-cab h4{font-size:14px}
.gr-cab .sub{font-size:12.5px; color:var(--texto2); margin-top:2px; max-width:var(--lectura)}
.gr svg{display:block; width:100%; height:auto; overflow:visible}
.gr-nota{margin-top:8px; font-size:11.5px; color:var(--muted); max-width:var(--lectura)}
.gr .rejilla{stroke:var(--linea); stroke-width:1; shape-rendering:crispEdges}
.gr .eje{stroke:var(--linea2); stroke-width:1; shape-rendering:crispEdges}
.gr .cat{fill:var(--texto2); font-size:13px}
.gr .val{fill:var(--texto); font-size:13px; font-weight:650; font-variant-numeric:tabular-nums}
.gr .det{fill:var(--muted); font-size:11.5px}
.gr .tick{fill:var(--muted); font-size:11px; font-variant-numeric:tabular-nums}
.gr .panel-tit{fill:var(--texto); font-size:12px; font-weight:650}
.gr .val-col{font-size:17px}
.gr .veredicto{font-size:12px; font-weight:700; letter-spacing:.03em}
.gr .banda{fill:var(--banda)}
.gr .barra rect.b{transition:opacity .1s}
.gr .barra:hover rect.b{opacity:.78}
.gr-tiles{display:flex; flex-wrap:wrap; gap:1px; background:var(--linea); border:1px solid var(--linea); border-radius:var(--r); overflow:hidden; margin-bottom:16px}
.gr-tile{background:var(--card); padding:14px 18px; flex:1 1 150px}
.gr-tile b{display:block; font-size:23px; font-weight:650; letter-spacing:-.025em; font-variant-numeric:tabular-nums}
.gr-tile span{display:block; font-size:11.5px; color:var(--texto2); margin-top:3px}
.gr-tile em{display:block; font-size:11px; color:var(--muted); font-style:normal; margin-top:3px}

#tip{
  position:fixed; z-index:120; pointer-events:none; opacity:0;
  max-width:280px; padding:7px 10px;
  background:var(--navy); color:#f4f3f0; font-size:12px; line-height:1.4;
  border-radius:var(--r); box-shadow:0 4px 14px rgba(0,0,0,.22);
  transition:opacity .1s;
}
#tip b{display:block; font-weight:650; margin-bottom:1px}
#tip i{display:block; font-style:normal; opacity:.75; margin-top:2px}

/* ---------- plan ---------- */
.progreso-global{
  display:flex; align-items:center; gap:14px; margin-bottom:26px;
  padding:15px 18px; background:var(--card);
  border:1px solid var(--linea); border-radius:var(--r);
}
.barra-p{flex:1; height:6px; background:var(--tinte); border-radius:3px; overflow:hidden}
.barra-p i{display:block; height:100%; background:var(--aqua); border-radius:3px; transition:width .2s}
.progreso-global .n{font-size:12.5px; color:var(--texto2); white-space:nowrap; font-variant-numeric:tabular-nums}

.bloque{margin-bottom:32px; scroll-margin-top:calc(var(--topbar) + 8px)}
.bloque-cab{padding-bottom:11px; border-bottom:1px solid var(--linea2); margin-bottom:6px}
.bloque-cab h3{font-size:15px; letter-spacing:.01em}
.bloque-cab .desc{font-size:13px; color:var(--texto2); margin-top:5px; max-width:var(--lectura)}
.bloque-cab .mini{display:flex; align-items:center; gap:10px; margin-top:10px}
.bloque-cab .mini .barra-p{max-width:170px}
.bloque-cab .mini .n{font-size:11.5px; color:var(--muted); font-variant-numeric:tabular-nums}

.tarea{display:flex; gap:13px; padding:13px 2px; border-bottom:1px solid var(--linea)}
.tarea:last-child{border-bottom:0}
.tarea input{
  flex:none; width:18px; height:18px; margin-top:1px; cursor:pointer;
  accent-color:var(--aqua);
}
.tarea label{padding:2px 0}
.tarea .cont{flex:1; min-width:0}
.tarea .fila{display:flex; align-items:baseline; gap:9px; flex-wrap:wrap}
.tarea .num{font-size:11px; font-weight:650; color:var(--muted); font-variant-numeric:tabular-nums}
.tarea label{font-size:14px; font-weight:600; cursor:pointer}
.tarea .mods{font-size:10.5px; font-weight:650; letter-spacing:.05em; color:var(--blue)}
.tarea .det{font-size:13px; color:var(--texto2); margin-top:4px; max-width:var(--lectura)}
.tarea.hecha label{color:var(--muted); text-decoration:line-through}
.tarea.hecha .det{opacity:.6}

/* ---------- profundizacion / fuentes ---------- */
.cat{
  margin-bottom:22px; padding:20px 22px; background:var(--card);
  border:1px solid var(--linea); border-radius:var(--r); box-shadow:var(--sombra);
}
.cat h3{font-size:15px; margin-bottom:11px}
.cat ul{margin:0; padding-left:19px}
.cat li{margin-bottom:.6em; font-size:13.5px; color:var(--texto2); max-width:var(--lectura)}
.cat li:last-child{margin-bottom:0}
.cat .esfuerzo{
  margin-top:13px; padding-top:12px; border-top:1px solid var(--linea);
  font-size:12.5px; color:var(--texto2);
}
.lista-fuentes{margin:0; padding-left:19px}
.lista-fuentes li{margin-bottom:.5em; font-size:13px; color:var(--texto2); max-width:var(--lectura)}

/* ---------- filtros ---------- */
.filtros{
  position:sticky; top:var(--topbar); z-index:50;
  margin:0 -40px 22px; padding:12px 40px;
  background:var(--bg);
  border-top:1px solid var(--linea); border-bottom:1px solid var(--linea);
}
.filtro-fila{display:flex; align-items:center; gap:9px; flex-wrap:wrap; margin-bottom:7px}
.filtro-fila:last-child{margin-bottom:0}
.filtro-et{
  font-size:10px; font-weight:650; letter-spacing:.09em; text-transform:uppercase;
  color:var(--muted); width:64px; flex:none;
}
.chip{
  padding:3px 10px; font-size:11.5px; font-weight:600;
  background:var(--card); color:var(--texto2);
  border:1px solid var(--linea2); border-radius:11px; cursor:pointer;
  white-space:nowrap;
}
.chip:hover{border-color:var(--muted); color:var(--texto)}
.chip[aria-pressed="true"]{background:var(--texto); color:var(--card); border-color:var(--texto)}
.chip .c{opacity:.62; font-weight:400; margin-left:3px; font-variant-numeric:tabular-nums}
.chip.limpiar{border-style:dashed; color:var(--muted)}

.sin-resultados{
  padding:44px 40px; text-align:center; color:var(--muted); font-size:14px;
}
mark{background:rgba(235,104,52,.26); color:inherit; border-radius:2px; padding:0 1px}

/* ---------- lightbox ---------- */
#lightbox{
  position:fixed; inset:0; z-index:150; display:none;
  background:rgba(8,9,11,.93); padding:28px;
  align-items:center; justify-content:center;
}
#lightbox.abierto{display:flex}
#lightbox img{max-width:100%; max-height:calc(100vh - 128px); object-fit:contain; border-radius:var(--r)}
#lightbox figcaption{
  position:absolute; left:28px; right:28px; bottom:20px;
  color:#d8d6d1; text-align:center; font-size:12.5px; max-width:none;
}
#lightbox .cerrar{
  position:absolute; top:18px; right:20px; width:34px; height:34px;
  background:rgba(255,255,255,.1); color:#fff; border:0; border-radius:var(--r);
  font-size:19px; cursor:pointer; line-height:1;
}

/* ---------- piezas que solo existen en el móvil ---------- */
.solo-movil{display:none !important}
.zona-controles{display:none}

.fondo-sheet{
  position:fixed; top:var(--topbar); left:0; width:100vw; bottom:0;
  z-index:69; background:rgba(8,9,11,.5);
  opacity:0; pointer-events:none; transition:opacity .18s;
}
.fondo-sheet.abierto{opacity:1; pointer-events:auto}

#btn-filtros .n{
  min-width:16px; padding:0 4px; border-radius:8px; font-size:10px; font-weight:700;
  background:var(--blue); color:#fff; line-height:16px; text-align:center;
}

.fab{
  position:fixed; right:12px; bottom:14px; z-index:58;
  width:40px; height:40px; border-radius:50%;
  background:var(--card); color:var(--texto2);
  border:1px solid var(--linea2); box-shadow:0 3px 12px rgba(0,0,0,.16);
  cursor:pointer; display:none; align-items:center; justify-content:center;
  opacity:0; pointer-events:none; transition:opacity .16s;
}
.fab svg{width:17px; height:17px}
.fab{backdrop-filter:saturate(1.2) blur(6px)}
.fab.visible{opacity:1; pointer-events:auto}

/* ---------- responsive ---------- */
@media (max-width:1040px){
  :root{--sidebar:250px}
  .seccion,.filtros,.portada{padding-left:28px; padding-right:28px}
}

@media (max-width:860px){
  :root{--topbar:56px; --lectura:none}

  .solo-movil{display:inline-flex !important}
  .topbar{z-index:75}
  .topbar .btn{min-height:38px; padding:8px 10px}
  .acciones .btn .et{display:none}
  .marca,.contador,.chev{display:none}
  .zona-controles #diag{align-self:center}
  .topbar{gap:8px; padding:0 12px}

  .shell{display:block}

  /* el índice baja como panel desplegable */
  .sidebar{
    position:fixed; top:var(--topbar); left:0; right:auto; z-index:68;
    width:100vw; max-width:100vw; max-height:calc(100vh - var(--topbar));
    overflow-x:hidden;
    border-right:0; border-bottom:1px solid var(--linea2);
    box-shadow:0 10px 28px rgba(0,0,0,.16);
    padding:14px 0 24px;
  }
  .sidebar[hidden]{display:none !important}
  .zona-controles{
    display:flex; gap:8px; padding:0 18px 16px; margin-bottom:14px;
    border-bottom:1px solid var(--linea);
  }
  .zona-controles .btn{flex:1; justify-content:center; padding:11px 8px; min-height:42px}
  .zona-controles .btn .et{display:inline}
  .nav-a{padding:11px 18px; font-size:14px}
  .nav-titulo{padding-left:18px; padding-right:18px}

  /* los filtros pasan a ser una hoja que sube desde abajo */
  .filtros{
    position:fixed; left:0; right:auto; bottom:0; top:auto; z-index:70;
    margin:0; border-top:1px solid var(--linea2);
    width:100vw; max-width:100vw;
    max-height:72vh; overflow-y:auto; overflow-x:hidden; overscroll-behavior:contain;
    padding:18px 18px calc(18px + env(safe-area-inset-bottom, 0px));
    background:var(--card); border-top:1px solid var(--linea2); border-bottom:0;
    border-radius:14px 14px 0 0; box-shadow:0 -8px 30px rgba(0,0,0,.2);
    transform:translateY(101%); transition:transform .2s ease;
  }
  .filtros[hidden]{display:block !important}
  .filtros.abierta{transform:none}
  .filtros::before{
    content:""; display:block; width:38px; height:4px; border-radius:2px;
    background:var(--linea2); margin:-6px auto 16px;
  }
  .filtro-fila{margin-bottom:14px}
  .filtro-et{width:auto; display:block; margin-bottom:2px}
  .chip{padding:8px 13px; font-size:13px; border-radius:16px}
  #cerrar-filtros{
    position:sticky; bottom:0; z-index:2;
    display:block; width:100%; margin-top:10px; padding:14px;
    background:var(--texto); color:var(--card); border:0; border-radius:var(--r);
    font-size:15px; font-weight:650; cursor:pointer;
    box-shadow:0 -10px 16px -6px var(--card);
  }
  .filtros{padding-bottom:calc(10px + env(safe-area-inset-bottom, 0px))}
  .chip{padding:9px 14px}

  .fab{display:flex}

  .seccion{padding:36px 18px 8px}
  .portada{padding:34px 18px 8px}
  .seccion + .seccion{border-top:0}
  .seccion-cab h2{font-size:21px}
  .portada h1{font-size:27px}
  .ficha{grid-template-columns:1fr; gap:0}
  .ficha dt{border-bottom:0; padding:10px 0 0}
  .ficha dd{padding:2px 0 10px}

  .modulo{margin-bottom:48px}
  .modulo-meta{grid-template-columns:1fr; gap:2px 0}
  .modulo-meta dd{margin-bottom:10px}
  .modulo-cab h2{font-size:19px}

  /* en el móvil los puntos llegan plegados: se recorre el módulo de un vistazo */
  .punto{margin-bottom:10px}
  .punto-cab{padding:15px 16px; gap:12px}
  .punto-tit h3{font-size:15px}
  .punto-cuerpo{padding:0 16px 16px}
  .punto[data-prioridad="CRÍTICA"] .punto-cab{padding-left:13px}
  .compacto .chev{display:block}
  .hallazgo{padding:17px 16px; gap:13px}
  .cat{padding:17px 16px}
  .accion{padding:13px 14px}
  .tarea{padding:16px 2px}
  .tarea input{width:24px; height:24px; margin-top:0}
  .tarea label{font-size:15px; line-height:1.45}
  .modulo-pasos{flex-direction:column}
}

@media (max-width:540px){
  /* el buscador necesita sitio: con tres botones rotulados no le queda */
  #btn-menu .et,#btn-filtros .et{display:none}
}

@media (max-width:420px){
  .seccion,.portada{padding-left:14px; padding-right:14px}
  .punto-cab{padding:14px}
  .punto-cuerpo{padding:0 14px 14px}
  .portada h1{font-size:24px}
  .cifras{grid-template-columns:repeat(2,1fr)}
}

/* el iOS de Safari amplía la página si el campo baja de 16 px */
@media (max-width:860px){
  .buscador input{font-size:16px; padding:10px 34px 10px 36px}
}


/* ======================= EDICIÓN =======================
   Solo se enciende donde el almacén está disponible. En el archivo
   local y en GitHub Pages no hay dónde guardar, así que no aparece. */

.notas{margin-top:26px; padding-top:18px; border-top:1px dashed var(--linea2)}
.notas-et{
  font-size:10px; font-weight:650; letter-spacing:.09em;
  text-transform:uppercase; color:var(--muted); margin-bottom:8px;
}
body:not(.puede-editar) .notas:not(.con-contenido){display:none}

#diag{
  display:inline-flex; align-items:center; gap:6px; flex:none; cursor:pointer;
  padding:4px 10px; border-radius:12px; font-size:11px; font-weight:650;
  letter-spacing:.03em; white-space:nowrap;
  background:var(--tinte); color:var(--texto2); border:1px solid var(--linea2);
}
#diag::before{content:""; width:7px; height:7px; border-radius:50%; background:currentColor}
#diag.ok{color:var(--verde); border-color:var(--verde); background:rgba(27,175,122,.12)}
#diag.mal{color:var(--red); border-color:var(--red); background:rgba(208,59,59,.12)}
#diag-panel{
  position:fixed; z-index:130; right:14px; top:calc(var(--topbar) + 8px);
  width:min(420px, calc(100vw - 24px)); max-height:70vh; overflow:auto;
  padding:16px 18px; border-radius:var(--r);
  background:var(--card); border:1px solid var(--linea2);
  box-shadow:0 10px 34px rgba(0,0,0,.2); display:none;
}
#diag-panel.abierto{display:block}
#diag-panel h4{font-size:13px; margin-bottom:10px}
#diag-panel dl{display:grid; grid-template-columns:max-content 1fr; gap:6px 12px; font-size:12px}
#diag-panel dt{color:var(--muted); white-space:nowrap}
#diag-panel dd{margin:0; color:var(--texto2); word-break:break-word}
#diag-panel dd.si{color:var(--verde); font-weight:600}
#diag-panel dd.no{color:var(--red); font-weight:600}
#diag-panel .pie{margin-top:12px; padding-top:10px; border-top:1px solid var(--linea); font-size:11.5px; color:var(--muted)}

.modo{
  display:inline-flex; align-items:center; gap:6px; flex:none;
  padding:4px 10px; border-radius:12px; font-size:11px; font-weight:650;
  letter-spacing:.04em; text-transform:uppercase; white-space:nowrap;
  background:rgba(27,175,122,.14); color:var(--verde);
  border:1px solid var(--verde);
}
.modo::before{content:""; width:6px; height:6px; border-radius:50%; background:currentColor}

.zona{position:relative}
.zona.vacia:empty::before,
.zona.vacia > p:only-child:empty::before{
  content:"Sin notas."; color:var(--muted); font-size:13px;
}
.zona .prosa{max-width:var(--lectura)}

/* marca discreta de lo que se ha tocado */
.zona.editada::after{
  content:""; position:absolute; left:-14px; top:2px; bottom:2px; width:2px;
  background:var(--aqua); border-radius:1px;
}
.punto[data-prioridad="CRÍTICA"] .zona.editada::after{left:-11px}

/* modo edición */
body.editando .zona{
  outline:1px dashed var(--linea2); outline-offset:6px; border-radius:2px;
  min-height:1.4em;
}
body.editando .zona:hover{outline-color:var(--muted)}
body.editando .zona:focus-within,
body.editando .zona[contenteditable="true"]:focus{
  outline:2px solid var(--blue); outline-offset:6px;
}
.zona[contenteditable="true"]{cursor:text}
.zona[contenteditable="true"] img{
  max-width:100%; height:auto; border-radius:var(--r);
  border:1px solid var(--linea); cursor:default;
}
.zona img.subida{display:block; margin:12px 0; max-width:100%; height:auto;
  border:1px solid var(--linea); border-radius:var(--r)}
.zona.soltando{outline:2px dashed var(--aqua) !important; background:var(--tinte)}

/* lo que se puede escribir con la barra de herramientas */
.zona h4{font-size:15.5px; font-weight:650; margin:16px 0 6px; letter-spacing:.005em}
.zona h4:first-child{margin-top:0}
.zona blockquote{
  margin:10px 0; padding:2px 0 2px 14px;
  border-left:3px solid var(--linea2); color:var(--muted);
}
.zona ul,.zona ol{margin:8px 0 8px 22px; padding:0}
.zona li{margin:3px 0}
.zona a{color:var(--blue); text-decoration:underline; text-underline-offset:2px}
.zona s,.zona strike{text-decoration:line-through; opacity:.72}

/* --------- herramientas de edición ---------
   Dos sitios para lo mismo: la cinta de abajo, siempre a la vista mientras se
   edita, y la burbuja que sale sobre el texto seleccionado en pantalla ancha.
   Las dos se dibujan del mismo listado y las atiende el mismo manejador. */

/* botones, comunes a la cinta y a la burbuja */
#cinta button,#formato button{
  flex:none; min-width:31px; height:31px; padding:0 7px; border:0; border-radius:5px;
  background:transparent; color:#f2f1ee; font-size:13px; line-height:1; cursor:pointer;
  display:inline-flex; align-items:center; justify-content:center; gap:5px;
}
#cinta button:hover,#formato button:hover{background:rgba(255,255,255,.14)}
#cinta button.on,#formato button.on{background:rgba(255,255,255,.24); box-shadow:inset 0 0 0 1px rgba(255,255,255,.28)}
#cinta button:disabled,#formato button:disabled{opacity:.3; cursor:default; background:transparent}
#cinta .sep,#formato .sep{
  flex:none; width:1px; align-self:stretch; margin:3px 4px; background:rgba(255,255,255,.22);
}
#cinta .tinta,#formato .tinta{
  width:17px; height:17px; border-radius:50%; border:1.5px solid rgba(255,255,255,.45);
}
#cinta b,#formato b{font-weight:800}
#cinta .et,#formato .et{font-size:12px; letter-spacing:.01em}
#cinta .glifo,#formato .glifo{font-size:15px}
#cinta svg,#formato svg{display:block; flex:none}

/* burbuja sobre la selección */
#formato{
  position:fixed; z-index:110; display:none; gap:2px; padding:5px;
  background:var(--navy); border-radius:7px; box-shadow:0 6px 20px rgba(0,0,0,.28);
}
#formato.visible{display:flex; flex-wrap:wrap; max-width:min(92vw,344px)}

/* panel de abajo: cinta de herramientas y estado */
#panel-edicion{
  position:fixed; left:0; right:0; bottom:0; z-index:80;
  display:none; flex-direction:column;
  background:var(--navy); color:#f2f1ee;
  box-shadow:0 -4px 18px rgba(0,0,0,.2);
}
body.editando #panel-edicion{display:flex}
#cinta{
  display:flex; align-items:center; gap:2px; padding:7px 12px 6px;
  overflow-x:auto; overflow-y:hidden; scrollbar-width:thin;
  scrollbar-color:rgba(255,255,255,.28) transparent;
  border-bottom:1px solid rgba(255,255,255,.14);
  -webkit-overflow-scrolling:touch;
}
#cinta::-webkit-scrollbar{height:5px}
#cinta::-webkit-scrollbar-thumb{background:rgba(255,255,255,.28); border-radius:3px}
#cinta::-webkit-scrollbar-track{background:transparent}
#cinta .grupo{display:flex; align-items:center; gap:2px; flex:none}

/* barra de estado de la edición */
#barra-edicion{
  display:none; align-items:center; gap:12px; flex-wrap:wrap;
  padding:9px 14px calc(9px + env(safe-area-inset-bottom,0px));
}
body.editando #barra-edicion{display:flex}
#barra-edicion .estado{font-size:12.5px; opacity:.85; flex:1; min-width:120px}
#barra-edicion .estado b{opacity:1; font-weight:600}
#barra-edicion button{
  padding:8px 14px; border-radius:var(--r); border:1px solid rgba(255,255,255,.28);
  background:transparent; color:#f2f1ee; font-size:13px; cursor:pointer; white-space:nowrap;
}
#barra-edicion button:hover{background:rgba(255,255,255,.12)}
#barra-edicion button.primario{background:var(--aqua); border-color:var(--aqua); color:#07281c; font-weight:650}
#barra-edicion .punto-rojo{width:7px; height:7px; border-radius:50%; background:var(--orange); flex:none}
#barra-edicion .corta{display:none}

/* el panel no puede taparle a nadie el último párrafo: su altura se mide en
   marcha y se le devuelve al documento como hueco */
body.editando{padding-bottom:var(--panel-edicion,118px)}
body.editando .fab{bottom:calc(var(--panel-edicion,118px) + 12px)}

@media (max-width:760px){
  /* con la cinta siempre a mano, la burbuja solo estorbaría: en el móvil pelea
     con el menú de selección del propio sistema */
  #formato{display:none !important}
  #cinta{padding:7px 8px 6px}
  #barra-edicion{gap:8px; padding:8px 10px calc(8px + env(safe-area-inset-bottom,0px))}
  #barra-edicion button{padding:8px 11px; font-size:12.5px}
  #barra-edicion .estado{flex:1 1 100%; order:-1; min-width:0}
  #barra-edicion .larga{display:none}
  #barra-edicion .corta{display:inline}
}

/* aviso de solo lectura */
#aviso-lectura{
  position:fixed; left:50%; transform:translateX(-50%); bottom:18px; z-index:112;
  padding:10px 16px; border-radius:20px; font-size:13px;
  background:var(--navy); color:#f2f1ee; box-shadow:0 4px 16px rgba(0,0,0,.24);
  opacity:0; pointer-events:none; transition:opacity .2s;
}
#aviso-lectura.visible{opacity:1}
body.editando #aviso-lectura{bottom:calc(var(--panel-edicion,118px) + 14px)}

@media print{
  #formato,#panel-edicion,#aviso-lectura,.notas-et{display:none !important}
  body.editando{padding-bottom:0}
  .zona{outline:0 !important}
  .zona.editada::after{display:none}
  .notas{display:block !important}
}

/* quien pide menos movimiento no lo tiene */
@media (prefers-reduced-motion: reduce){
  *,*::before,*::after{
    animation-duration:.01ms !important; animation-iteration-count:1 !important;
    transition-duration:.01ms !important; scroll-behavior:auto !important;
  }
}

/* ---------- impresion ---------- */
@media print{
  :root{--bg:#fff; --card:#fff; --texto:#000; --texto2:#222; --linea:#ccc; --linea2:#999; --tinte:#f4f4f4; --sombra:none}
  .topbar,.sidebar,.filtros,.acciones,.buscador,#lightbox,#tip,.saltar,.chev{display:none !important}
  body{font-size:10.5pt; background:#fff; padding-top:0}
  .shell{display:block}
  main{padding:0}
  .seccion,.portada{padding:0 0 6mm; break-before:page}
  .portada{break-before:auto}
  .punto-cuerpo,.compacto .punto:not(.abierto) .punto-cuerpo,.punto.plegado:not(.abierto) .punto-cuerpo{display:block !important}
  .punto[hidden]{display:none !important}
  .punto{break-inside:avoid; box-shadow:none; border:1px solid #ccc; margin-bottom:5mm}
  .modulo{break-before:page}
  figure,table,.tabla-caja,.gr,.hallazgo,.cat,.tarea{break-inside:avoid}
  thead{display:table-header-group}
  .tabla-caja{overflow:visible}
  a{color:#000; text-decoration:none}
  .accion{background:#f4f4f4 !important; border-left:3px solid #666}
  mark{background:none; font-weight:700}
  .gr svg{max-height:none}
}
"""


# ==========================================================================
#  JavaScript
# ==========================================================================

JS = r"""
'use strict';

const DATA = JSON.parse(document.getElementById('datos').textContent);
const SERVIDOR = (function(){
  const el = document.getElementById('servidor');
  try { return el ? JSON.parse(el.textContent) : null; } catch (e){ return null; }
})();
const IMGS = JSON.parse(document.getElementById('capturas-b64').textContent);

/* ---------------- utilidades ---------------- */
const $  = (s, r) => (r || document).querySelector(s);
const $$ = (s, r) => Array.prototype.slice.call((r || document).querySelectorAll(s));

function esc(s){
  return String(s == null ? '' : s)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;');
}
function norm(s){
  return String(s == null ? '' : s)
    .normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
}
function slug(s){
  return norm(s).replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');
}

/* almacenamiento tolerante: si no hay localStorage, el informe sigue funcionando */
const Store = {
  get(k, d){
    try{ const v = localStorage.getItem(k); return v === null ? d : JSON.parse(v); }
    catch(e){ return d; }
  },
  set(k, v){
    try{ localStorage.setItem(k, JSON.stringify(v)); return true; }
    catch(e){ return false; }
  }
};

/* ---------------- vocabularios cerrados ---------------- */
const CLASE_PRIORIDAD = {
  'CRÍTICA':'p-critica', 'ALTA':'p-alta', 'MEDIA':'p-media', 'BAJA':'p-baja', '—':'p-info'
};
const ORDEN_PRIORIDAD = ['CRÍTICA','ALTA','MEDIA','BAJA','—'];
const CLASE_ESTADO = {
  'VERIFICADO':'e-verde',
  'ENTREGADO':'e-verde',
  'DIAGNÓSTICO POR EVIDENCIA':'e-marino',
  'HALLAZGO ESTRUCTURAL':'e-marino',
  'DATO INTERNO DE LA CUENTA':'e-dorado',
  'REQUIERE MONITORIZACIÓN CONTINUA':'e-dorado',
  'REQUIERE MATERIAL ORIGINAL':'e-dorado',
  'FASE 2 — PROFUNDIZACIÓN':'e-dorado',
  'EXCLUIDO POR CRITERIO PROFESIONAL':'e-gris'
};
const COLOR_PRIORIDAD = {
  'CRÍTICA':'var(--red)', 'ALTA':'var(--orange)', 'MEDIA':'var(--blue)',
  'BAJA':'var(--aqua)', '—':'var(--dim)'
};

/* definiciones de estado, tomadas literalmente de «Cómo leer este documento» */
const DEF_ESTADO = {};
(DATA.como_leer || []).forEach(function(sec){
  (sec[1] || []).forEach(function(p){
    if (p.lead) DEF_ESTADO[p.lead.replace(/[.:—\s]+$/,'').trim()] = p.t;
  });
});

/* ---------------- índice de búsqueda ---------------- */
const PUNTOS = [];
DATA.modulos.forEach(function(m){
  m.puntos.forEach(function(p){
    const partes = [p.punto, p.accion];
    (p.hallazgo || []).forEach(function(h){ partes.push(h.t); });
    if (p.tabla){
      partes.push(p.tabla.headers.join(' '));
      p.tabla.rows.forEach(function(r){ partes.push(r.join(' ')); });
    }
    PUNTOS.push({
      id: m.id.toLowerCase() + '-p' + p.n,
      modulo: m.id, n: p.n,
      estado: p.estado, prioridad: p.prioridad,
      texto: norm(partes.join(' \u00b7 '))
    });
  });
});

const CAPTURA_DE = {};
(DATA.capturas || []).forEach(function(c){
  const k = c.modulo + '-' + c.punto;
  (CAPTURA_DE[k] = CAPTURA_DE[k] || []).push(c);
});
const GRAFICO_DE = {};
(DATA.graficos || []).forEach(function(g){
  if (g.modulo && g.punto) GRAFICO_DE[g.modulo + '-' + g.punto] = g;
});

/* recuento de prioridades por módulo (no viene precalculado) */
const CUENTA = {};
DATA.modulos.forEach(function(m){
  const c = {'CRÍTICA':0,'ALTA':0,'MEDIA':0,'BAJA':0,'—':0};
  m.puntos.forEach(function(p){ if (c[p.prioridad] !== undefined) c[p.prioridad]++; });
  CUENTA[m.id] = c;
});

/* =========================================================================
   Render de texto
   ========================================================================= */

/* Un párrafo de hallazgo: la entradilla en versalitas va en negrita.
   'lead' es el prefijo exacto que el documento original marca en negrita. */
function parrafo(p){
  const t = p && p.t ? p.t : '';
  const lead = p && p.lead ? p.lead : '';
  if (lead && t.indexOf(lead) === 0){
    return '<p><b class="lead">' + esc(lead) + '</b>' + esc(t.slice(lead.length)) + '</p>';
  }
  return '<p>' + esc(t) + '</p>';
}
function prosa(ps){
  return '<div class="prosa">' + (ps || []).map(parrafo).join('') + '</div>';
}

function tablaHTML(t){
  if (!t) return '';
  let h = '<div class="tabla-caja"><table><thead><tr>';
  t.headers.forEach(function(c){ h += '<th>' + esc(c) + '</th>'; });
  h += '</tr></thead><tbody>';
  t.rows.forEach(function(r){
    h += '<tr>';
    r.forEach(function(c){ h += '<td>' + esc(c) + '</td>'; });
    h += '</tr>';
  });
  return h + '</tbody></table></div>';
}

function badgePrioridad(v){
  return '<span class="badge ' + (CLASE_PRIORIDAD[v] || 'p-info') + '" data-tip-t="Prioridad" data-tip-d="' +
    esc(v) + '">' + esc(v === '—' ? '— informativo' : v) + '</span>';
}
function badgeEstado(v){
  const def = DEF_ESTADO[v] || '';
  return '<a class="badge ' + (CLASE_ESTADO[v] || 'e-gris') + '" href="#como-leer"' +
    ' data-tip-t="' + esc(v) + '" data-tip-d="' + esc(def || 'Tipo de evidencia. Ver «Cómo leer este informe».') + '">' +
    esc(v) + '</a>';
}

/* =========================================================================
   Gráficos — SVG a mano, sin librerías
   ========================================================================= */

const VB = 1000;

function ejeMax(vals){
  const m = Math.max.apply(null, vals.map(Math.abs).concat([0]));
  if (m <= 0) return 1;
  const exp = Math.pow(10, Math.floor(Math.log(m) / Math.LN10));
  const paso = m / exp <= 2 ? exp / 2 : (m / exp <= 5 ? exp : exp * 2);
  return Math.ceil(m / paso) * paso;
}

/* Ancho aproximado de una cadena en unidades del viewBox. No hace falta
   precision tipografica: solo dimensionar la columna de etiquetas. */
function anchoTexto(s, tam){
  let w = 0;
  for (let i = 0; i < s.length; i++){
    const ch = s[i];
    if (/[A-ZÁÉÍÓÚÑÜ0-9@#%&]/.test(ch)) w += tam * 0.72;
    else if (/[iljtfr.,'·:;!| ]/.test(ch)) w += tam * 0.34;
    else if (/[mwMW]/.test(ch)) w += tam * 0.88;
    else w += tam * 0.58;
  }
  return w;
}
function recortar(s, maxW, tam){
  if (anchoTexto(s, tam) <= maxW) return s;
  let t = s;
  while (t.length > 3 && anchoTexto(t + '…', tam) > maxW) t = t.slice(0, -1);
  return t.replace(/[\s·,.\-–—]+$/, '') + '…';
}

/* El color de cada barra se midio sobre el PNG original, pixel a pixel:
   es el del grafico del informe, no una interpretacion. */
const COLOR_BARRA = {
  blue:'var(--blue)', orange:'var(--orange)', aqua:'var(--aqua)',
  red:'var(--red)', dim:'var(--barra-base)', base:'var(--barra-base)',
  navy:'var(--texto)'
};
function colorBarra(b){
  if (b.color && COLOR_BARRA[b.color]) return COLOR_BARRA[b.color];
  if (b.destaca === 'A') return 'var(--aqua)';
  if (b.destaca === 'B') return 'var(--red)';
  return 'var(--barra-base)';
}

function tipAttrs(b, unidad){
  return ' data-tip-t="' + esc(b.cat) + '"' +
         ' data-tip-v="' + esc(b.etiqueta + (unidad ? ' ' + unidad : '')) + '"' +
         (b.detalle ? ' data-tip-d="' + esc(b.detalle) + '"' : '');
}

/* Panel de barras horizontales. Devuelve {svg, alto}. */
function panelBarras(panel, opts){
  opts = opts || {};
  const barras = panel.barras || [];
  const TAM_CAT = 13, TAM_DET = 11.5;
  let anchoLbl = opts.anchoLbl;
  if (anchoLbl == null){
    let mx = 0;
    barras.forEach(function(b){
      mx = Math.max(mx, anchoTexto(b.cat || '', TAM_CAT));
      if (b.detalle) mx = Math.max(mx, anchoTexto(b.detalle, TAM_DET));
    });
    anchoLbl = Math.min(opts.maxLbl != null ? opts.maxLbl : 360, Math.max(110, mx + 16));
  }
  const x0 = opts.x0 != null ? opts.x0 : 0;
  const ancho = opts.ancho != null ? opts.ancho : VB;
  const rowH = opts.rowH != null ? opts.rowH : 30;
  const gap = opts.gap != null ? opts.gap : 9;
  const divergente = !!opts.divergente;
  /* hueco para la etiqueta de valor, segun la etiqueta mas larga del panel */
  let finEtiqueta = 26;
  barras.forEach(function(b){
    finEtiqueta = Math.max(finEtiqueta, anchoTexto(b.etiqueta || '', 13) + 20);
  });
  finEtiqueta = Math.min(finEtiqueta, 130);
  const bx = x0 + anchoLbl;                      // inicio del área de barras
  const bw = ancho - anchoLbl - finEtiqueta;

  let y = opts.y0 || 0;
  let s = '';

  let dominio = barras.map(function(b){ return b.valor; });
  if (panel.banda) dominio = dominio.concat([panel.banda.min, panel.banda.max]);
  const max = opts.max != null ? opts.max : ejeMax(dominio);
  const cero = divergente ? bx + bw / 2 : bx;
  const escala = divergente ? (bw / 2) / max : bw / max;

  if (panel.nombre){
    s += '<text class="panel-tit" x="' + x0 + '" y="' + (y + 11) + '">' + esc(panel.nombre) + '</text>';
    y += 26;
  }

  const yTop = y;
  const alturaBarras = barras.length * (rowH + gap) - gap;

  /* rejilla discreta */
  const nT = divergente ? 4 : 4;
  for (let i = 0; i <= nT; i++){
    const v = divergente ? (-max + (2 * max * i) / nT) : (max * i) / nT;
    const gx = cero + v * escala;
    s += '<line class="rejilla" x1="' + gx.toFixed(1) + '" y1="' + yTop +
         '" x2="' + gx.toFixed(1) + '" y2="' + (yTop + alturaBarras) + '"/>';
  }
  if (divergente){
    s += '<line class="eje" x1="' + cero + '" y1="' + yTop + '" x2="' + cero +
         '" y2="' + (yTop + alturaBarras) + '"/>';
  }

  /* banda de referencia sombreada, detrás de las barras */
  if (panel.banda){
    const b1 = cero + panel.banda.min * escala;
    const b2 = cero + panel.banda.max * escala;
    s += '<rect class="banda" x="' + Math.min(b1,b2).toFixed(1) + '" y="' + yTop +
         '" width="' + Math.abs(b2-b1).toFixed(1) + '" height="' + alturaBarras + '"/>';
    if (panel.banda.etiqueta){
      s += '<text class="det" x="' + ((b1+b2)/2).toFixed(1) + '" y="' + (yTop - 6) +
           '" text-anchor="middle">' + esc(panel.banda.etiqueta) + '</text>';
    }
  }

  barras.forEach(function(b){
    const v = b.valor || 0;
    const w = Math.abs(v) * escala;
    const bxi = v < 0 ? cero - w : cero;
    const cy = y + rowH / 2;

    s += '<g class="barra"' + tipAttrs(b, panel.unidad) + '>';
    /* pista de fondo, casi invisible */
    s += '<rect x="' + bx + '" y="' + y + '" width="' + (bw) + '" height="' + rowH +
         '" fill="transparent"/>';
    s += '<rect class="b" x="' + bxi.toFixed(1) + '" y="' + y + '" width="' + Math.max(w,1).toFixed(1) +
         '" height="' + rowH + '" fill="' + colorBarra(b) + '" rx="1"/>';

    /* etiqueta de categoría */
    s += '<text class="cat" data-max="' + (anchoLbl - 14).toFixed(0) + '" x="' + (x0 + anchoLbl - 12) +
         '" y="' + (cy + 4.5) + '" text-anchor="end">' + esc(b.cat || '') + '</text>';

    /* etiqueta de valor, directamente sobre la barra */
    const vx = v < 0 ? bxi - 8 : bxi + w + 8;
    const anc = v < 0 ? 'end' : 'start';
    s += '<text class="val" x="' + vx.toFixed(1) + '" y="' + (cy + 4.5) +
         '" text-anchor="' + anc + '">' + esc(b.etiqueta) + '</text>';

    if (b.detalle){
      s += '<text class="det" data-max="' + (anchoLbl - 14).toFixed(0) + '" x="' + (x0 + anchoLbl - 12) +
           '" y="' + (cy + 17) + '" text-anchor="end">' + esc(b.detalle) + '</text>';
    }
    s += '</g>';
    y += rowH + gap;
  });

  return { svg: s, alto: y - (opts.y0 || 0) - gap };
}

/* g4 — tres paneles con columna vertical y banda de referencia sombreada
   detras, tal y como esta en la figura original. Cada panel lleva su propia
   escala: las tres metricas no son comparables entre si. */
function panelesConBanda(g){
  const paneles = g.paneles || [];
  const n = paneles.length || 1;
  const HUECO = 38;
  const ANCHO = (VB - HUECO * (n - 1)) / n;
  const Y_TIT = 13, Y_TOP = 54, ALTO = 186;
  const Y_BASE = Y_TOP + ALTO;
  let s = '';

  paneles.forEach(function(p, i){
    const x0 = i * (ANCHO + HUECO);
    const b = (p.barras || [])[0];
    if (!b) return;
    let dominio = [b.valor];
    if (p.banda) dominio = dominio.concat([p.banda.min, p.banda.max]);
    const max = ejeMax(dominio);
    const k = ALTO / max;

    s += '<text class="panel-tit" x="' + (x0 + ANCHO / 2).toFixed(1) + '" y="' + Y_TIT +
         '" text-anchor="middle">' + esc(p.nombre) + '</text>';

    /* banda de referencia, detras de la columna */
    if (p.banda){
      const yA = Y_BASE - p.banda.max * k;
      const yB = Y_BASE - p.banda.min * k;
      s += '<rect class="banda" x="' + x0.toFixed(1) + '" y="' + yA.toFixed(1) +
           '" width="' + ANCHO.toFixed(1) + '" height="' + Math.max(yB - yA, 3).toFixed(1) + '"/>';
      if (p.banda.etiqueta){
        const m = p.banda.etiqueta.match(/^(\S+)\s+(.+)$/);
        const yc = (yA + yB) / 2;
        const xe = x0 + ANCHO - 12;
        if (m){
          s += '<text class="det" x="' + xe.toFixed(1) + '" y="' + (yc - 2).toFixed(1) +
               '" text-anchor="end">' + esc(m[1]) + '</text>';
          s += '<text class="det" x="' + xe.toFixed(1) + '" y="' + (yc + 14).toFixed(1) +
               '" text-anchor="end">' + esc(m[2]) + '</text>';
        } else {
          s += '<text class="det" x="' + xe.toFixed(1) + '" y="' + (yc + 5).toFixed(1) +
               '" text-anchor="end">' + esc(p.banda.etiqueta) + '</text>';
        }
      }
    }

    /* la columna */
    const cw = ANCHO * 0.30;
    const cx = x0 + ANCHO * 0.13;
    const h = Math.max(b.valor * k, 3);
    const cy = Y_BASE - h;
    s += '<g class="barra"' + tipAttrs(b, p.unidad) + '>' +
         '<rect class="b" x="' + cx.toFixed(1) + '" y="' + cy.toFixed(1) +
         '" width="' + cw.toFixed(1) + '" height="' + h.toFixed(1) +
         '" fill="' + colorBarra(b) + '"/></g>';

    /* etiqueta de valor, justo encima de la columna */
    s += '<text class="val val-col" x="' + cx.toFixed(1) + '" y="' + (cy - 11).toFixed(1) +
         '">' + esc(b.etiqueta) + '</text>';

    /* linea de base */
    s += '<line class="eje" x1="' + x0.toFixed(1) + '" y1="' + Y_BASE +
         '" x2="' + (x0 + ANCHO).toFixed(1) + '" y2="' + Y_BASE + '"/>';

    /* bajo la base: que mide y como sale. El texto es literal; solo se parte
       en dos lineas por el separador que ya trae. */
    const partes = (b.detalle || '').split(' · ');
    if (partes[0]){
      s += '<text class="det" x="' + (x0 + ANCHO / 2).toFixed(1) + '" y="' + (Y_BASE + 21) +
           '" text-anchor="middle">' + esc(partes[0]) + '</text>';
    }
    if (partes[1]){
      s += '<text class="veredicto" x="' + (x0 + ANCHO / 2).toFixed(1) + '" y="' + (Y_BASE + 41) +
           '" text-anchor="middle" fill="' + colorBarra(b) + '">' + esc(partes[1]) + '</text>';
    }
  });

  return svgEnvoltorio(s, Y_BASE + 52);
}

function svgEnvoltorio(inner, alto){
  return '<svg viewBox="0 0 ' + VB + ' ' + Math.ceil(alto) + '" preserveAspectRatio="xMidYMid meet" ' +
         'role="img" xmlns="http://www.w3.org/2000/svg">' + inner + '</svg>';
}

function dibujarGrafico(g){
  const paneles = g.paneles || [];
  let inner = '', alto = 0;

  if (g.tipo === 'barhDoble' && paneles.length >= 2){
    const anchoPanel = VB / 2 - 18;
    const a = panelBarras(paneles[0], {x0:0, ancho:anchoPanel, maxLbl:200, rowH:26, gap:8});
    const b = panelBarras(paneles[1], {x0:VB/2 + 18, ancho:anchoPanel, maxLbl:160, rowH:26, gap:8});
    inner = a.svg + b.svg;
    alto = Math.max(a.alto, b.alto) + 12;

  } else if (g.tipo === 'panelesConBanda'){
    return panelesConBanda(g);

  } else if (g.tipo === 'barh+composicion' && paneles.length >= 2){
    const a = panelBarras(paneles[0], {x0:0, ancho:VB*0.63, maxLbl:250, rowH:22, gap:6});
    const b = panelBarras(paneles[1], {x0:VB*0.63 + 26, ancho:VB*0.37 - 26, maxLbl:180, rowH:26, gap:9});
    inner = a.svg + b.svg;
    alto = Math.max(a.alto, b.alto) + 12;

  } else if (g.tipo === 'divergente'){
    const r = panelBarras(paneles[0] || {barras:[]}, {x0:0, ancho:VB, maxLbl:330, rowH:30, gap:10, divergente:true});
    inner = r.svg; alto = r.alto + 12;

  } else if (g.tipo === 'apiladaPorModulo'){
    return dibujarApilada(g);

  } else {
    let y = 0;
    paneles.forEach(function(p){
      const r = panelBarras(p, {x0:0, ancho:VB, maxLbl:380, rowH:30, gap:10, y0:y});
      inner += r.svg;
      y += r.alto + 30;
    });
    alto = y + 6;
  }

  return svgEnvoltorio(inner, alto);
}

/* g9 — dos paneles: la distribucion de prioridades modulo a modulo y el
   total del diagnostico. Los recuentos NO vienen precalculados: se cuentan
   aqui sobre modulos[].puntos[].prioridad. */
function dibujarApilada(g){
  const ROW = 22, GAP = 7;
  const ANCHO_IZQ = VB * 0.56, X_DER = VB * 0.615;
  const LBL_IZQ = 52, FIN_IZQ = 52;
  const bxI = LBL_IZQ, bwI = ANCHO_IZQ - LBL_IZQ - FIN_IZQ;
  const total = DATA.modulos.reduce(function(a, m){ return a + m.puntos.length; }, 0);
  const maxTot = Math.max.apply(null, DATA.modulos.map(function(m){ return m.puntos.length; }));

  let s = '', y = 0;
  s += '<text class="panel-tit" x="0" y="11">Puntos por módulo</text>';
  s += '<text class="panel-tit" x="' + X_DER + '" y="11">Total del diagnóstico</text>';
  y = 34;

  const yTop = y;
  DATA.modulos.forEach(function(m){
    const c = CUENTA[m.id];
    const n = m.puntos.length;
    let x = bxI;
    const cy = y + ROW / 2;
    s += '<text class="cat" x="' + (LBL_IZQ - 12) + '" y="' + (cy + 4.5) +
         '" text-anchor="end">' + esc(m.id) + '</text>';
    ORDEN_PRIORIDAD.forEach(function(pr){
      const k = c[pr];
      if (!k) return;
      const w = (k / maxTot) * bwI;
      s += '<g class="barra" data-tip-t="' + esc(m.id + ' · ' + m.titulo) + '"' +
           ' data-tip-v="' + k + (k === 1 ? ' punto ' : ' puntos ') +
           esc(pr === '—' ? 'informativos' : 'de prioridad ' + pr.toLowerCase()) + '"' +
           ' data-tip-d="' + n + ' puntos en el módulo">' +
           '<rect class="b" x="' + x.toFixed(1) + '" y="' + y + '" width="' + Math.max(w, 1).toFixed(1) +
           '" height="' + ROW + '" fill="' + COLOR_PRIORIDAD[pr] + '"/></g>';
      x += w;
    });
    s += '<text class="tick" x="' + (x + 9).toFixed(1) + '" y="' + (cy + 4.5) + '">' + n + '</text>';
    y += ROW + GAP;
  });
  const yFinIzq = y;

  /* panel derecho: el total por prioridad */
  const LBL_DER = 104, FIN_DER = 104;
  const bxD = X_DER + LBL_DER;
  const bwD = VB - bxD - FIN_DER;
  const maxPr = Math.max.apply(null, ORDEN_PRIORIDAD.map(function(pr){ return CUENTA_TOTAL[pr]; }));
  const alto = 54, hueco = (yFinIzq - yTop - 5 * alto) / 4;
  let yd = yTop;
  ORDEN_PRIORIDAD.forEach(function(pr){
    const n = CUENTA_TOTAL[pr];
    const w = (n / maxPr) * bwD;
    const pct = Math.round(n / total * 100);
    const cy = yd + alto / 2;
    s += '<text class="cat" x="' + (bxD - 12) + '" y="' + (cy + 4.5) + '" text-anchor="end">' +
         esc(pr === '—' ? 'Informativo' : pr) + '</text>';
    s += '<g class="barra" data-tip-t="' + esc(pr === '—' ? 'Informativo · sin corrección' : pr) + '"' +
         ' data-tip-v="' + n + ' de ' + total + ' puntos · ' + pct + ' %">' +
         '<rect class="b" x="' + bxD + '" y="' + yd + '" width="' + Math.max(w, 1).toFixed(1) +
         '" height="' + alto + '" fill="' + COLOR_PRIORIDAD[pr] + '"/></g>';
    s += '<text class="val" x="' + (bxD + w + 10).toFixed(1) + '" y="' + (cy + 4.5) + '">' +
         n + '   (' + pct + ' %)</text>';
    yd += alto + hueco;
  });

  /* leyenda: cinco series apiladas la hacen imprescindible */
  y += 16;
  let lx = 0;
  ORDEN_PRIORIDAD.forEach(function(pr){
    const et = pr === '—' ? 'Informativo' : pr.charAt(0) + pr.slice(1).toLowerCase();
    s += '<rect x="' + lx + '" y="' + (y - 9) + '" width="10" height="10" fill="' +
         COLOR_PRIORIDAD[pr] + '"/>';
    s += '<text class="tick" x="' + (lx + 15) + '" y="' + y + '">' + esc(et) + '</text>';
    lx += 25 + anchoTexto(et, 11) + 22;
  });
  y += 10;

  return svgEnvoltorio(s, Math.max(y, yd + 6));
}

/* La estimacion de ancho sirve para dimensionar la columna; el recorte
   definitivo se hace midiendo el texto ya renderizado, que es exacto. */
function ajustarEtiquetas(raiz){
  const textos = (raiz || document).querySelectorAll('figure.gr svg text[data-max]');
  for (let i = 0; i < textos.length; i++){
    const t = textos[i];
    const max = parseFloat(t.getAttribute('data-max'));
    const completo = t.getAttribute('data-full') || t.textContent;
    t.setAttribute('data-full', completo);
    t.textContent = completo;
    let largo;
    try { largo = t.getComputedTextLength(); } catch (e) { continue; }
    if (largo <= max) continue;
    let lo = 0, hi = completo.length;
    while (lo < hi){
      const mid = Math.ceil((lo + hi) / 2);
      t.textContent = completo.slice(0, mid) + '…';
      if (t.getComputedTextLength() <= max) lo = mid; else hi = mid - 1;
    }
    t.textContent = completo.slice(0, lo).replace(/[\s·,.\-–—]+$/, '') + '…';
    /* la etiqueta recortada mantiene el texto integro en el tooltip */
    const g = t.closest('g.barra');
    if (g && !g.getAttribute('data-tip-d')) g.setAttribute('data-tip-d', completo);
  }
}

function graficoHTML(g){
  if (!g) return '';
  let h = '<figure class="gr" id="grafico-' + esc(g.id) + '">';
  h += '<div class="gr-cab"><h4>' + esc(g.titulo) + '</h4>';
  if (g.subtitulo) h += '<div class="sub">' + esc(g.subtitulo) + '</div>';
  h += '</div>';
  if (g.tiles && g.tiles.length){
    h += '<div class="gr-tiles">';
    g.tiles.forEach(function(t){
      h += '<div class="gr-tile"><b>' + esc(t.valor) + '</b><span>' + esc(t.etiqueta) + '</span>' +
           (t.detalle ? '<em>' + esc(t.detalle) + '</em>' : '') + '</div>';
    });
    h += '</div>';
  }
  h += dibujarGrafico(g);
  if (g.nota) h += '<figcaption class="gr-nota">' + esc(g.nota) + '</figcaption>';
  return h + '</figure>';
}

/* =========================================================================
   Render de las secciones
   ========================================================================= */

function figuraHTML(c){
  if (!c) return '';
  const src = IMGS[c.archivo];
  if (!src) return '';
  const alt = 'Figura ' + c.figura + '. ' + c.pie;
  /* incrustadas van ya decodificadas; como archivo suelto se piden al llegar */
  const diferida = DATA.meta.capturas_aparte ? ' loading="lazy" decoding="async"' : '';
  return '<figure id="figura-' + c.figura + '">' +
    '<img src="' + src + '" alt="' + esc(alt) + '" width="' + c.ancho + '" height="' + c.alto + '"' +
    ' data-fig="' + c.figura + '"' + diferida + '>' +
    '<figcaption><b>Figura ' + c.figura + '.</b> ' + esc(c.pie) + '</figcaption></figure>';
}

function puntoHTML(m, p){
  const id = m.id.toLowerCase() + '-p' + p.n;
  const clave = m.id + '-' + p.n;
  let h = '<article class="punto" id="' + id + '" data-modulo="' + m.id + '"' +
          ' data-prioridad="' + esc(p.prioridad) + '" data-estado="' + esc(p.estado) + '">';

  h += '<div class="punto-cab" role="button" tabindex="0" aria-expanded="true">' +
       '<svg class="chev" viewBox="0 0 16 16" aria-hidden="true"><path d="M6 3l5 5-5 5" fill="none" stroke="currentColor" stroke-width="1.8"/></svg>' +
       '<span class="punto-n">' + p.n + '</span>' +
       '<div class="punto-tit"><h3>' + esc(p.punto) + '</h3>' +
       '<div class="distintivos">' + badgePrioridad(p.prioridad) + badgeEstado(p.estado) + '</div>' +
       '</div></div>';

  h += '<div class="punto-cuerpo">';
  h += '<div class="zona" data-edit="' + id + '-h">' + prosa(p.hallazgo) + '</div>';
  if (p.tabla) h += tablaHTML(p.tabla);
  (CAPTURA_DE[clave] || []).forEach(function(c){ h += figuraHTML(c); });
  if (GRAFICO_DE[clave]) h += graficoHTML(GRAFICO_DE[clave]);
  h += '<div class="accion"><span class="et">Acción</span>' +
       '<div class="zona" data-edit="' + id + '-a"><p>' + esc(p.accion) + '</p></div></div>';
  h += '</div></article>';
  return h;
}

function moduloHTML(m, i, todos){
  const c = CUENTA[m.id];
  let h = '<section class="modulo" id="' + m.id.toLowerCase() + '">';
  h += '<div class="modulo-cab"><div class="id">' + esc(m.id) + '</div><h2>' + esc(m.titulo) + '</h2>';

  h += '<div class="modulo-cifras">';
  h += '<span class="mp"><b>' + m.puntos.length + '</b> puntos</span>';
  if (c['CRÍTICA']) h += '<span class="mp c"><b>' + c['CRÍTICA'] + '</b> ' +
    (c['CRÍTICA'] === 1 ? 'crítico' : 'críticos') + '</span>';
  if (c['ALTA']) h += '<span class="mp a"><b>' + c['ALTA'] + '</b> alta</span>';
  h += '</div>';

  h += '<dl class="modulo-meta">';
  if (m.calificacion) h += '<dt>Valoración</dt><dd>' + esc(m.calificacion) + '</dd>';
  if (m.estado_modulo) h += '<dt>Estado</dt><dd>' + esc(m.estado_modulo) + '</dd>';
  if (m.alcance) h += '<dt>Alcance</dt><dd>' + esc(m.alcance) + '</dd>';
  if (m.fuente) h += '<dt>Fuente</dt><dd>' + esc(m.fuente) + '</dd>';
  h += '</dl></div>';

  if (m.resumen && m.resumen.length)
    h += '<div class="modulo-resumen"><div class="zona" data-edit="' + m.id.toLowerCase() +
         '-res">' + prosa(m.resumen) + '</div></div>';
  m.puntos.forEach(function(p){ h += puntoHTML(m, p); });

  /* espacio propio del equipo al cierre del módulo */
  h += '<div class="notas" data-notas="' + m.id.toLowerCase() + '">' +
       '<div class="notas-et">Notas del equipo</div>' +
       '<div class="zona vacia" data-edit="' + m.id.toLowerCase() + '-n"><p></p></div></div>';

  /* pasar al módulo contiguo sin volver al índice */
  const ant = todos[i - 1], sig = todos[i + 1];
  h += '<nav class="modulo-pasos" aria-label="Módulos contiguos">';
  h += ant
    ? '<a class="paso" href="#' + ant.id.toLowerCase() + '"><span>← ' + esc(ant.id) +
      ' anterior</span><b>' + esc(ant.titulo) + '</b></a>'
    : '<span class="paso vacio"></span>';
  h += sig
    ? '<a class="paso sig" href="#' + sig.id.toLowerCase() + '"><span>' + esc(sig.id) +
      ' siguiente →</span><b>' + esc(sig.titulo) + '</b></a>'
    : '<span class="paso vacio"></span>';
  h += '</nav>';
  return h + '</section>';
}

function graficoSuelto(id){
  const g = (DATA.graficos || []).filter(function(x){ return x.id === id; })[0];
  return g ? graficoHTML(g) : '';
}

function render(){
  const meta = DATA.meta, por = DATA.portada;
  let h = '';

  /* ---------- portada + resumen ejecutivo ---------- */
  h += '<section class="portada" id="portada">';
  h += '<div class="eyebrow">' + esc(meta.base_contractual || '') + '</div>';
  h += '<h1>' + esc(meta.titulo) + '</h1>';
  h += '<div class="sub">' + esc(meta.subtitulo) + '</div>';
  h += '<div class="sujeto">' + esc(meta.sujeto) + '</div>';
  h += '<div class="cargo">' + esc(meta.cargo) + '</div>';

  h += '<dl class="ficha">';
  [['Cliente', meta.cliente], ['Alcance', meta.alcance],
   ['Fuentes', meta.fuentes], ['Documento', meta.documento]].forEach(function(f){
    if (f[1]) h += '<dt>' + esc(f[0]) + '</dt><dd>' + esc(f[1]) + '</dd>';
  });
  h += '</dl>';

  if (por.descripcion && por.descripcion.length){
    h += '<div class="zona" data-edit="port-desc" style="margin-top:24px"><div class="prosa">' +
         por.descripcion.map(function(t){ return '<p>' + esc(t) + '</p>'; }).join('') + '</div></div>';
  }

  h += '<div class="cifras">' +
       '<div class="cifra"><b>' + meta.total_modulos + '</b><span>módulos</span></div>' +
       '<div class="cifra"><b>' + meta.total_puntos + '</b><span>puntos auditados</span></div>' +
       '<div class="cifra"><b>' + CUENTA_TOTAL['CRÍTICA'] + '</b><span>críticos</span></div>' +
       '<div class="cifra"><b>' + CUENTA_TOTAL['ALTA'] + '</b><span>prioridad alta</span></div>' +
       '<div class="cifra"><b>' + meta.total_tablas + '</b><span>tablas de datos</span></div>' +
       '<div class="cifra"><b>' + meta.total_capturas + '</b><span>capturas</span></div>' +
       '<div class="cifra"><b>' + meta.total_acciones + '</b><span>acciones a 90 días</span></div>' +
       '</div>';
  h += '</section>';

  h += '<section class="seccion" id="resumen">';
  h += '<div class="seccion-cab"><div class="eyebrow">Resumen ejecutivo</div>' +
       '<h2>Resumen ejecutivo consolidado</h2>';
  if (DATA.resumen.intro)
    h += '<div class="sub zona" data-edit="res-intro"><p>' + esc(DATA.resumen.intro.t) + '</p></div>';
  h += '</div>';

  h += '<div class="hallazgos">';
  DATA.resumen.hallazgos.forEach(function(hh, i){
    h += '<div class="hallazgo"><div class="num">' + (i+1) + '</div>' +
         '<div class="zona" data-edit="res-h' + i + '">' +
         '<h4>' + esc(hh[0]) + '</h4>' +
         (hh[1] ? '<p>' + esc(hh[1].t) + '</p>' : '') + '</div></div>';
  });
  h += '</div>';

  h += '<h3 style="margin:34px 0 4px;font-size:15px">Calificaciones e indicadores clave</h3>';
  h += tablaHTML({ headers: DATA.resumen.calificaciones_headers, rows: DATA.resumen.calificaciones });

  h += graficoSuelto('g1');
  h += graficoSuelto('g9');
  h += '</section>';

  /* ---------- cómo leer ---------- */
  h += '<section class="seccion" id="como-leer">';
  h += '<div class="seccion-cab"><div class="eyebrow">Guía de lectura</div>' +
       '<h2>Cómo leer este informe</h2></div>';
  DATA.como_leer.forEach(function(sec, i){
    h += '<div class="cat"><h3>' + esc(sec[0]) + '</h3>' +
         '<div class="zona" data-edit="leer-' + i + '">' + prosa(sec[1]) + '</div></div>';
  });
  h += '</section>';

  /* ---------- módulos ---------- */
  h += '<section class="seccion" id="modulos">';
  h += '<div class="seccion-cab"><div class="eyebrow">Cuerpo del informe</div>' +
       '<h2>Los ' + meta.total_modulos + ' módulos, punto por punto</h2>';
  if (DATA.intros && DATA.intros.cuerpo) h += '<div class="sub">' + esc(DATA.intros.cuerpo.t) + '</div>';
  h += '</div>';

  h += '<div class="tabla-caja"><table class="t-modulos"><thead><tr>' +
       '<th>ID</th><th>Módulo</th><th class="n">Puntos</th><th class="n">Críticos</th>' +
       '<th class="n">Alta</th><th>Alcance del análisis</th></tr></thead><tbody>';
  DATA.modulos.forEach(function(m){
    const c = CUENTA[m.id];
    h += '<tr data-ir="' + m.id.toLowerCase() + '" tabindex="0">' +
      '<td>' + esc(m.id) + '</td><td>' + esc(m.titulo) + '</td>' +
      '<td class="n">' + m.puntos.length + '</td>' +
      '<td class="n"><span class="pill ' + (c['CRÍTICA'] ? 'c' : 'cero') + '">' + c['CRÍTICA'] + '</span></td>' +
      '<td class="n"><span class="pill ' + (c['ALTA'] ? 'a' : 'cero') + '">' + c['ALTA'] + '</span></td>' +
      '<td class="alc">' + esc(m.alcance || '') + '</td></tr>';
  });
  const tot = DATA.modulos.reduce(function(a,m){ return a + m.puntos.length; }, 0);
  h += '<tr class="total"><td></td><td>TOTAL — ' + meta.total_modulos + ' módulos de análisis</td>' +
       '<td class="n">' + tot + '</td>' +
       '<td class="n">' + CUENTA_TOTAL['CRÍTICA'] + '</td>' +
       '<td class="n">' + CUENTA_TOTAL['ALTA'] + '</td><td></td></tr>';
  h += '</tbody></table></div>';

  /* Los filtros viven dentro de la sección de módulos y son sticky: aparecen
     al entrar en ella y se van al salir, sin que ningún observador tenga que
     decidirlo. Un control que aparece y desaparece por lógica en JS acaba
     desapareciendo justo cuando se está usando. */
  h += '<div class="filtros" id="filtros" role="group" aria-label="Filtros"></div>';
  h += '<div id="lista-modulos">';
  DATA.modulos.forEach(function(m, i){ h += moduloHTML(m, i, DATA.modulos); });
  h += '</div><div class="sin-resultados" id="sin-resultados" hidden>' +
       'Ningún punto coincide con la búsqueda y los filtros activos.</div>';
  h += '</section>';

  /* ---------- plan ---------- */
  h += '<section class="seccion" id="plan">';
  h += '<div class="seccion-cab"><div class="eyebrow">Hoja de ruta</div>' +
       '<h2>Plan de acción consolidado — 90 días</h2>';
  if (DATA.plan_intro) h += '<div class="sub">' + esc(DATA.plan_intro.t) + '</div>';
  h += '</div>';
  h += '<div class="progreso-global"><div class="n"><b id="pg-n">0</b> de ' + meta.total_acciones + ' acciones</div>' +
       '<div class="barra-p"><i id="pg-b" style="width:0%"></i></div>' +
       '<div class="n" id="pg-p">0%</div></div>';

  DATA.plan.forEach(function(bl, bi){
    h += '<div class="bloque" id="bloque-' + bi + '">';
    h += '<div class="bloque-cab"><h3>' + esc(bl[0]) + '</h3>';
    if (bl[1]) h += '<div class="desc zona" data-edit="plan-b' + bi + '"><p>' + esc(bl[1].t) + '</p></div>';
    h += '<div class="mini"><div class="barra-p"><i data-bp="' + bi + '" style="width:0%"></i></div>' +
         '<div class="n" data-bn="' + bi + '">0 / ' + bl[2].length + '</div></div>';
    h += '</div>';
    bl[2].forEach(function(ac, ai){
      const id = 'tarea-' + bi + '-' + ai;
      h += '<div class="tarea" data-bloque="' + bi + '">' +
        '<input type="checkbox" id="' + id + '" data-tarea="' + bi + '.' + ai + '">' +
        '<div class="cont"><div class="fila">' +
        '<span class="num">' + String(ac[3]).padStart(2,'0') + '</span>' +
        '<label for="' + id + '">' + esc(ac[0]) + '</label>' +
        '<span class="mods">' + esc(ac[1]) + '</span></div>' +
        '<div class="det zona" data-edit="plan-a' + String(ac[3]).padStart(2,'0') + '"><p>' +
        (ac[2] ? esc(ac[2].t) : '') + '</p></div>' +
        '</div></div>';
    });
    h += '</div>';
  });
  h += '</section>';

  /* ---------- fase de profundización ---------- */
  h += '<section class="seccion" id="profundizacion">';
  h += '<div class="seccion-cab"><div class="eyebrow">Qué falta</div>' +
       '<h2>Fase de profundización</h2>';
  if (DATA.vacios.intro)
    h += '<div class="sub zona" data-edit="prof-int"><p>' + esc(DATA.vacios.intro.t) + '</p></div>';
  h += '</div>';
  DATA.vacios.categorias.forEach(function(cat, ci){
    h += '<div class="cat"><h3>' + esc(cat[0]) + '</h3>' +
         '<div class="zona" data-edit="prof-' + ci + '"><ul>';
    let esf = '';
    cat[1].forEach(function(l){
      if (/^ESFUERZO/i.test(l.t)) { esf = l; return; }
      h += '<li>' + (l.lead && l.t.indexOf(l.lead) === 0
        ? '<b class="lead">' + esc(l.lead) + '</b>' + esc(l.t.slice(l.lead.length))
        : esc(l.t)) + '</li>';
    });
    h += '</ul>';
    if (esf) h += '<div class="esfuerzo">' + esc(esf.t) + '</div>';
    h += '</div></div>';
  });
  h += '</section>';

  /* ---------- fuentes y metodología ---------- */
  h += '<section class="seccion" id="fuentes">';
  h += '<div class="seccion-cab"><div class="eyebrow">Anexos</div>' +
       '<h2>Fuentes y metodología</h2></div>';
  h += '<h3 style="font-size:15px;margin-bottom:4px">Componentes del análisis</h3>';
  h += tablaHTML({ headers: DATA.fuentes.documentos_headers, rows: DATA.fuentes.documentos });
  DATA.fuentes.grupos.forEach(function(g, gi){
    if (!g[1].length) return;
    h += '<h3 style="font-size:15px;margin:26px 0 8px">' + esc(g[0]) + '</h3>' +
         '<div class="zona" data-edit="fuen-' + gi + '"><ul class="lista-fuentes">';
    g[1].forEach(function(l){ h += '<li>' + esc(l.t) + '</li>'; });
    h += '</ul></div>';
  });
  h += '<h3 style="font-size:15px;margin:30px 0 8px">Nota metodológica y trazabilidad</h3>';
  h += '<div class="zona" data-edit="nota-0">' + prosa(DATA.nota) + '</div>';
  h += '</section>';

  $('#contenido').innerHTML = h;
  ajustarEtiquetas();
}

const CUENTA_TOTAL = (function(){
  const t = {'CRÍTICA':0,'ALTA':0,'MEDIA':0,'BAJA':0,'—':0};
  DATA.modulos.forEach(function(m){
    ORDEN_PRIORIDAD.forEach(function(p){ t[p] += CUENTA[m.id][p]; });
  });
  return t;
})();

/* ---------------- barra lateral ---------------- */
function renderSidebar(){
  let h = '<div class="zona-controles" id="zona-controles"></div>';
  h += '<div class="nav-grupo"><div class="nav-titulo">Informe</div>';
  [['portada','Portada y resumen ejecutivo'],
   ['como-leer','Cómo leer este informe'],
   ['modulos','Los 21 módulos'],
   ['plan','Hoja de ruta a 90 días'],
   ['profundizacion','Fase de profundización'],
   ['fuentes','Fuentes y metodología']].forEach(function(s){
    h += '<a class="nav-a" href="#' + s[0] + '"><span class="tx">' + esc(s[1]) + '</span></a>';
  });
  h += '</div>';

  h += '<div class="nav-grupo"><div class="nav-titulo">Módulos</div>';
  DATA.modulos.forEach(function(m){
    const c = CUENTA[m.id]['CRÍTICA'];
    h += '<a class="nav-a" href="#' + m.id.toLowerCase() + '" title="' + esc(m.id + ' — ' + m.titulo) + '">' +
      '<span class="id">' + esc(m.id) + '</span>' +
      '<span class="tx">' + esc(m.titulo) + '</span>' +
      (c ? '<span class="crit" title="' + c + ' puntos críticos">' + c + '</span>' : '') +
      '</a>';
  });
  h += '</div>';
  $('#sidebar').innerHTML = h;
}

/* ---------------- filtros ---------------- */
function renderFiltros(){
  const estados = {};
  DATA.modulos.forEach(function(m){
    m.puntos.forEach(function(p){ estados[p.estado] = (estados[p.estado] || 0) + 1; });
  });

  let h = '<div class="filtro-fila"><span class="filtro-et">Prioridad</span>';
  ORDEN_PRIORIDAD.forEach(function(p){
    if (!CUENTA_TOTAL[p]) return;
    h += '<button class="chip" data-f="prioridad" data-v="' + esc(p) + '" aria-pressed="false">' +
      esc(p === '—' ? 'informativo' : p) + '<span class="c">' + CUENTA_TOTAL[p] + '</span></button>';
  });
  h += '</div><div class="filtro-fila"><span class="filtro-et">Evidencia</span>';
  Object.keys(estados).sort(function(a,b){ return estados[b] - estados[a]; }).forEach(function(e){
    h += '<button class="chip" data-f="estado" data-v="' + esc(e) + '" aria-pressed="false">' +
      esc(e) + '<span class="c">' + estados[e] + '</span></button>';
  });
  h += '<button class="chip limpiar" id="limpiar-todo">Limpiar todo</button></div>';
  h += '<button id="cerrar-filtros" class="solo-movil">Ver los puntos</button>';
  $('#filtros').innerHTML = h;
}

function esMovil(){ return matchMedia('(max-width: 860px)').matches; }

/* ---------------- búsqueda y filtrado ---------------- */
const estado = { q:'', prioridad:new Set(), estado:new Set() };
/* Filtrar oculta puntos y encoge el documento, así que el navegador recorta la
   posición de lectura y quitar la búsqueda te lanzaría al principio del
   informe. Se ancla a un elemento concreto —no a una coordenada, que no
   sobrevive al cambio de altura— y se devuelve al limpiar. */
let filtrandoAntes = false, anclaGuardada = null;

function anclaVisible(){
  const els = $$('.modulo, .punto');
  for (let i = 0; i < els.length; i++){
    const el = els[i];
    if (el.hidden || !el.id) continue;
    const r = el.getBoundingClientRect();
    if (r.bottom > 90) return { id: el.id, off: r.top };
  }
  return null;
}
function devuelveAncla(a){
  if (!a) return;
  const el = document.getElementById(a.id);
  if (!el || el.hidden) return;
  scrollBy(0, el.getBoundingClientRect().top - a.off);
}
let tarjetas = null;
const resaltadas = new Set();

function indexarTarjetas(){
  tarjetas = {};
  $$('.punto').forEach(function(el){ tarjetas[el.id] = el; });
}

function resaltar(el, q){
  if (!q) return;
  const nq = norm(q);
  const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, {
    acceptNode: function(n){
      if (!n.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
      const p = n.parentNode.nodeName;
      if (p === 'SCRIPT' || p === 'STYLE' || p === 'MARK') return NodeFilter.FILTER_REJECT;
      return NodeFilter.FILTER_ACCEPT;
    }
  });
  const objetivos = [];
  let n;
  while ((n = walker.nextNode())) {
    if (norm(n.nodeValue).indexOf(nq) !== -1) objetivos.push(n);
  }
  objetivos.forEach(function(nodo){
    const texto = nodo.nodeValue;
    const base = norm(texto);
    const frag = document.createDocumentFragment();
    let i = 0, k;
    while ((k = base.indexOf(nq, i)) !== -1){
      if (k > i) frag.appendChild(document.createTextNode(texto.slice(i, k)));
      const mk = document.createElement('mark');
      mk.textContent = texto.slice(k, k + nq.length);
      frag.appendChild(mk);
      i = k + nq.length;
    }
    if (i < texto.length) frag.appendChild(document.createTextNode(texto.slice(i)));
    nodo.parentNode.replaceChild(frag, nodo);
  });
}

function quitarResaltado(el){
  const marcas = el.querySelectorAll('mark');
  if (!marcas.length) return;
  for (let i = 0; i < marcas.length; i++){
    const m = marcas[i];
    m.parentNode.replaceChild(document.createTextNode(m.textContent), m);
  }
  el.normalize();
}

function aplicar(){
  const q = norm(estado.q.trim());
  const fp = estado.prioridad, fe = estado.estado;
  const filtrando = !!(q || fp.size || fe.size);

  /* el ancla se toma antes de ocultar nada: después el navegador ya ha
     recortado la posición de lectura y no hay qué recuperar */
  if (filtrando && !filtrandoAntes) anclaGuardada = anclaVisible();

  let nP = 0;
  const modulosVivos = new Set();

  PUNTOS.forEach(function(p){
    let ok = true;
    if (fp.size && !fp.has(p.prioridad)) ok = false;
    if (ok && fe.size && !fe.has(p.estado)) ok = false;
    if (ok && q && p.texto.indexOf(q) === -1) ok = false;

    const el = tarjetas[p.id];
    if (!el) return;

    /* el resaltado se hace y se deshace sobre nodos de texto: nunca se
       reconstruye el HTML, para no volver a decodificar las capturas */
    if (resaltadas.has(p.id)){ quitarResaltado(el); resaltadas.delete(p.id); }

    el.hidden = !ok;
    if (ok){
      nP++;
      modulosVivos.add(p.modulo);
      if (q){ resaltar(el, estado.q.trim()); resaltadas.add(p.id); }
    }
  });

  $$('.modulo').forEach(function(m){
    m.hidden = !modulosVivos.has(m.id.toUpperCase());
  });
  $$('.t-modulos tbody tr[data-ir]').forEach(function(tr){
    tr.style.opacity = modulosVivos.has(tr.dataset.ir.toUpperCase()) ? '' : '.34';
  });

  if (!filtrando && filtrandoAntes && anclaGuardada){
    const a = anclaGuardada;
    anclaGuardada = null;
    /* dos cuadros: el primero deja que el navegador rehaga el alto */
    requestAnimationFrame(function(){ requestAnimationFrame(function(){ devuelveAncla(a); }); });
  }
  filtrandoAntes = filtrando;

  $('#sin-resultados').hidden = nP !== 0 || !filtrando;
  $('#contador').innerHTML = '<b>' + nP + '</b> de ' + DATA.meta.total_puntos + ' puntos' +
    (filtrando ? ' · ' + modulosVivos.size + ' de ' + DATA.meta.total_modulos + ' módulos' : '');
  $('#limpiar-todo').hidden = !filtrando;

  /* cuántos filtros hay puestos, para el botón del móvil */
  const nf = fp.size + fe.size;
  const marca = $('#n-filtros');
  if (marca){ marca.hidden = !nf; marca.textContent = nf; }
}

/* ---------------- hoja de ruta ---------------- */
const CLAVE = 'fb360.plan.v1';
function initPlan(){
  const guardado = Store.get(CLAVE, {}) || {};
  $$('input[data-tarea]').forEach(function(cb){
    cb.checked = !!guardado[cb.dataset.tarea];
    cb.closest('.tarea').classList.toggle('hecha', cb.checked);
    cb.addEventListener('change', function(){
      const g = Store.get(CLAVE, {}) || {};
      if (cb.checked) g[cb.dataset.tarea] = 1; else delete g[cb.dataset.tarea];
      Store.set(CLAVE, g);
      cb.closest('.tarea').classList.toggle('hecha', cb.checked);
      progreso();
    });
  });
  progreso();
}
function progreso(){
  const todas = $$('input[data-tarea]');
  const hechas = todas.filter(function(c){ return c.checked; }).length;
  const pct = todas.length ? Math.round(hechas / todas.length * 100) : 0;
  $('#pg-n').textContent = hechas;
  $('#pg-b').style.width = pct + '%';
  $('#pg-p').textContent = pct + '%';

  DATA.plan.forEach(function(bl, bi){
    const cbs = $$('.tarea[data-bloque="' + bi + '"] input');
    const n = cbs.filter(function(c){ return c.checked; }).length;
    const b = $('[data-bp="' + bi + '"]');
    if (b) b.style.width = (cbs.length ? n / cbs.length * 100 : 0) + '%';
    const t = $('[data-bn="' + bi + '"]');
    if (t) t.textContent = n + ' / ' + cbs.length;
  });
}

/* ---------------- tooltip ---------------- */
function initTooltip(){
  const tip = $('#tip');
  let visible = false;
  document.addEventListener('mouseover', function(e){
    const el = e.target.closest ? e.target.closest('[data-tip-t]') : null;
    if (!el){ if (visible){ tip.style.opacity = 0; visible = false; } return; }
    let h = '<b>' + esc(el.dataset.tipT) + '</b>';
    if (el.dataset.tipV) h += esc(el.dataset.tipV);
    if (el.dataset.tipD) h += '<i>' + esc(el.dataset.tipD) + '</i>';
    tip.innerHTML = h;
    tip.style.opacity = 1;
    visible = true;
  });
  document.addEventListener('mousemove', function(e){
    if (!visible) return;
    const r = tip.getBoundingClientRect();
    let x = e.clientX + 14, y = e.clientY + 16;
    if (x + r.width > innerWidth - 8) x = e.clientX - r.width - 14;
    if (y + r.height > innerHeight - 8) y = e.clientY - r.height - 12;
    tip.style.left = x + 'px';
    tip.style.top = y + 'px';
  });
  document.addEventListener('mouseout', function(e){
    if (!e.relatedTarget || !e.relatedTarget.closest || !e.relatedTarget.closest('[data-tip-t]')){
      tip.style.opacity = 0; visible = false;
    }
  });
}

/* ---------------- lightbox ---------------- */
function initLightbox(){
  const lb = $('#lightbox'), img = $('#lb-img'), cap = $('#lb-cap');
  let previo = null;
  document.addEventListener('click', function(e){
    const t = e.target;
    if (t.tagName === 'IMG' && t.dataset.fig){
      previo = t;
      img.src = t.src; img.alt = t.alt;
      cap.textContent = t.alt;
      lb.classList.add('abierto');
      $('#lb-cerrar').focus();
    }
  });
  function cerrar(){
    lb.classList.remove('abierto');
    img.src = '';
    if (previo) previo.focus();
  }
  lb.addEventListener('click', function(e){ if (e.target === lb || e.target.id === 'lb-cerrar') cerrar(); });
  document.addEventListener('keydown', function(e){
    if (e.key === 'Escape' && lb.classList.contains('abierto')) cerrar();
  });
}

/* ---------------- enlaces profundos ---------------- */
function initHash(){
  let ultimo = location.hash;
  const obs = new IntersectionObserver(function(ents){
    ents.forEach(function(en){
      if (!en.isIntersecting) return;
      const h = '#' + en.target.id;
      if (h !== ultimo){
        ultimo = h;
        history.replaceState(null, '', h);
        marcarNav(en.target.id);
      }
    });
  }, { rootMargin: '-70px 0px -75% 0px', threshold: 0 });

  $$('.punto, .modulo, .seccion, .portada').forEach(function(el){ if (el.id) obs.observe(el); });

  if (location.hash){
    const el = document.getElementById(location.hash.slice(1));
    if (el) setTimeout(function(){ el.scrollIntoView(); }, 40);
  }
}
function marcarNav(id){
  const base = id.split('-p')[0];
  $$('.nav-a').forEach(function(a){
    a.classList.toggle('activo', a.getAttribute('href') === '#' + base || a.getAttribute('href') === '#' + id);
  });
}

/* ---------------- tema ---------------- */
function initTema(){
  const guardado = Store.get('fb360.tema', null);
  if (guardado) document.documentElement.setAttribute('data-theme', guardado);
  const btn = $('#btn-tema');
  function pinta(){
    const t = document.documentElement.getAttribute('data-theme');
    const oscuro = t === 'dark' || (!t && matchMedia('(prefers-color-scheme: dark)').matches);
    btn.setAttribute('aria-pressed', String(oscuro));
    btn.querySelector('.et').textContent = oscuro ? 'Claro' : 'Oscuro';
  }
  btn.addEventListener('click', function(){
    const t = document.documentElement.getAttribute('data-theme');
    const oscuro = t === 'dark' || (!t && matchMedia('(prefers-color-scheme: dark)').matches);
    const nuevo = oscuro ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', nuevo);
    Store.set('fb360.tema', nuevo);
    pinta();
  });
  pinta();
}


/* =========================================================================
   EDICIÓN
   -------------------------------------------------------------------------
   El informe original nunca se toca: sigue siendo el JSON incrustado en esta
   página. Lo que se escribe se guarda aparte, en una capa por encima, y cada
   región editada puede devolverse a su texto original.

   Quién puede escribir lo decide el enlace: el de edición lleva un token
   (#k=...) que la página guarda y manda con cada escritura. Sin token, la
   página es de solo lectura y ni siquiera aparece el botón de editar. Las
   tablas no admiten escritura directa: todo pasa por una función de servidor
   que comprueba el token antes de tocar nada.
   ========================================================================= */

const SB = SERVIDOR;   // lo inyecta build.py
const CLAVE_TOKEN = 'fb360.token';

const PALETA_TINTA = [
  ['var(--texto)',  'Normal',  ''],
  ['#d03b3b',       'Rojo',    '#d03b3b'],
  ['#eb6834',       'Naranja', '#eb6834'],
  ['#2a78d6',       'Azul',    '#2a78d6'],
  ['#1d6f42',       'Verde',   '#1d6f42'],
];
const PALETA_FONDO = ['#fff2a8', '#ffd6c2', '#cfe3fb', '#c9f0dd'];

let TOKEN = null, PUEDE_EDITAR = false, EDITANDO = false;
let PINTA_COMPACTO = null, COMPACTO_PREVIO = false;
let MIDE_PANEL = null;

/* Qué está pasando de verdad. Si algo falla, tiene que verse en pantalla:
   un fallo silencioso obliga a adivinar desde fuera. */
const DIAG = {
  servidor: null, lectura: '—', escritura: '—', token: 'no',
  ediciones: 0, error: '', version: '',
};

function pintaDiag(){
  const chip = document.getElementById('diag');
  if (!chip) return;
  const bien = DIAG.lectura === 'sí';
  chip.className = bien ? 'ok' : 'mal';
  chip.textContent = !DIAG.servidor ? 'Sin servidor'
    : !bien ? 'Sin conexión'
    : (PUEDE_EDITAR ? 'Editor' : 'Solo lectura');
  const panel = document.getElementById('diag-panel');
  if (!panel) return;
  const fila = function(k, v, clase){
    return '<dt>' + k + '</dt><dd' + (clase ? ' class="' + clase + '"' : '') + '>' + esc(v) + '</dd>';
  };
  panel.innerHTML = '<h4>Estado de la conexión</h4><dl>' +
    fila('Servidor', DIAG.servidor || 'no configurado', DIAG.servidor ? 'si' : 'no') +
    fila('Leer cambios', DIAG.lectura, DIAG.lectura === 'sí' ? 'si' : 'no') +
    fila('Cambios cargados', String(DIAG.ediciones)) +
    fila('Enlace de edición', DIAG.token) +
    fila('Permiso de escritura', DIAG.escritura, DIAG.escritura === 'sí' ? 'si' : (DIAG.escritura === '—' ? '' : 'no')) +
    fila('Bloques editables', String($$('.zona').length)) +
    fila('Versión', DIAG.version || '—') +
    (DIAG.error ? fila('Último error', DIAG.error, 'no') : '') +
    '</dl><div class="pie">Si algo aquí sale en rojo, manda una captura de este panel.</div>';
}

function montaDiag(){
  const grupo = $('.acciones');
  if (!grupo || document.getElementById('diag')) return;
  const chip = document.createElement('button');
  chip.id = 'diag';
  chip.type = 'button';
  chip.title = 'Estado de la conexión con el servidor de cambios';
  /* dentro de .acciones para que viaje con ellos: en el móvil ese grupo se
     muda al índice, y en la barra de arriba no cabe sin comerse el buscador */
  grupo.insertBefore(chip, grupo.firstChild);
  const panel = document.createElement('div');
  panel.id = 'diag-panel';
  document.body.appendChild(panel);
  chip.addEventListener('click', function(){ panel.classList.toggle('abierto'); pintaDiag(); });
  document.addEventListener('click', function(e){
    if (!e.target.closest('#diag') && !e.target.closest('#diag-panel')) panel.classList.remove('abierto');
  });
  pintaDiag();
}
const SUCIAS = new Set();
let guardando = false, pendiente = null, ultimoGuardado = null;

/* El texto tal y como salió del informe. Se guarda aparte, en memoria: es lo
   que devuelve ↺ y lo que decide si un bloque sigue contando como editado.
   Fuera del DOM para no llevar dos copias de todo el informe en la página. */
const ORIGINAL = new Map();
function guardaOriginal(zona){
  const k = zona.dataset.edit;
  if (!ORIGINAL.has(k)) ORIGINAL.set(k, zona.innerHTML);
  return ORIGINAL.get(k);
}
function textoOriginal(zona){ return ORIGINAL.get(zona.dataset.edit); }

/* ---------- limpieza del HTML que se guarda y se muestra ----------
   Lo escribe gente con el enlace, se guarda y se vuelve a pintar para todos:
   se filtra en ambos sentidos para que nada ejecutable sobreviva. */
const ETIQUETAS_OK = new Set(['P','BR','B','STRONG','I','EM','U','S','STRIKE','SPAN',
  'UL','OL','LI','IMG','MARK','DIV','H4','BLOCKQUOTE','A']);
const ESTILOS_OK = ['color', 'background-color', 'font-weight', 'font-style',
  'text-align', 'text-decoration', 'text-decoration-line', 'margin-left'];
const ENLACE_OK = /^https?:\/\//i;

function esImagenNuestra(u){
  return typeof u === 'string' && SB && u.indexOf(SB.deposito) === 0;
}

function limpiaHTML(html){
  const caja = document.createElement('div');
  caja.innerHTML = String(html || '');
  const fuera = [];
  const w = document.createTreeWalker(caja, NodeFilter.SHOW_ELEMENT);
  let n;
  while ((n = w.nextNode())){
    if (!ETIQUETAS_OK.has(n.tagName)){ fuera.push(n); continue; }
    for (let i = n.attributes.length - 1; i >= 0; i--){
      const a = n.attributes[i].name;
      const v = n.attributes[i].value;
      const conservar =
        (a === 'style') ||
        (a === 'class' && /^(lead|subida|prosa)$/.test(v)) ||
        (n.tagName === 'IMG' && (a === 'alt' || a === 'width' || a === 'height' || a === 'loading')) ||
        (n.tagName === 'IMG' && a === 'src' && esImagenNuestra(v)) ||
        (n.tagName === 'A' && a === 'href' && ENLACE_OK.test(v)) ||
        (n.tagName === 'A' && (a === 'target' || a === 'rel'));
      if (!conservar) n.removeAttribute(a);
    }
    if (n.tagName === 'IMG' && !esImagenNuestra(n.getAttribute('src'))){ fuera.push(n); continue; }
    /* un enlace sin destino válido pierde la etiqueta, nunca el texto */
    if (n.tagName === 'A'){
      if (!n.getAttribute('href')){ fuera.push(n); continue; }
      n.setAttribute('target', '_blank');
      n.setAttribute('rel', 'noopener noreferrer');
    }
    if (n.hasAttribute('style')){
      const limpio = n.style.cssText.split(';').map(function(d){ return d.trim(); })
        .filter(function(d){ return d && ESTILOS_OK.indexOf(d.split(':')[0].trim().toLowerCase()) !== -1; })
        .join('; ');
      if (limpio) n.setAttribute('style', limpio); else n.removeAttribute('style');
    }
  }
  /* una etiqueta no permitida se sustituye por su contenido, no se borra:
     así el filtro nunca hace perder texto */
  fuera.forEach(function(el){
    if (!el.parentNode) return;
    if (el.tagName !== 'IMG'){
      while (el.firstChild) el.parentNode.insertBefore(el.firstChild, el);
    }
    el.remove();
  });
  return caja.innerHTML;
}

/* ---------- hablar con el servidor ---------- */
async function pide(ruta){
  const r = await fetch(SB.url + '/rest/v1/' + ruta, {
    headers: { apikey: SB.anon, Authorization: 'Bearer ' + SB.anon },
  });
  if (!r.ok) throw new Error('lectura ' + r.status);
  return r.json();
}

async function manda(cuerpo){
  const r = await fetch(SB.url + '/functions/v1/fb360', {
    method: 'POST',
    headers: { apikey: SB.anon, Authorization: 'Bearer ' + SB.anon, 'content-type': 'application/json' },
    body: JSON.stringify(Object.assign({ token: TOKEN }, cuerpo)),
  });
  const d = await r.json().catch(function(){ return {}; });
  if (!r.ok) { const e = new Error(d.error || ('error ' + r.status)); e.estado = r.status; throw e; }
  return d;
}

/* ---------- imágenes ----------
   Se reducen aquí, en el navegador: nunca se sube el original de 4 MB. */
const LIMITE_IMG = 420000;

async function comprimeImagen(fichero){
  let bitmap;
  try { bitmap = await createImageBitmap(fichero); }
  catch (e) { return null; }
  let escala = Math.min(1, 1600 / Math.max(bitmap.width, bitmap.height));
  for (let paso = 0; paso < 7; paso++){
    const w = Math.max(1, Math.round(bitmap.width * escala));
    const h = Math.max(1, Math.round(bitmap.height * escala));
    const c = document.createElement('canvas');
    c.width = w; c.height = h;
    const ctx = c.getContext('2d');
    ctx.fillStyle = '#ffffff'; ctx.fillRect(0, 0, w, h);
    ctx.drawImage(bitmap, 0, 0, w, h);
    const calidades = [0.88, 0.78, 0.66, 0.5];
    for (let i = 0; i < calidades.length; i++){
      const url = c.toDataURL('image/jpeg', calidades[i]);
      if (url.length <= LIMITE_IMG) return { datos: url, w: w, h: h };
    }
    escala *= 0.74;
  }
  return null;
}

async function insertaFichero(fichero, zona){
  if (!fichero || !/^image\//.test(fichero.type)) return;
  if (!zona) { avisa('Pon el cursor donde quieras la imagen.'); return; }
  avisa('Subiendo la imagen…');
  const img = await comprimeImagen(fichero);
  if (!img){ avisa('No se pudo leer esa imagen.'); return; }
  let res;
  try { res = await manda({ accion: 'imagen', datos: img.datos, ancho: img.w, alto: img.h }); }
  catch (e){ avisa('No se pudo subir: ' + e.message); return; }
  const el = document.createElement('img');
  el.className = 'subida';
  el.src = res.url;
  el.loading = 'lazy';
  el.alt = 'Imagen añadida por el equipo';
  confirmaYa();
  insertaEnCursor(el, zona);
  confirma(zona);
  marcaSucia(zona);
  avisa('Imagen añadida');
}

function insertaEnCursor(nodo, zona){
  const sel = getSelection();
  if (sel && sel.rangeCount && zona.contains(sel.anchorNode)){
    const r = sel.getRangeAt(0);
    r.deleteContents();
    r.insertNode(nodo);
    r.setStartAfter(nodo); r.collapse(true);
    sel.removeAllRanges(); sel.addRange(r);
  } else {
    zona.appendChild(nodo);
  }
  if (!nodo.nextSibling) zona.appendChild(document.createElement('p'));
}

/* ---------- estado y guardado ---------- */
function marcaSucia(zona){
  SUCIAS.add(zona.dataset.edit);
  zona.classList.add('editada');
  zona.classList.remove('vacia');
  const notas = zona.closest('.notas');
  if (notas) notas.classList.add('con-contenido');
  pintaEstado();
  clearTimeout(pendiente);
  pendiente = setTimeout(guardar, 1600);
}

async function guardar(){
  if (!PUEDE_EDITAR || guardando || !SUCIAS.size) { pintaEstado(); return; }
  guardando = true; pintaEstado();
  let fallos = 0, ultimo = '';
  for (const clave of Array.from(SUCIAS)){
    const zona = document.querySelector('.zona[data-edit="' + clave + '"]');
    if (!zona) { SUCIAS.delete(clave); continue; }
    const html = limpiaHTML(zona.innerHTML);
    /* deshacer hasta el principio deja el bloque como estaba: entonces no se
       guarda una copia del original, se quita la fila */
    const orig = textoOriginal(zona);
    const vuelto = orig != null && html === limpiaHTML(orig);
    try {
      await manda(vuelto ? { accion: 'borrar', clave: clave }
                         : { accion: 'guardar', clave: clave, html: html });
      SUCIAS.delete(clave);
      zona.dataset.guardado = '1';
      if (vuelto) sincronizaZona(zona);
    } catch (e){ fallos++; ultimo = e.message; DIAG.error = e.message; pintaDiag(); }
  }
  guardando = false;
  if (!fallos) ultimoGuardado = new Date();
  pintaEstado(fallos ? ('No se guardaron ' + fallos + ': ' + ultimo) : '');
  if (fallos){ clearTimeout(pendiente); pendiente = setTimeout(guardar, 6000); }
}

function pintaEstado(extra){
  const el = document.getElementById('estado-edicion');
  if (!el) return;
  let t;
  if (guardando) t = 'Guardando…';
  else if (SUCIAS.size) t = '<span class="punto-rojo"></span> Sin guardar (' + SUCIAS.size + ')';
  else if (ultimoGuardado) t = '<b>Guardado</b> a las ' + ultimoGuardado.toLocaleTimeString('es-ES', {hour:'2-digit', minute:'2-digit'});
  else t = 'Todo al día';
  el.innerHTML = t + (extra ? ' · ' + esc(extra) : '');
}

function avisa(texto){
  const el = document.getElementById('aviso-lectura');
  if (!el) return;
  el.textContent = texto;
  el.classList.add('visible');
  clearTimeout(avisa._t);
  avisa._t = setTimeout(function(){ el.classList.remove('visible'); }, 3000);
}

/* ---------- pintar una edición sobre el informe ---------- */
function aplicaEdicion(clave, html){
  const zona = document.querySelector('.zona[data-edit="' + clave + '"]');
  if (!zona) return;
  if (document.activeElement === zona) return;      // se está escribiendo ahí
  if (SUCIAS.has(clave)) return;                    // hay cambios propios sin guardar
  guardaOriginal(zona);
  const limpio = limpiaHTML(html);
  if (zona.innerHTML === limpio) return;
  zona.innerHTML = limpio;
  PREVIO.set(clave, zona.innerHTML);
  zona.classList.add('editada');
  zona.classList.remove('vacia');
  const notas = zona.closest('.notas');
  if (notas) notas.classList.add('con-contenido');
  refrescaIndice(zona);
}

async function revierte(zona){
  const orig = textoOriginal(zona);
  if (orig == null || zona.innerHTML === orig){ avisa('Este bloque ya está como el original.'); return; }
  confirmaYa();
  zona.innerHTML = orig;
  sincronizaZona(zona);
  confirma(zona);                     // devolver el bloque también se deshace
  SUCIAS.delete(zona.dataset.edit);
  pintaEstado();
  if (PUEDE_EDITAR){
    try { await manda({ accion: 'borrar', clave: zona.dataset.edit }); avisa('Devuelto al original'); }
    catch (e){ avisa('No se pudo borrar en el servidor: ' + e.message); }
  }
}

/* el buscador tiene que encontrar también lo que se acaba de escribir */
function refrescaIndice(zona){
  const art = zona.closest('.punto');
  if (!art) return;
  const reg = PUNTOS.filter(function(x){ return x.id === art.id; })[0];
  if (!reg) return;
  const cuerpo = art.querySelector('.punto-cuerpo');
  reg.texto = norm((art.querySelector('h3') ? art.querySelector('h3').textContent : '') +
                   ' ' + (cuerpo ? cuerpo.textContent : ''));
}

/* ---------- deshacer y rehacer ----------
   El deshacer del navegador no sirve aquí: se pierde en cuanto la página
   reescribe un bloque por su cuenta —al llegar cambios de otra persona, al
   insertar una imagen, al devolver un bloque a su original— y no cruza de un
   bloque a otro. Así que la historia se lleva aparte, como en un procesador
   de texto: una sola línea de tiempo para todo el informe, con el bloque
   afectado, el antes, el después y dónde estaba el cursor. */
const LINEA = [];            // los cambios, en orden
let IDX = 0;                 // cuántos están aplicados
const PREVIO = new Map();    // clave -> HTML en el último punto confirmado
const SEL_BASE = new Map();  // clave -> dónde quedó el cursor en ese punto
const TOPE_HIST = 150;
let relojHist = null, zonaEscribiendo = null;

/* El cursor se guarda como número de caracteres, no como nodo: el nodo
   desaparece al reescribir el bloque, la posición en el texto no. */
function marcaSeleccion(zona){
  const sel = getSelection();
  if (!sel || !sel.rangeCount) return null;
  const r = sel.getRangeAt(0);
  if (!zona.contains(r.startContainer)) return null;
  const hasta = document.createRange();
  hasta.selectNodeContents(zona);
  hasta.setEnd(r.startContainer, r.startOffset);
  return { ini: hasta.toString().length, largo: r.toString().length };
}

function ponSeleccion(zona, marca){
  if (!marca) return;
  const w = document.createTreeWalker(zona, NodeFilter.SHOW_TEXT);
  const r = document.createRange();
  let n, visto = 0, puesto = false, cerrado = false;
  const fin = marca.ini + marca.largo;
  while ((n = w.nextNode())){
    const largo = n.nodeValue.length;
    if (!puesto && visto + largo >= marca.ini){
      r.setStart(n, Math.max(0, marca.ini - visto)); puesto = true;
    }
    if (puesto && visto + largo >= fin){
      r.setEnd(n, Math.max(0, Math.min(largo, fin - visto))); cerrado = true; break;
    }
    visto += largo;
  }
  if (!puesto){ r.selectNodeContents(zona); r.collapse(false); }
  else if (!cerrado){ r.setEnd(r.startContainer, r.startOffset); }
  try {
    const sel = getSelection();
    sel.removeAllRanges(); sel.addRange(r);
  } catch (e){}
}

/* El punto de partida de un bloque hay que apuntarlo ANTES de tocarlo: si se
   apunta al cerrar el paso, el primer cambio se compara consigo mismo y se
   pierde. De ahí que se llame al entrar en el bloque y antes de cada tecla. */
function baseDe(zona){
  const k = zona.dataset.edit;
  if (!PREVIO.has(k)) PREVIO.set(k, zona.innerHTML);
  return PREVIO.get(k);
}

/* Cierra el cambio que estuviera en curso y lo anota. Devuelve si hubo algo
   que anotar. Todo lo que toca un bloque pasa por aquí. */
function confirma(zona){
  if (!zona || !zona.dataset || !zona.dataset.edit) return false;
  const k = zona.dataset.edit;
  const antes = baseDe(zona);
  const ahora = zona.innerHTML;
  if (antes === ahora) return false;
  LINEA.length = IDX;                       // lo que se pudiera rehacer, se pierde
  LINEA.push({
    clave: k, antes: antes, despues: ahora,
    selA: SEL_BASE.get(k) || null, selD: marcaSeleccion(zona),
  });
  while (LINEA.length > TOPE_HIST) LINEA.shift();
  IDX = LINEA.length;
  PREVIO.set(k, ahora);
  SEL_BASE.set(k, LINEA[LINEA.length - 1].selD);
  pintaHistorial();
  return true;
}

/* Se escribe seguido: los golpes de tecla se juntan en un solo paso mientras
   no haya pausa. Cualquier otra cosa cierra el paso antes de actuar. */
function confirmaYa(){
  clearTimeout(relojHist);
  const z = zonaEscribiendo || zonaActiva();
  zonaEscribiendo = null;
  return confirma(z);
}

function anotaEscritura(zona){
  clearTimeout(relojHist);
  zonaEscribiendo = zona;
  relojHist = setTimeout(function(){ zonaEscribiendo = null; confirma(zona); }, 700);
}

function pintaHistorial(){
  $$('[data-hist="atras"]').forEach(function(b){ b.disabled = IDX <= 0; });
  $$('[data-hist="adelante"]').forEach(function(b){ b.disabled = IDX >= LINEA.length; });
}

/* clases y buscador al día después de reescribir un bloque desde fuera */
function sincronizaZona(zona){
  const k = zona.dataset.edit;
  const orig = textoOriginal(zona);
  const cambiado = orig == null || zona.innerHTML !== orig;
  zona.classList.toggle('editada', cambiado);
  if (k.slice(-2) === '-n') zona.classList.toggle('vacia', !zona.textContent.trim() && !zona.querySelector('img'));
  else zona.classList.remove('vacia');
  const notas = zona.closest('.notas');
  if (notas) notas.classList.toggle('con-contenido', !!notas.querySelector('.zona.editada'));
  refrescaIndice(zona);
}

function aplicaPaso(entrada, atras){
  const zona = document.querySelector('.zona[data-edit="' + entrada.clave + '"]');
  if (!zona) { avisa('Ese cambio era de un bloque que ya no está.'); return false; }
  const html  = atras ? entrada.antes : entrada.despues;
  const marca = atras ? entrada.selA  : entrada.selD;
  const punto = zona.closest('.punto');
  if (punto) punto.classList.add('abierto');       // no se deshace a ciegas
  zona.innerHTML = html;
  /* el navegador vuelve a escribir el HTML a su manera al asignarlo: el punto
     de partida se lee de vuelta del DOM, nunca de la cadena que se le dio, o
     el paso siguiente vería una diferencia que no existe */
  PREVIO.set(entrada.clave, zona.innerHTML);
  SEL_BASE.set(entrada.clave, marca);
  sincronizaZona(zona);
  SUCIAS.add(entrada.clave);
  pintaEstado();
  clearTimeout(pendiente);
  pendiente = setTimeout(guardar, 1200);
  if (punto && punto.hidden){
    avisa('Hecho, pero ese punto está oculto por el filtro.');
    return true;
  }
  try { zona.focus({ preventScroll: true }); } catch (e){ zona.focus(); }
  ponSeleccion(zona, marca);
  const caja = zona.getBoundingClientRect();
  if (caja.top < 90 || caja.bottom > innerHeight - 130){
    zona.scrollIntoView({ block: 'center', behavior: 'smooth' });
  }
  return true;
}

function deshacer(){
  confirmaYa();
  if (IDX <= 0){ avisa('No queda nada que deshacer.'); pintaHistorial(); return; }
  IDX--;
  if (!aplicaPaso(LINEA[IDX], true)) { /* el bloque ya no existe: se salta */ }
  pintaHistorial(); pintaBotones();
}

function rehacer(){
  confirmaYa();
  if (IDX >= LINEA.length){ avisa('No queda nada que rehacer.'); pintaHistorial(); return; }
  const e = LINEA[IDX];
  IDX++;
  aplicaPaso(e, false);
  pintaHistorial(); pintaBotones();
}

/* ---------- barra de herramientas ----------
   Un solo listado para los dos sitios donde aparece: la cinta de abajo, fija
   mientras se edita, y la burbuja sobre el texto seleccionado en pantalla
   ancha. El mismo manejador atiende a las dos. */
function svg(d){
  return '<svg viewBox="0 0 16 16" width="15" height="15" fill="none" ' +
    'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" ' +
    'stroke-linejoin="round" aria-hidden="true">' + d + '</svg>';
}
const ICO = {
  deshacer: svg('<path d="M6.5 3.4 3 6.5l3.5 3.1"/><path d="M3.4 6.5h6.1a3.5 3.5 0 0 1 0 7H6.6"/>'),
  rehacer:  svg('<path d="M9.5 3.4 13 6.5l-3.5 3.1"/><path d="M12.6 6.5H6.5a3.5 3.5 0 0 0 0 7h2.9"/>'),
  izq:      svg('<path d="M2.2 3.6h11.6M2.2 6.9h7.4M2.2 10.2h10.4M2.2 13.5h5.9"/>'),
  centro:   svg('<path d="M2.2 3.6h11.6M4.3 6.9h7.4M2.8 10.2h10.4M5 13.5h5.9"/>'),
  der:      svg('<path d="M2.2 3.6h11.6M6.4 6.9h7.4M3.4 10.2h10.4M7.9 13.5h5.9"/>'),
  menos:    svg('<path d="M2.2 3.4h11.6M6.6 6.8h7.2M6.6 10h7.2M2.2 13.4h11.6"/><path d="M4.6 6.9 2.3 8.4l2.3 1.5z" fill="currentColor" stroke="none"/>'),
  mas:      svg('<path d="M2.2 3.4h11.6M6.6 6.8h7.2M6.6 10h7.2M2.2 13.4h11.6"/><path d="M2.3 6.9l2.3 1.5-2.3 1.5z" fill="currentColor" stroke="none"/>'),
  enlace:   svg('<path d="M6.6 9.4a2.7 2.7 0 0 0 3.8 0l2.2-2.2a2.7 2.7 0 1 0-3.8-3.8l-.9.9"/><path d="M9.4 6.6a2.7 2.7 0 0 0-3.8 0L3.4 8.8a2.7 2.7 0 1 0 3.8 3.8l.9-.9"/>'),
  imagen:   svg('<path d="M2.2 5.4h2.5l1-1.7h4.6l1 1.7h2.5v8H2.2z"/><circle cx="8" cy="9.3" r="2.4"/>'),
  revertir: svg('<path d="M3.1 8a4.9 4.9 0 1 0 1.6-3.6"/><path d="M2.4 2.7v3.2h3.2"/>'),
  limpiar:  svg('<path d="M4 3.2h8M8 3.2v9.6"/><path d="M2.4 13.6l11.2-11.2" stroke-width="1.3"/>'),
};

const HERRAMIENTAS = [
  { hist: 'atras',     ico: ICO.deshacer, et: 'Deshacer', t: 'Deshacer el último cambio (Ctrl+Z)' },
  { hist: 'adelante',  ico: ICO.rehacer,  et: 'Rehacer',  t: 'Rehacer lo deshecho (Ctrl+Y)' },
  { sep: 1 },
  { cmd: 'bold',          html: '<b>B</b>', t: 'Negrita (Ctrl+B)', estado: 'bold', burbuja: 1 },
  { cmd: 'italic',        html: '<i>I</i>', t: 'Cursiva (Ctrl+I)', estado: 'italic', burbuja: 1 },
  { cmd: 'underline',     html: '<span style="text-decoration:underline">U</span>', t: 'Subrayado (Ctrl+U)', estado: 'underline', burbuja: 1 },
  { cmd: 'strikeThrough', html: '<span style="text-decoration:line-through">S</span>', t: 'Tachado', estado: 'strikeThrough', burbuja: 1 },
  { sep: 1, burbuja: 1 },
  { bloque: '<h4>',         et: 'Título', t: 'Convertir el párrafo en subtítulo' },
  { bloque: '<p>',          et: 'Normal', t: 'Devolver el párrafo a texto normal' },
  { bloque: '<blockquote>', glifo: '&#10077;', t: 'Convertir el párrafo en cita' },
  { sep: 1 },
  { cmd: 'insertUnorderedList', glifo: '&#8226;&#8212;', t: 'Lista de puntos', estado: 'insertUnorderedList' },
  { cmd: 'insertOrderedList',   glifo: '1&#8212;',       t: 'Lista numerada',  estado: 'insertOrderedList' },
  { cmd: 'outdent', css: 1, ico: ICO.menos, t: 'Menos sangría' },
  { cmd: 'indent',  css: 1, ico: ICO.mas,   t: 'Más sangría' },
  { sep: 1 },
  { cmd: 'justifyLeft',    css: 1, ico: ICO.izq,    t: 'Alinear a la izquierda', estado: 'justifyLeft' },
  { cmd: 'justifyCenter',  css: 1, ico: ICO.centro, t: 'Centrar',                estado: 'justifyCenter' },
  { cmd: 'justifyRight',   css: 1, ico: ICO.der,    t: 'Alinear a la derecha',   estado: 'justifyRight' },
  { sep: 1, burbuja: 1 },
  { tintas: 1, burbuja: 1 },
  { sep: 1, burbuja: 1 },
  { fondos: 1, burbuja: 1 },
  { fondo: 'transparent', glifo: '&#8709;', t: 'Quitar el resaltado', burbuja: 1 },
  { sep: 1, burbuja: 1 },
  { enlace: 1, ico: ICO.enlace, t: 'Poner un enlace', burbuja: 1 },
  { cmd: 'removeFormat', ico: ICO.limpiar, t: 'Quitar el formato de lo seleccionado', burbuja: 1 },
  { sep: 1 },
  { img: 1,      ico: ICO.imagen,   et: 'Imagen', t: 'Insertar una imagen' },
  { revertir: 1, ico: ICO.revertir, t: 'Devolver este bloque a su texto original' },
];

function dibujaBoton(h){
  if (h.sep) return '<span class="sep"></span>';
  if (h.tintas){
    return PALETA_TINTA.map(function(c){
      return '<button type="button" data-tinta="' + c[2] + '" title="Texto ' + c[1].toLowerCase() + '">' +
             '<span class="tinta" style="background:' + c[0] + '"></span></button>';
    }).join('');
  }
  if (h.fondos){
    return PALETA_FONDO.map(function(c){
      return '<button type="button" data-fondo="' + c + '" title="Resaltar">' +
             '<span class="tinta" style="background:' + c + '"></span></button>';
    }).join('');
  }
  let a = '';
  if (h.hist)     a += ' data-hist="' + h.hist + '"';
  if (h.cmd)      a += ' data-cmd="' + h.cmd + '"';
  if (h.bloque)   a += ' data-bloque="' + esc(h.bloque) + '"';
  if (h.fondo)    a += ' data-fondo="' + h.fondo + '"';
  if (h.enlace)   a += ' data-enlace="1"';
  if (h.img)      a += ' data-img-btn="1"';
  if (h.revertir) a += ' data-revertir="1"';
  if (h.css)      a += ' data-css="1"';
  const dentro = (h.ico || '') + (h.html || '') +
    (h.glifo ? '<span class="glifo">' + h.glifo + '</span>' : '') +
    (h.et ? '<span class="et">' + h.et + '</span>' : '');
  return '<button type="button"' + a + ' title="' + esc(h.t || '') + '" ' +
         'aria-label="' + esc(h.t || '') + '">' + dentro + '</button>';
}

function construyeCinta(){
  const c = document.createElement('div');
  c.id = 'cinta';
  c.setAttribute('role', 'toolbar');
  c.setAttribute('aria-label', 'Herramientas de edición');
  c.innerHTML = HERRAMIENTAS.map(dibujaBoton).join('');
  return c;
}

function construyeFormato(){
  const b = document.createElement('div');
  b.id = 'formato';
  b.setAttribute('role', 'toolbar');
  b.setAttribute('aria-label', 'Formato del texto seleccionado');
  b.innerHTML = HERRAMIENTAS.filter(function(h){ return h.burbuja; }).map(dibujaBoton).join('');
  document.body.appendChild(b);
  return b;
}

/* ---------- ejecutar una herramienta ---------- */
let zonaDestinoImg = null, pideImagen = null;

function ponEnlace(zona){
  const sel = getSelection();
  const guardado = sel && sel.rangeCount ? sel.getRangeAt(0).cloneRange() : null;
  if (guardado && guardado.collapsed){ avisa('Selecciona antes el texto del enlace.'); return; }
  const u = prompt('Dirección del enlace (tiene que empezar por https://)', 'https://');
  if (guardado){ try { sel.removeAllRanges(); sel.addRange(guardado); } catch (e){} }
  if (!u) return;
  if (!ENLACE_OK.test(u)){ avisa('Solo valen enlaces que empiecen por http:// o https://'); return; }
  document.execCommand('createLink', false, u);
  $$('a[href]', zona).forEach(function(a){
    a.setAttribute('target', '_blank'); a.setAttribute('rel', 'noopener noreferrer');
  });
}

function ejecuta(b){
  if (!b || b.disabled) return;
  if (b.dataset.hist){ b.dataset.hist === 'atras' ? deshacer() : rehacer(); return; }
  const z = zonaActiva();
  if (b.dataset.revertir){ if (z) revierte(z); else avisa('Pon el cursor en el bloque que quieras devolver.'); return; }
  if (b.dataset.imgBtn){
    zonaDestinoImg = z;
    if (!z){ avisa('Pon el cursor donde quieras la imagen.'); return; }
    if (pideImagen) pideImagen();
    return;
  }
  if (!z){ avisa('Pon antes el cursor en un bloque.'); return; }
  confirmaYa();                                   // el paso anterior se cierra aquí
  baseDe(z);
  /* styleWithCSS solo donde hace falta: la negrita y las demás salen mejor
     como etiqueta, y el color no sobrevive de otra forma. */
  const conCSS = !!(b.dataset.css || b.hasAttribute('data-tinta') || b.hasAttribute('data-fondo'));
  try { document.execCommand('styleWithCSS', false, conCSS); } catch (e){}
  if (b.dataset.enlace) ponEnlace(z);
  else if (b.dataset.bloque) document.execCommand('formatBlock', false, b.dataset.bloque);
  else if (b.dataset.cmd) document.execCommand(b.dataset.cmd);
  else if (b.hasAttribute('data-tinta')) document.execCommand('foreColor', false, b.getAttribute('data-tinta') || '#0b0b0b');
  else if (b.hasAttribute('data-fondo')){
    const c = b.getAttribute('data-fondo');
    if (!document.execCommand('hiliteColor', false, c)) document.execCommand('backColor', false, c);
  }
  if (confirma(z)) marcaSucia(z);
  pintaBotones();
}

/* que los botones digan en qué estado está el cursor, como en un Word */
const ESTADOS = ['bold','italic','underline','strikeThrough',
                 'insertUnorderedList','insertOrderedList',
                 'justifyLeft','justifyCenter','justifyRight'];
function pintaBotones(){
  pintaHistorial();
  const dentro = !!zonaActiva();
  $$('#cinta [data-cmd], #formato [data-cmd]').forEach(function(b){
    if (ESTADOS.indexOf(b.dataset.cmd) === -1) return;
    let on = false;
    if (dentro){ try { on = document.queryCommandState(b.dataset.cmd); } catch (e){} }
    b.classList.toggle('on', !!on);
  });
}

function colocaFormato(barra){
  const sel = getSelection();
  const zona = zonaActiva();
  if (!zona || !sel || !sel.rangeCount || sel.isCollapsed){
    if (!zona) barra.classList.remove('visible');
    return;
  }
  const r = sel.getRangeAt(0).getBoundingClientRect();
  if (!r.width && !r.height) return;
  barra.classList.add('visible');
  const cb = barra.getBoundingClientRect();
  const panel = document.getElementById('panel-edicion');
  const suelo = innerHeight - ((panel && panel.offsetHeight) || 0) - 8;
  let x = r.left + r.width / 2 - cb.width / 2;
  let y = r.top - cb.height - 10;
  if (y < 66) y = r.bottom + 10;
  if (y + cb.height > suelo) y = Math.max(66, r.top - cb.height - 10);
  x = Math.max(8, Math.min(x, innerWidth - cb.width - 8));
  barra.style.left = Math.round(x) + 'px';
  barra.style.top = Math.round(y) + 'px';
}

function zonaActiva(){
  const a = document.activeElement;
  if (a && a.classList && a.classList.contains('zona')) return a;
  const sel = getSelection();
  if (sel && sel.anchorNode){
    const base = sel.anchorNode.nodeType === 1 ? sel.anchorNode : sel.anchorNode.parentElement;
    const z = base && base.closest ? base.closest('.zona') : null;
    if (z) return z;
  }
  return null;
}

/* ---------- encender y apagar el modo edición ---------- */
function modoEdicion(on){
  /* No se puede editar lo que no se ve: en el móvil los puntos llegan
     plegados, así que entrar en edición los despliega, y al salir se
     devuelve el modo compacto si estaba puesto. */
  if (PINTA_COMPACTO){
    if (on && document.body.classList.contains('compacto')){
      COMPACTO_PREVIO = true; PINTA_COMPACTO(false);
    } else if (!on && COMPACTO_PREVIO){
      COMPACTO_PREVIO = false; PINTA_COMPACTO(true);
    }
  }
  if (!on) confirmaYa();
  EDITANDO = on;
  document.body.classList.toggle('editando', on);
  $$('.zona').forEach(function(z){
    /* el texto de partida se guarda antes de tocar nada: es lo que devuelve ↺
       y lo que decide si el bloque sigue marcado como editado */
    guardaOriginal(z);
    if (on) z.setAttribute('contenteditable', 'true');
    else z.removeAttribute('contenteditable');
  });
  if (on && MIDE_PANEL) requestAnimationFrame(MIDE_PANEL);
  const btn = document.getElementById('btn-editar');
  if (btn){
    btn.setAttribute('aria-pressed', String(on));
    const et = btn.querySelector('.et');
    if (et) et.textContent = on ? 'Listo' : 'Editar';
  }
  if (on){
    pintaBotones();
    avisa('Todo lo que salga con borde punteado se puede escribir. ' +
          $$('.zona').length + ' bloques.');
  } else {
    const f = document.getElementById('formato');
    if (f) f.classList.remove('visible');
    guardar();
  }
}

/* ---------- traer lo que hay guardado ---------- */
async function traeEdiciones(){
  try {
    const filas = await pide('fb360_ediciones?select=clave,html');
    DIAG.lectura = 'sí'; DIAG.ediciones = filas.length; DIAG.error = '';
    const vistas = new Set();
    filas.forEach(function(f){ vistas.add(f.clave); aplicaEdicion(f.clave, f.html); });
    /* lo que ya no está en el servidor vuelve a su original */
    $$('.zona.editada').forEach(function(z){
      const k = z.dataset.edit;
      if (!vistas.has(k) && ORIGINAL.has(k) && !SUCIAS.has(k) && document.activeElement !== z){
        z.innerHTML = ORIGINAL.get(k);
        PREVIO.set(k, z.innerHTML);
        z.classList.remove('editada');
        if (k.slice(-2) === '-n') z.classList.add('vacia');
        const notas = z.closest('.notas');
        if (notas && !notas.querySelector('.zona.editada')) notas.classList.remove('con-contenido');
      }
    });
    pintaDiag();
    return true;
  } catch (e){
    DIAG.lectura = 'no';
    DIAG.error = (e && e.message) || 'no se pudo contactar con el servidor';
    pintaDiag();
    return false;
  }
}

/* ---------- arranque ---------- */
async function initEdicion(){
  DIAG.version = (document.getElementById('version') || {}).textContent || '';
  DIAG.servidor = SB && SB.url ? SB.url.replace('https://', '') : null;
  montaDiag();
  if (!SB || !SB.url) { pintaDiag(); return; }

  /* un enlace que fuerza solo lectura, pase lo que pase en este navegador */
  if (/(^|[?&#])ver(=1)?([&#]|$)/.test(location.search + location.hash)){
    DIAG.token = 'ignorado (enlace de solo lectura)';
    await traeEdiciones();
    setInterval(traeEdiciones, 30000);
    return;
  }

  /* el token viaja en el enlace: se guarda y se quita de la barra de
     direcciones, para que no acabe en el historial ni en una captura */
  const m = (location.hash || '').match(/^#k=([A-Za-z0-9-]{8,80})$/);
  if (m){
    TOKEN = m[1];
    try { localStorage.setItem(CLAVE_TOKEN, TOKEN); } catch (e){}
    /* fuera de la barra de direcciones: que no acabe en el historial, en una
       captura de pantalla ni en un enlace reenviado sin querer */
    const sinHash = location.href.split('#')[0];
    try { history.replaceState(null, '', sinHash); } catch (e){}
    if (location.hash){ try { location.replace(sinHash); } catch (e){} }
  } else {
    try { TOKEN = localStorage.getItem(CLAVE_TOKEN); } catch (e){ TOKEN = null; }
  }

  DIAG.token = TOKEN ? 'sí' : 'no';
  const hay = await traeEdiciones();
  if (!hay && !TOKEN) { pintaDiag(); return; }
  setInterval(traeEdiciones, 30000);
  addEventListener('focus', function(){ if (!EDITANDO) traeEdiciones(); });

  if (!TOKEN) { pintaDiag(); return; }
  try { await manda({ accion: 'comprobar' }); PUEDE_EDITAR = true; DIAG.escritura = 'sí'; }
  catch (e){
    PUEDE_EDITAR = false;
    DIAG.escritura = 'no';
    DIAG.error = (e && e.message) || 'la comprobación del enlace falló';
    try { localStorage.removeItem(CLAVE_TOKEN); } catch (e2){}
    avisa('El enlace de edición no vale: ' + DIAG.error);
    pintaDiag();
    return;
  }
  document.body.classList.add('puede-editar');
  montaEditor();
  pintaDiag();
}

function montaEditor(){
  /* Que se vea de un vistazo en qué modo se está: el token queda recordado en
     el navegador, así que el enlace normal también abre como editor una vez
     usado el de edición. Sin esto, los dos enlaces parecen el mismo. */
  const btn = document.createElement('button');
  btn.className = 'btn'; btn.id = 'btn-editar'; btn.setAttribute('aria-pressed', 'false');
  btn.innerHTML = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M11.5 2.5l2 2L6 12l-2.5.5.5-2.5z" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/></svg><span class="et">Editar</span>';
  /* En la barra de arriba, no dentro de .acciones: en el móvil ese grupo se
     muda al índice desplegable, y entonces para editar había que abrir antes
     el menú. Es el botón principal de quien tiene el enlace de edición. */
  const arriba = $('.topbar');
  arriba.insertBefore(btn, $('#btn-filtros') || $('.acciones'));
  btn.addEventListener('click', function(){ modoEdicion(!EDITANDO); });

  /* un solo panel abajo: la cinta de herramientas encima del estado */
  const panel = document.createElement('div');
  panel.id = 'panel-edicion';
  const cinta = construyeCinta();
  const barra = document.createElement('div');
  barra.id = 'barra-edicion';
  barra.innerHTML =
    '<div class="estado" id="estado-edicion" role="status" aria-live="polite">Todo al día</div>' +
    '<button id="btn-exportar">Descargar</button>' +
    '<button id="btn-salir-editor" ' +
      'title="Olvida el enlace de edición en este navegador: vuelve a ser solo lectura">' +
      '<span class="larga">Cerrar sesión de editor</span><span class="corta">Cerrar sesión</span>' +
    '</button>' +
    '<button id="btn-guardar" class="primario">Guardar</button>';
  panel.appendChild(cinta);
  panel.appendChild(barra);
  document.body.appendChild(panel);

  /* la altura del panel se le devuelve al documento como hueco: nadie debe
     quedarse con el último párrafo tapado */
  function mideePanel(){
    document.documentElement.style.setProperty('--panel-edicion',
      (panel.offsetHeight || 118) + 'px');
  }
  if (window.ResizeObserver) new ResizeObserver(mideePanel).observe(panel);
  addEventListener('resize', mideePanel);
  MIDE_PANEL = mideePanel;

  const formato = construyeFormato();
  const inputImg = document.createElement('input');
  inputImg.type = 'file'; inputImg.accept = 'image/*'; inputImg.hidden = true;
  document.body.appendChild(inputImg);
  pideImagen = function(){ inputImg.click(); };

  document.addEventListener('beforeinput', function(e){
    const z = e.target.closest && e.target.closest('.zona');
    if (z && EDITANDO) baseDe(z);           // el antes, antes de que cambie
  });
  document.addEventListener('focusin', function(e){
    const z = e.target.closest && e.target.closest('.zona');
    if (z && EDITANDO) baseDe(z);
  });
  document.addEventListener('input', function(e){
    const z = e.target.closest && e.target.closest('.zona');
    if (!z || !EDITANDO) return;
    marcaSucia(z);
    anotaEscritura(z);
  });
  /* al salir de un bloque, lo escrito ahí queda cerrado como un paso */
  document.addEventListener('focusout', function(e){
    const z = e.target.closest && e.target.closest('.zona');
    if (z && EDITANDO) confirma(z);
  });

  document.addEventListener('selectionchange', function(){
    if (!EDITANDO) return;
    requestAnimationFrame(function(){ colocaFormato(formato); pintaBotones(); });
  });
  addEventListener('scroll', function(){
    if (EDITANDO && formato.classList.contains('visible')) colocaFormato(formato);
  }, { passive: true });

  /* las dos barras hacen lo mismo y no le roban el foco al texto */
  [cinta, formato].forEach(function(bar){
    bar.addEventListener('mousedown', function(e){ e.preventDefault(); });
    bar.addEventListener('click', function(e){
      const b = e.target.closest('button');
      if (b) ejecuta(b);
    });
  });

  document.addEventListener('keydown', function(e){
    if (!EDITANDO) return;
    if (!(e.ctrlKey || e.metaKey)) {
      /* el Intro cierra el paso: deshacer no debe saltarse un párrafo entero */
      if (e.key === 'Enter' && zonaActiva()) setTimeout(confirmaYa, 0);
      return;
    }
    const t = e.key.toLowerCase();
    if (t === 's'){ e.preventDefault(); confirmaYa(); guardar(); return; }
    if (t === 'z' && !e.shiftKey){ e.preventDefault(); deshacer(); return; }
    if ((t === 'z' && e.shiftKey) || t === 'y'){ e.preventDefault(); rehacer(); return; }
    const z = zonaActiva();
    if (!z) return;
    const atajo = { b: 'bold', i: 'italic', u: 'underline' }[t];
    if (atajo){
      e.preventDefault();
      confirmaYa();
      try { document.execCommand('styleWithCSS', false, false); } catch (err){}
      document.execCommand(atajo);
      if (confirma(z)) marcaSucia(z);
      pintaBotones();
    }
  });

  /* pegar: texto sin formato ajeno, y capturas del portapapeles */
  document.addEventListener('paste', function(e){
    const z = e.target.closest && e.target.closest('.zona');
    if (!z || !EDITANDO) return;
    const items = (e.clipboardData && e.clipboardData.items) || [];
    for (let i = 0; i < items.length; i++){
      if (/^image\//.test(items[i].type)){
        e.preventDefault();
        insertaFichero(items[i].getAsFile(), z);
        return;
      }
    }
    e.preventDefault();
    confirmaYa();
    document.execCommand('insertText', false, (e.clipboardData && e.clipboardData.getData('text/plain')) || '');
    if (confirma(z)) marcaSucia(z);
  });

  /* arrastrar y soltar */
  document.addEventListener('dragover', function(e){
    const z = e.target.closest && e.target.closest('.zona');
    if (!z || !EDITANDO) return;
    e.preventDefault(); z.classList.add('soltando');
  });
  document.addEventListener('dragleave', function(e){
    const z = e.target.closest && e.target.closest('.zona');
    if (z) z.classList.remove('soltando');
  });
  document.addEventListener('drop', function(e){
    const z = e.target.closest && e.target.closest('.zona');
    if (!z || !EDITANDO) return;
    e.preventDefault(); z.classList.remove('soltando');
    const fs = (e.dataTransfer && e.dataTransfer.files) || [];
    for (let i = 0; i < fs.length; i++) insertaFichero(fs[i], z);
  });

  inputImg.addEventListener('change', function(){
    const f = inputImg.files && inputImg.files[0];
    if (f) insertaFichero(f, zonaDestinoImg);
    inputImg.value = '';
  });

  document.getElementById('btn-guardar').addEventListener('click', function(){
    confirmaYa(); guardar();
  });
  document.getElementById('btn-exportar').addEventListener('click', exporta);

  /* devolver este navegador a modo lectura: olvida el enlace de edición */
  document.getElementById('btn-salir-editor').addEventListener('click', async function(){
    confirmaYa();
    if (SUCIAS.size && !confirm('Hay cambios sin guardar. ¿Salir igualmente?')) return;
    await guardar().catch(function(){});
    try { localStorage.removeItem(CLAVE_TOKEN); } catch (e){}
    location.replace(location.href.split('#')[0]);
  });

  addEventListener('beforeunload', function(e){
    if (SUCIAS.size){ e.preventDefault(); e.returnValue = ''; }
  });

  pintaEstado();
  pintaHistorial();
}

async function exporta(){
  let filas = [];
  try { filas = await pide('fb360_ediciones?select=clave,html,actualizado'); } catch (e){}
  const salida = { informe: DATA.meta.titulo, generado: new Date().toISOString(), ediciones: filas };
  const blob = new Blob([JSON.stringify(salida, null, 1)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'ediciones-diagnostico-360.json';
  document.body.appendChild(a); a.click();
  setTimeout(function(){ URL.revokeObjectURL(a.href); a.remove(); }, 1000);
  avisa('Descargando ' + filas.length + ' bloques editados');
}

/* ---------------- arranque ---------------- */
function init(){
  renderSidebar();
  render();
  renderFiltros();
  indexarTarjetas();
  initPlan();
  initTooltip();
  initLightbox();
  initTema();
  initHash();

  /* buscador */
  const inp = $('#q');
  let pend = null;
  inp.addEventListener('input', function(){
    estado.q = inp.value;
    $('#q-limpiar').hidden = !inp.value;
    if (pend) cancelAnimationFrame(pend);
    pend = requestAnimationFrame(aplicar);
  });
  $('#q-limpiar').addEventListener('click', function(){
    inp.value = ''; estado.q = ''; $('#q-limpiar').hidden = true; inp.focus(); aplicar();
  });

  /* chips */
  $('#filtros').addEventListener('click', function(e){
    const b = e.target.closest('.chip');
    if (!b) return;
    if (b.id === 'limpiar-todo'){
      estado.q = ''; inp.value = ''; $('#q-limpiar').hidden = true;
      estado.prioridad.clear(); estado.estado.clear();
      $$('#filtros .chip[data-f]').forEach(function(c){ c.setAttribute('aria-pressed','false'); });
      aplicar();
      return;
    }
    const set = estado[b.dataset.f];
    const v = b.dataset.v;
    if (set.has(v)){ set.delete(v); b.setAttribute('aria-pressed','false'); }
    else { set.add(v); b.setAttribute('aria-pressed','true'); }
    aplicar();
  });

  /* Modo compacto. En una pantalla estrecha es el estado POR DEFECTO: con 267
     puntos abiertos, recorrer un módulo en el teléfono es interminable. Basta
     con tocar un punto para desplegarlo. */
  const bc = $('#btn-compacto');
  function pintaCompacto(on){
    document.body.classList.toggle('compacto', on);
    bc.setAttribute('aria-pressed', String(on));
    bc.querySelector('.et').textContent = on ? 'Desplegar' : 'Compacto';
    $$('.punto').forEach(function(p){
      p.classList.remove('abierto');
      const cab = $('.punto-cab', p);
      if (cab) cab.setAttribute('aria-expanded', String(!on));
    });
  }
  PINTA_COMPACTO = pintaCompacto;
  const elegido = Store.get('fb360.compacto', null);
  pintaCompacto(elegido === null ? esMovil() : !!elegido);
  bc.addEventListener('click', function(){
    const on = !document.body.classList.contains('compacto');
    Store.set('fb360.compacto', on);
    pintaCompacto(on);
  });

  /* desplegar un punto */
  function alternar(cab){
    if (!document.body.classList.contains('compacto')) return;
    const p = cab.closest('.punto');
    const on = p.classList.toggle('abierto');
    cab.setAttribute('aria-expanded', String(on));
  }
  document.addEventListener('click', function(e){
    const cab = e.target.closest('.punto-cab');
    if (cab && !e.target.closest('a')) alternar(cab);
    const tr = e.target.closest('.t-modulos tr[data-ir]');
    if (tr) location.hash = '#' + tr.dataset.ir;
  });
  document.addEventListener('keydown', function(e){
    if (e.key !== 'Enter' && e.key !== ' ') return;
    const cab = e.target.closest && e.target.closest('.punto-cab');
    if (cab){ e.preventDefault(); alternar(cab); }
    const tr = e.target.closest && e.target.closest('.t-modulos tr[data-ir]');
    if (tr){ e.preventDefault(); location.hash = '#' + tr.dataset.ir; }
  });

  const barraFiltros = $('#filtros');

  /* índice desplegable */
  const bm = $('#btn-menu'), sb = $('#sidebar'), fondo = $('#fondo-sheet');
  function abreMenu(v){
    if (v) sb.dataset.abiertoPorElUsuario = '1'; else delete sb.dataset.abiertoPorElUsuario;
    sb.hidden = !v;
    bm.setAttribute('aria-expanded', String(v));
    if (esMovil()) fondo.hidden = !(v || barraFiltros.classList.contains('abierta'));
  }
  bm.addEventListener('click', function(){ abreMenu(sb.hidden); });
  sb.addEventListener('click', function(e){
    if (e.target.closest('.nav-a') && esMovil()) abreMenu(false);
  });

  /* hoja de filtros: en el móvil sube desde abajo en vez de ocupar la pantalla */
  const bf = $('#btn-filtros');
  function abreFiltros(v){
    barraFiltros.classList.toggle('abierta', v);
    bf.setAttribute('aria-expanded', String(v));
    fondo.hidden = !(v || (esMovil() && !sb.hidden));
  }
  let ultimoFiltro = 0;
  bf.addEventListener('click', function(e){
    const t = e.timeStamp || 0;
    if (t && t - ultimoFiltro < 350) return;   // toque duplicado
    ultimoFiltro = t;
    abreFiltros(!barraFiltros.classList.contains('abierta'));
  });
  fondo.addEventListener('click', function(){ abreFiltros(false); abreMenu(false); });
  document.addEventListener('click', function(e){
    if (e.target.id === 'cerrar-filtros') abreFiltros(false);
  });
  document.addEventListener('keydown', function(e){
    if (e.key === 'Escape'){ abreFiltros(false); if (esMovil()) abreMenu(false); }
  });

  /* botón flotante para volver arriba */
  const fab = $('#btn-arriba');
  fab.addEventListener('click', function(){
    scrollTo({ top: 0, behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
  });
  addEventListener('scroll', function(){
    fab.classList.toggle('visible', scrollY > 700);
  }, { passive: true });

  /* los controles viven en la barra superior, y en el móvil dentro del índice */
  const acciones = $('.acciones'), topbar = $('.topbar'), zona = $('#zona-controles');
  function colocaControles(){
    const destino = esMovil() ? zona : topbar;
    if (acciones.parentNode !== destino) destino.appendChild(acciones);
  }
  function ajustaMenu(){
    colocaControles();
    if (esMovil()){
      /* la hoja de filtros existe siempre; lo que la muestra es .abierta */
      if (!sb.dataset.abiertoPorElUsuario){
        sb.hidden = true;
        bm.setAttribute('aria-expanded', 'false');
      }
    } else {
      sb.hidden = false;
      bm.setAttribute('aria-expanded', 'true');
      abreFiltros(false);
      fondo.hidden = true;
    }
  }
  ajustaMenu();
  addEventListener('resize', ajustaMenu);

  /* atajo: / enfoca el buscador */
  document.addEventListener('keydown', function(e){
    if (e.key === '/' && document.activeElement !== inp){
      e.preventDefault(); inp.focus(); inp.select();
    }
  });

  $('#imprimir').addEventListener('click', function(){ print(); });

  aplicar();

  /* la edición se enciende sola donde hay dónde guardar */
  initEdicion();
}

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
else init();
"""


# ==========================================================================
#  Ensamblado
# ==========================================================================

def dim_png(datos):
    return struct.unpack(">II", datos[16:24])


def json_seguro(obj):
    """JSON incrustable en <script>: escapa < para que no aparezca </script>."""
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")) \
        .replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def main():
    contenido_p = os.path.join(AQUI, "contenido.json")
    if not os.path.exists(contenido_p):
        sys.exit("Falta contenido.json — ejecuta antes extraer_contenido.py")
    contenido = json.load(open(contenido_p, encoding="utf-8"))

    # datos de graficos verificados
    graficos_p = os.path.join(AQUI, "graficos.json")
    if os.path.exists(graficos_p):
        contenido["graficos"] = json.load(open(graficos_p, encoding="utf-8"))
        contenido["meta"]["total_graficos"] = len(contenido["graficos"])

    # capturas -> data URI
    imgs = {}
    total_bytes = 0
    for c in contenido.get("capturas", []):
        ruta = os.path.join(AQUI, "capturas", c["archivo"])
        if not os.path.exists(ruta):
            print("  AVISO — falta la captura", c["archivo"])
            continue
        datos = open(ruta, "rb").read()
        total_bytes += len(datos)
        imgs[c["archivo"]] = "data:image/png;base64," + base64.b64encode(datos).decode("ascii")

    meta = contenido["meta"]
    # Nombre de la pestaña y de la ficha al publicarlo. Es rotulo de interfaz,
    # no texto del informe.
    titulo = "Diagnóstico Digital 360 · Freddy Bernal"

    # El mismo contenido se emite de dos formas:
    #   informe.html           documento completo, para abrir con doble clic
    #   informe_artifact.html  solo <title>, <style> y cuerpo, porque el
    #                          servicio de publicacion aporta su propio
    #                          <!doctype>, <html>, <head> y <body>.
    cabeza = (
        "<title>" + titulo + "</title>\n"
        "<style>" + CSS + "</style>\n"
    )

    cuerpo = (
'<a class="saltar" href="#contenido">Saltar al contenido</a>\n'

        '<header class="topbar">\n'
        '  <button class="btn solo-movil" id="btn-menu" aria-expanded="false" aria-controls="sidebar">'
        '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M1 3h14M1 8h14M1 13h14" stroke="currentColor" stroke-width="1.6" fill="none"/></svg>'
        '<span class="et">Índice</span></button>\n'
        '  <div class="marca"><b>' + meta["titulo"] + '</b><span>' + meta["sujeto"] + '</span></div>\n'
        '  <div class="buscador">\n'
        '    <svg class="lupa" viewBox="0 0 16 16" aria-hidden="true"><circle cx="7" cy="7" r="5" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M11 11l4 4" stroke="currentColor" stroke-width="1.6"/></svg>\n'
        '    <input id="q" type="search" placeholder="Buscar en los ' + str(meta["total_puntos"]) + ' puntos…" '
        'aria-label="Buscar en los puntos del informe" autocomplete="off" spellcheck="false">\n'
        '    <button class="limpiar" id="q-limpiar" aria-label="Limpiar la búsqueda" hidden>&times;</button>\n'
        '  </div>\n'
        '  <div class="contador" id="contador" role="status" aria-live="polite"></div>\n'
        '  <button class="btn solo-movil" id="btn-filtros" aria-expanded="false" aria-controls="filtros">'
        '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M1.5 3h13M4 8h8M6.5 13h3" stroke="currentColor" stroke-width="1.6" fill="none" stroke-linecap="round"/></svg>'
        '<span class="et">Filtros</span><span class="n" id="n-filtros" hidden>0</span></button>\n'
        '  <div class="acciones">\n'
        '    <button class="btn" id="btn-compacto" aria-pressed="false">'
        '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M1 4h14M1 8h14M1 12h14" stroke="currentColor" stroke-width="1.4" fill="none"/></svg>'
        '<span class="et">Compacto</span></button>\n'
        '    <button class="btn" id="btn-tema" aria-pressed="false">'
        '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M13 9.5A5.5 5.5 0 016.5 3a5.5 5.5 0 106.5 6.5z" fill="currentColor"/></svg>'
        '<span class="et">Oscuro</span></button>\n'
        '    <button class="btn" id="imprimir">'
        '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M4 6V2h8v4M4 12H2V6h12v6h-2M4 10h8v4H4z" fill="none" stroke="currentColor" stroke-width="1.3"/></svg>'
        '<span class="et">Imprimir</span></button>\n'
        '  </div>\n'
        '</header>\n'

        '<div class="shell">\n'
        '  <nav class="sidebar" id="sidebar" aria-label="Índice del informe"></nav>\n'
        '  <main id="contenido-wrap">\n'
        '    <div id="contenido"></div>\n'
        '  </main>\n'
        '</div>\n'

        '<div class="fondo-sheet" id="fondo-sheet" hidden></div>\n'
        '<button class="fab" id="btn-arriba" aria-label="Volver arriba">'
        '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 13V3M3.5 7.5L8 3l4.5 4.5" stroke="currentColor" stroke-width="1.7" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>'
        '</button>\n'
        '<div id="tip" role="tooltip" aria-hidden="true"></div>\n'
        '<div id="lightbox" role="dialog" aria-modal="true" aria-label="Captura ampliada">\n'
        '  <button class="cerrar" id="lb-cerrar" aria-label="Cerrar">&times;</button>\n'
        '  <img id="lb-img" alt="">\n'
        '  <figcaption id="lb-cap"></figcaption>\n'
        '</div>\n'
    )

    sello = datetime.datetime.now().strftime("%d %b %Y · %H:%M")
    servidor = ('<span id="version" hidden>' + sello + "</span>\n"
                '<script type="application/json" id="servidor">'
                + json_seguro(SERVIDOR) + "</script>\n")

    cola = (
        '<script type="application/json" id="datos">' + json_seguro(contenido) + "</script>\n"
        '<script type="application/json" id="capturas-b64">' + json_seguro(imgs) + "</script>\n"
        "<script>" + JS + "</script>\n"
    )

    html = (
        "<!DOCTYPE html>\n"
        '<html lang="es">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<meta name="description" content="' + meta.get("alcance", "") + '">\n'
        + cabeza +
        "</head>\n<body>\n" + cuerpo + servidor + cola + "</body>\n</html>\n"
    )
    # El artefacto NO lleva servidor: dentro de claude.ai la politica de
    # seguridad bloquea las llamadas a hosts externos, asi que alli el informe
    # es de solo lectura y el editor ni se enciende.
    artefacto = cabeza + cuerpo + ('<span id="version" hidden>' + sello + "</span>\n") + cola

    salida = os.path.join(AQUI, "informe.html")
    with open(salida, "w", encoding="utf-8") as fh:
        fh.write(html)

    salida_art = os.path.join(AQUI, "informe_artifact.html")
    with open(salida_art, "w", encoding="utf-8") as fh:
        fh.write(artefacto)

    # ---- index.html para GitHub Pages ----
    # Aqui las capturas NO van incrustadas: se sirven como archivos y el
    # navegador las pide solo al llegar a ellas. El HTML baja de 4,8 MB a
    # menos de 1, que es la diferencia entre util e inutil en un movil.
    contenido_web = dict(contenido)
    contenido_web["meta"] = dict(meta, capturas_aparte=True)
    rutas = {c["archivo"]: "capturas/" + c["archivo"]
             for c in contenido.get("capturas", [])}

    # icono en línea: la pestaña y el acceso directo del móvil quedan bien
    # sin pedir un archivo aparte
    icono = (
        "data:image/svg+xml,"
        "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
        "%3Crect width='32' height='32' rx='7' fill='%231d2027'/%3E"
        "%3Crect x='7' y='19' width='4' height='7' rx='1' fill='%232a78d6'/%3E"
        "%3Crect x='14' y='13' width='4' height='13' rx='1' fill='%231baf7a'/%3E"
        "%3Crect x='21' y='7' width='4' height='19' rx='1' fill='%23eb6834'/%3E"
        "%3C/svg%3E"
    )
    cabeza_web = (
        '<link rel="icon" href="' + icono + '">\n'
        '<link rel="apple-touch-icon" href="' + icono + '">\n'
        '<meta name="theme-color" content="#ffffff" media="(prefers-color-scheme: light)">\n'
        '<meta name="theme-color" content="#0d0f12" media="(prefers-color-scheme: dark)">\n'
        '<meta name="apple-mobile-web-app-title" content="Diagnóstico 360">\n'
        '<meta property="og:type" content="article">\n'
        '<meta property="og:title" content="' + titulo + '">\n'
        '<meta property="og:description" content="' + meta.get("alcance", "") + '">\n'
        '<meta property="og:locale" content="es_ES">\n'
        + cabeza
    )
    web = (
        "<!DOCTYPE html>\n"
        '<html lang="es">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '<meta name="description" content="' + meta.get("alcance", "") + '">\n'
        '<meta name="color-scheme" content="light dark">\n'
        + cabeza_web +
        "</head>\n<body>\n" + cuerpo + servidor +
        '<script type="application/json" id="datos">' + json_seguro(contenido_web) + "</script>\n"
        '<script type="application/json" id="capturas-b64">' + json_seguro(rutas) + "</script>\n"
        "<script>" + JS + "</script>\n"
        "</body>\n</html>\n"
    )
    salida_web = os.path.join(AQUI, "index.html")
    with open(salida_web, "w", encoding="utf-8") as fh:
        fh.write(web)
    # sin esto, GitHub Pages pasa el sitio por Jekyll sin necesidad
    open(os.path.join(AQUI, ".nojekyll"), "w").close()

    mb = os.path.getsize(salida) / 1024 / 1024
    print("informe.html escrito —", round(mb, 2), "MB")
    print("informe_artifact.html escrito —",
          round(os.path.getsize(salida_art) / 1024 / 1024, 2), "MB (para publicar)")
    print("index.html escrito —",
          round(os.path.getsize(salida_web) / 1024 / 1024, 2), "MB (GitHub Pages, capturas aparte)")
    print("  módulos    ", meta["total_modulos"])
    print("  puntos     ", meta["total_puntos"])
    print("  tablas     ", meta["total_tablas"])
    print("  capturas   ", len(imgs), "(", round(total_bytes / 1024 / 1024, 2), "MB en PNG )")
    print("  gráficos   ", len(contenido.get("graficos", [])))
    print("  acciones   ", meta["total_acciones"])


if __name__ == "__main__":
    main()
