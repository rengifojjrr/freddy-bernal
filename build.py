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
import json
import os
import struct
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))


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
  margin:0; background:var(--bg); color:var(--texto);
  font-family:system-ui,-apple-system,"Segoe UI",sans-serif;
  font-size:15px; line-height:1.62;
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
  position:sticky; top:0; z-index:60;
  display:flex; align-items:center; gap:14px;
  height:var(--topbar); padding:0 18px;
  background:var(--card); border-bottom:1px solid var(--linea);
}
.marca{display:flex; flex-direction:column; line-height:1.15; flex:none}
.marca b{font-size:13px; font-weight:650; letter-spacing:.02em}
.marca span{font-size:11px; color:var(--muted)}

.buscador{position:relative; flex:1 1 auto; max-width:460px; min-width:0}
.buscador input{
  width:100%; padding:8px 30px 8px 32px;
  background:var(--bg); color:var(--texto);
  border:1px solid var(--linea2); border-radius:var(--r);
  font-size:13.5px;
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

.menu-movil{display:none}

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
.seccion{padding:44px 40px 8px; scroll-margin-top:calc(var(--topbar) + 8px)}
.seccion-cab{margin-bottom:28px; padding-bottom:14px; border-bottom:1px solid var(--linea2)}
.seccion-cab h2{font-size:23px; letter-spacing:-.02em}
.seccion-cab .sub{margin-top:6px; font-size:13.5px; color:var(--texto2); max-width:var(--lectura)}
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
.modulo{margin:0 0 52px; scroll-margin-top:calc(var(--topbar) + 8px)}
.modulo-cab{padding-bottom:15px; border-bottom:2px solid var(--texto); margin-bottom:20px}
.modulo-cab .id{
  font-size:11px; font-weight:700; letter-spacing:.1em; color:var(--blue);
}
.modulo-cab h2{font-size:21px; margin-top:5px; letter-spacing:-.02em}
.modulo-meta{
  display:flex; flex-wrap:wrap; gap:8px 22px; margin-top:12px; font-size:12px; color:var(--texto2);
}
.modulo-meta div{display:flex; gap:7px; align-items:baseline}
.modulo-meta span{
  font-size:10px; font-weight:650; letter-spacing:.08em;
  text-transform:uppercase; color:var(--muted); flex:none;
}
.modulo-resumen{margin:16px 0 26px}

/* ---------- punto ---------- */
.punto{
  background:var(--card); border:1px solid var(--linea); border-radius:var(--r);
  margin-bottom:14px; box-shadow:var(--sombra);
  scroll-margin-top:calc(var(--topbar) + 8px);
}
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
  flex:none; width:16px; height:16px; margin-top:2px; cursor:pointer;
  accent-color:var(--aqua);
}
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
  background:var(--bg); padding:12px 40px;
  border-bottom:1px solid var(--linea);
  transition:opacity .15s;
}
.filtros[hidden]{display:none !important}
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

/* ---------- responsive ---------- */
@media (max-width:1040px){
  :root{--sidebar:246px}
  .seccion,.filtros,.portada{padding-left:28px; padding-right:28px}
}
@media (max-width:700px){
  .btn .et{display:none}
  .btn{padding:6px 8px}
  .menu-movil .et{display:none}
  .topbar{gap:8px; padding:0 12px}
  .acciones{gap:4px}
}
@media (max-width:860px){
  .menu-movil{display:inline-flex}
  .shell{display:block}
  .sidebar{
    position:static; width:auto; height:auto; max-height:66vh;
    border-right:0; border-bottom:1px solid var(--linea2); padding:14px 0 20px;
  }
  .sidebar[hidden]{display:none !important}
  .seccion,.filtros,.portada{padding-left:18px; padding-right:18px}
  .seccion{padding-top:32px}
  .filtros{position:static}
  .punto-cuerpo{padding-left:20px}
  .marca{display:none}
  .buscador{max-width:none}
  .contador{display:none}
  .portada h1{font-size:26px}
  .ficha{grid-template-columns:1fr}
  .ficha dt{border-bottom:0; padding-bottom:0}
  .ficha dd{padding-top:2px}
  .filtro-et{width:auto}
}
@media (max-width:420px){
  .seccion,.filtros,.portada{padding-left:14px; padding-right:14px}
  .punto-cab{padding:14px}
  .punto-cuerpo{padding:0 14px 14px}
  .hallazgo{padding:16px}
}

/* ---------- impresion ---------- */
@media print{
  :root{--bg:#fff; --card:#fff; --texto:#000; --texto2:#222; --linea:#ccc; --linea2:#999; --tinte:#f4f4f4; --sombra:none}
  .topbar,.sidebar,.filtros,.acciones,.buscador,#lightbox,#tip,.saltar,.chev{display:none !important}
  body{font-size:10.5pt; background:#fff}
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

function colorBarra(b){
  if (b.destaca === 'A') return 'var(--aqua)';
  if (b.destaca === 'B') return 'var(--orange)';
  if (b.destaca === 'C') return 'var(--red)';
  if (b.destaca === 'D') return 'var(--blue)';
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
  const anchoLbl = opts.anchoLbl != null ? opts.anchoLbl : 240;
  const x0 = opts.x0 != null ? opts.x0 : 0;
  const ancho = opts.ancho != null ? opts.ancho : VB;
  const rowH = opts.rowH != null ? opts.rowH : 30;
  const gap = opts.gap != null ? opts.gap : 9;
  const divergente = !!opts.divergente;
  const finEtiqueta = 96;                       // hueco para la etiqueta de valor
  const bx = x0 + anchoLbl;                      // inicio del área de barras
  const bw = ancho - anchoLbl - finEtiqueta;

  let y = opts.y0 || 0;
  let s = '';

  const max = opts.max != null ? opts.max : ejeMax(barras.map(function(b){ return b.valor; }));
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
    s += '<text class="cat" x="' + (x0 + anchoLbl - 12) + '" y="' + (cy + 4.5) +
         '" text-anchor="end">' + esc(b.cat) + '</text>';

    /* etiqueta de valor, directamente sobre la barra */
    const vx = v < 0 ? bxi - 8 : bxi + w + 8;
    const anc = v < 0 ? 'end' : 'start';
    s += '<text class="val" x="' + vx.toFixed(1) + '" y="' + (cy + 4.5) +
         '" text-anchor="' + anc + '">' + esc(b.etiqueta) + '</text>';

    if (b.detalle){
      s += '<text class="det" x="' + (x0 + anchoLbl - 12) + '" y="' + (cy + 17) +
           '" text-anchor="end">' + esc(b.detalle) + '</text>';
    }
    s += '</g>';
    y += rowH + gap;
  });

  return { svg: s, alto: y - (opts.y0 || 0) - gap };
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
    const a = panelBarras(paneles[0], {x0:0, ancho:anchoPanel, anchoLbl:170, rowH:26, gap:8});
    const b = panelBarras(paneles[1], {x0:VB/2 + 18, ancho:anchoPanel, anchoLbl:120, rowH:26, gap:8});
    inner = a.svg + b.svg;
    alto = Math.max(a.alto, b.alto) + 12;

  } else if (g.tipo === 'panelesConBanda'){
    let y = 0;
    paneles.forEach(function(p){
      const r = panelBarras(p, {x0:0, ancho:VB, anchoLbl:250, rowH:30, gap:9, y0:y});
      inner += r.svg;
      y += r.alto + 34;
    });
    alto = y;

  } else if (g.tipo === 'barh+composicion' && paneles.length >= 2){
    const a = panelBarras(paneles[0], {x0:0, ancho:VB*0.63, anchoLbl:210, rowH:22, gap:6});
    const b = panelBarras(paneles[1], {x0:VB*0.63 + 26, ancho:VB*0.37 - 26, anchoLbl:150, rowH:26, gap:9});
    inner = a.svg + b.svg;
    alto = Math.max(a.alto, b.alto) + 12;

  } else if (g.tipo === 'divergente'){
    const r = panelBarras(paneles[0] || {barras:[]}, {x0:0, ancho:VB, anchoLbl:250, rowH:30, gap:10, divergente:true});
    inner = r.svg; alto = r.alto + 12;

  } else if (g.tipo === 'apiladaPorModulo'){
    return dibujarApilada(g);

  } else {
    let y = 0;
    paneles.forEach(function(p){
      const r = panelBarras(p, {x0:0, ancho:VB, anchoLbl:260, rowH:30, gap:10, y0:y});
      inner += r.svg;
      y += r.alto + 30;
    });
    alto = y + 6;
  }

  return svgEnvoltorio(inner, alto);
}

/* g9 — barra apilada por módulo, contada sobre modulos[].puntos[].prioridad */
function dibujarApilada(g){
  const anchoLbl = 250, finEt = 70;
  const bx = anchoLbl, bw = VB - anchoLbl - finEt;
  const rowH = 22, gap = 7;
  const maxTot = Math.max.apply(null, DATA.modulos.map(function(m){ return m.puntos.length; }));
  let y = 0, s = '';

  DATA.modulos.forEach(function(m){
    const c = CUENTA[m.id];
    const tot = m.puntos.length;
    let x = bx;
    const cy = y + rowH/2;

    s += '<text class="cat" x="' + (anchoLbl - 12) + '" y="' + (cy + 4.5) + '" text-anchor="end">' +
         esc(m.id + ' · ' + m.titulo) + '</text>';

    ORDEN_PRIORIDAD.forEach(function(pr){
      const n = c[pr];
      if (!n) return;
      const w = (n / maxTot) * bw;
      s += '<g class="barra" data-tip-t="' + esc(m.id + ' · ' + pr) + '" data-tip-v="' + n +
           (n === 1 ? ' punto' : ' puntos') + '" data-tip-d="' + esc(m.titulo) + '">';
      s += '<rect class="b" x="' + x.toFixed(1) + '" y="' + y + '" width="' + Math.max(w,1).toFixed(1) +
           '" height="' + rowH + '" fill="' + COLOR_PRIORIDAD[pr] + '"/>';
      s += '</g>';
      x += w;
    });

    s += '<text class="val" x="' + (x + 8).toFixed(1) + '" y="' + (cy + 4.5) + '">' + tot + '</text>';
    y += rowH + gap;
  });

  /* leyenda: aquí sí hace falta, porque hay cinco series apiladas */
  y += 12;
  let lx = bx;
  ORDEN_PRIORIDAD.forEach(function(pr){
    const total = DATA.modulos.reduce(function(a,m){ return a + CUENTA[m.id][pr]; }, 0);
    s += '<rect x="' + lx + '" y="' + (y - 8) + '" width="9" height="9" fill="' + COLOR_PRIORIDAD[pr] + '"/>';
    s += '<text class="tick" x="' + (lx + 14) + '" y="' + y + '">' +
         esc(pr === '—' ? 'informativo' : pr.toLowerCase()) + ' · ' + total + '</text>';
    lx += 32 + (pr === '—' ? 96 : pr.length * 8.2 + 46);
  });
  y += 12;

  return svgEnvoltorio(s, y);
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
  return '<figure id="figura-' + c.figura + '">' +
    '<img src="' + src + '" alt="' + esc(alt) + '" width="' + c.ancho + '" height="' + c.alto + '"' +
    ' data-fig="' + c.figura + '">' +
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
  h += prosa(p.hallazgo);
  if (p.tabla) h += tablaHTML(p.tabla);
  (CAPTURA_DE[clave] || []).forEach(function(c){ h += figuraHTML(c); });
  if (GRAFICO_DE[clave]) h += graficoHTML(GRAFICO_DE[clave]);
  h += '<div class="accion"><span class="et">Acción</span><p>' + esc(p.accion) + '</p></div>';
  h += '</div></article>';
  return h;
}

function moduloHTML(m){
  const c = CUENTA[m.id];
  let h = '<section class="modulo" id="' + m.id.toLowerCase() + '">';
  h += '<div class="modulo-cab"><div class="id">' + esc(m.id) + '</div><h2>' + esc(m.titulo) + '</h2>';
  h += '<div class="modulo-meta">';
  h += '<div><span>Puntos</span>' + m.puntos.length + '</div>';
  if (c['CRÍTICA']) h += '<div><span>Críticos</span>' + c['CRÍTICA'] + '</div>';
  if (c['ALTA']) h += '<div><span>Alta</span>' + c['ALTA'] + '</div>';
  if (m.estado_modulo) h += '<div><span>Estado</span>' + esc(m.estado_modulo) + '</div>';
  if (m.calificacion) h += '<div><span>Valoración</span>' + esc(m.calificacion) + '</div>';
  h += '</div>';
  if (m.alcance) h += '<div class="modulo-meta"><div><span>Alcance</span>' + esc(m.alcance) + '</div></div>';
  if (m.fuente) h += '<div class="modulo-meta"><div><span>Fuente</span>' + esc(m.fuente) + '</div></div>';
  h += '</div>';
  if (m.resumen && m.resumen.length) h += '<div class="modulo-resumen">' + prosa(m.resumen) + '</div>';
  m.puntos.forEach(function(p){ h += puntoHTML(m, p); });
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
    h += '<div class="prosa" style="margin-top:24px">' +
         por.descripcion.map(function(t){ return '<p>' + esc(t) + '</p>'; }).join('') + '</div>';
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
  if (DATA.resumen.intro) h += '<div class="sub">' + esc(DATA.resumen.intro.t) + '</div>';
  h += '</div>';

  h += '<div class="hallazgos">';
  DATA.resumen.hallazgos.forEach(function(hh, i){
    h += '<div class="hallazgo"><div class="num">' + (i+1) + '</div><div>' +
         '<h3>' + esc(hh[0]) + '</h3>' +
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
  DATA.como_leer.forEach(function(sec){
    h += '<div class="cat"><h3>' + esc(sec[0]) + '</h3>' + prosa(sec[1]) + '</div>';
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

  h += '<div id="lista-modulos">';
  DATA.modulos.forEach(function(m){ h += moduloHTML(m); });
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
    if (bl[1]) h += '<div class="desc">' + esc(bl[1].t) + '</div>';
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
        (ac[2] ? '<div class="det">' + esc(ac[2].t) + '</div>' : '') +
        '</div></div>';
    });
    h += '</div>';
  });
  h += '</section>';

  /* ---------- fase de profundización ---------- */
  h += '<section class="seccion" id="profundizacion">';
  h += '<div class="seccion-cab"><div class="eyebrow">Qué falta</div>' +
       '<h2>Fase de profundización</h2>';
  if (DATA.vacios.intro) h += '<div class="sub">' + esc(DATA.vacios.intro.t) + '</div>';
  h += '</div>';
  DATA.vacios.categorias.forEach(function(cat){
    h += '<div class="cat"><h3>' + esc(cat[0]) + '</h3><ul>';
    let esf = '';
    cat[1].forEach(function(l){
      if (/^ESFUERZO/i.test(l.t)) { esf = l; return; }
      h += '<li>' + (l.lead && l.t.indexOf(l.lead) === 0
        ? '<b class="lead">' + esc(l.lead) + '</b>' + esc(l.t.slice(l.lead.length))
        : esc(l.t)) + '</li>';
    });
    h += '</ul>';
    if (esf) h += '<div class="esfuerzo">' + esc(esf.t) + '</div>';
    h += '</div>';
  });
  h += '</section>';

  /* ---------- fuentes y metodología ---------- */
  h += '<section class="seccion" id="fuentes">';
  h += '<div class="seccion-cab"><div class="eyebrow">Anexos</div>' +
       '<h2>Fuentes y metodología</h2></div>';
  h += '<h3 style="font-size:15px;margin-bottom:4px">Componentes del análisis</h3>';
  h += tablaHTML({ headers: DATA.fuentes.documentos_headers, rows: DATA.fuentes.documentos });
  DATA.fuentes.grupos.forEach(function(g){
    if (!g[1].length) return;
    h += '<h3 style="font-size:15px;margin:26px 0 8px">' + esc(g[0]) + '</h3><ul class="lista-fuentes">';
    g[1].forEach(function(l){ h += '<li>' + esc(l.t) + '</li>'; });
    h += '</ul>';
  });
  h += '<h3 style="font-size:15px;margin:30px 0 8px">Nota metodológica y trazabilidad</h3>';
  h += prosa(DATA.nota);
  h += '</section>';

  $('#contenido').innerHTML = h;
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
  let h = '';
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
  $('#filtros').innerHTML = h;
}

/* ---------------- búsqueda y filtrado ---------------- */
const estado = { q:'', prioridad:new Set(), estado:new Set() };
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

  const filtrando = !!(q || fp.size || fe.size);
  $('#sin-resultados').hidden = nP !== 0 || !filtrando;
  $('#contador').innerHTML = '<b>' + nP + '</b> de ' + DATA.meta.total_puntos + ' puntos' +
    (filtrando ? ' · ' + modulosVivos.size + ' de ' + DATA.meta.total_modulos + ' módulos' : '');
  $('#limpiar-todo').hidden = !filtrando;
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

  /* modo compacto */
  const bc = $('#btn-compacto');
  bc.addEventListener('click', function(){
    const on = document.body.classList.toggle('compacto');
    bc.setAttribute('aria-pressed', String(on));
    $$('.punto').forEach(function(p){
      p.classList.remove('abierto');
      const cab = $('.punto-cab', p);
      if (cab) cab.setAttribute('aria-expanded', String(!on));
    });
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

  /* menú móvil */
  const bm = $('#btn-menu');
  bm.addEventListener('click', function(){
    const sb = $('#sidebar');
    const abierto = sb.hidden;
    sb.hidden = !abierto;
    bm.setAttribute('aria-expanded', String(abierto));
  });
  $('#sidebar').addEventListener('click', function(e){
    if (e.target.closest('.nav-a') && innerWidth <= 860){
      $('#sidebar').hidden = true;
      bm.setAttribute('aria-expanded','false');
    }
  });
  function ajustaMenu(){
    const movil = innerWidth <= 860;
    $('#sidebar').hidden = movil;
    bm.setAttribute('aria-expanded', String(!movil));
  }
  ajustaMenu();
  addEventListener('resize', ajustaMenu);

  /* atajo: / enfoca el buscador */
  document.addEventListener('keydown', function(e){
    if (e.key === '/' && document.activeElement !== inp){
      e.preventDefault(); inp.focus(); inp.select();
    }
  });

  /* la barra de filtros solo se muestra mientras se recorren los módulos */
  const barraFiltros = $('#filtros');
  const secModulos = $('#modulos');
  if (secModulos && 'IntersectionObserver' in window){
    new IntersectionObserver(function(ents){
      barraFiltros.hidden = !ents[0].isIntersecting;
    }, { threshold: 0 }).observe(secModulos);
    barraFiltros.hidden = true;
  }

  $('#imprimir').addEventListener('click', function(){ print(); });

  aplicar();
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
    titulo = "%s · %s" % (meta["titulo"], meta["sujeto"])

    html = (
        "<!DOCTYPE html>\n"
        '<html lang="es">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<meta name="description" content="' + meta.get("alcance", "") + '">\n'
        "<title>" + titulo + "</title>\n"
        "<style>" + CSS + "</style>\n"
        "</head>\n<body>\n"
        '<a class="saltar" href="#contenido">Saltar al contenido</a>\n'

        '<header class="topbar">\n'
        '  <button class="btn menu-movil" id="btn-menu" aria-expanded="false" aria-controls="sidebar">'
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
        '    <div class="filtros" id="filtros" role="group" aria-label="Filtros"></div>\n'
        '    <div id="contenido"></div>\n'
        '  </main>\n'
        '</div>\n'

        '<div id="tip" role="tooltip" aria-hidden="true"></div>\n'
        '<div id="lightbox" role="dialog" aria-modal="true" aria-label="Captura ampliada">\n'
        '  <button class="cerrar" id="lb-cerrar" aria-label="Cerrar">&times;</button>\n'
        '  <img id="lb-img" alt="">\n'
        '  <figcaption id="lb-cap"></figcaption>\n'
        '</div>\n'

        '<script type="application/json" id="datos">' + json_seguro(contenido) + "</script>\n"
        '<script type="application/json" id="capturas-b64">' + json_seguro(imgs) + "</script>\n"
        "<script>" + JS + "</script>\n"
        "</body>\n</html>\n"
    )

    salida = os.path.join(AQUI, "informe.html")
    with open(salida, "w", encoding="utf-8") as fh:
        fh.write(html)

    mb = os.path.getsize(salida) / 1024 / 1024
    print("informe.html escrito —", round(mb, 2), "MB")
    print("  módulos    ", meta["total_modulos"])
    print("  puntos     ", meta["total_puntos"])
    print("  tablas     ", meta["total_tablas"])
    print("  capturas   ", len(imgs), "(", round(total_bytes / 1024 / 1024, 2), "MB en PNG )")
    print("  gráficos   ", len(contenido.get("graficos", [])))
    print("  acciones   ", meta["total_acciones"])


if __name__ == "__main__":
    main()
