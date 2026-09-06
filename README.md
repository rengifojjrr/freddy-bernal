# Diagnóstico Digital 360 — informe HTML interactivo

Hay dos formas del mismo informe, generadas en la misma pasada:

- **`informe.html`** — archivo único autocontenido. Se abre haciendo doble clic:
  sin servidor, sin conexión y sin dependencias. Unos 5 MB, porque las diez
  capturas van incrustadas en base64.
- **`informe_artifact.html`** — el mismo contenido sin `<!doctype>`, `<html>`,
  `<head>` ni `<body>`, porque el servicio de publicación aporta ese envoltorio.
  Es el que se publica para obtener un enlace compartible.

Publicado en: <https://claude.ai/code/artifact/a4d342eb-a940-4d8e-9986-812ba9a5c3c4>

La página publicada es **privada** hasta que se comparta desde su propio menú.
Para sacar un PDF conviene usar el archivo local: dentro de un marco publicado,
el botón de imprimir depende de lo que permita el navegador anfitrión.

## Qué contiene

21 módulos · 267 puntos · 69 tablas de datos · 10 capturas · 10 gráficos ·
47 acciones en la hoja de ruta a 90 días.

Todo el texto es literal respecto de los documentos originales. Nada se ha
reescrito, resumido ni acortado.

## Cómo se construye

La carpeta no traía `contenido.json` ni `capturas/`: solo el informe en Word y
la matriz en Excel. Toda la fuente de verdad se deriva de esos dos archivos.

```
informe.docx  ─┐
               ├─► extraer_contenido.py ─► contenido.json + capturas/*.png
matriz.xlsx   ─┘

graficos_png/*.png ─► muestrear_colores.py ─► color real de cada barra
                                               (escrito en graficos.json)

contenido.json + capturas/ + graficos.json ─► build.py ─► informe.html
```

Para rehacerlo:

```sh
./regenerar.sh          # solo el HTML, a partir del contenido ya extraído
./regenerar.sh --todo   # vuelve a extraerlo todo desde el DOCX y el XLSX
```

Los scripts usan solo la biblioteca estándar de Python, salvo
`muestrear_colores.py`, que necesita Pillow para leer los PNG.

### `extraer_contenido.py`

Transcribe el DOCX y el XLSX. No interpreta el contenido: solo decide la
estructura, y para ello se apoya en marcas que el propio documento ya trae.

Un detalle que importa: las entradillas en versalitas —`HALLAZGO CENTRAL.`,
`EL DATO MÁS IMPORTANTE:`, `ADVERTENCIA —`— **no se detectan con una expresión
regular**. Se probó, y el patrón «mayúsculas seguidas de punto, dos puntos o
raya» acierta en 312 párrafos pero falla en 84: se salta 67 entradillas reales
y marca 11 que no lo son. El DOCX marca esas aperturas como texto en negrita,
que es el dato fiable, y de ahí salen. Por eso cada párrafo de hallazgo en el
JSON es `{t, lead}`: `t` es el párrafo íntegro y literal, `lead` es el prefijo
exacto que va en negrita, o cadena vacía si no hay ninguno.

### Los gráficos

Los diez gráficos del informe original **solo existen como PNG rasterizado**.
Ni el DOCX ni el XLSX contienen sus series como números: la hoja «9. Gráficos»
de la matriz son diez títulos y diez imágenes incrustadas.

Las cifras se recuperaron leyendo cada imagen y después se verificaron, una a
una, contra el texto del informe y contra las hojas de datos de la matriz.
`graficos_trazabilidad.json` guarda esa comprobación: para cada cifra, la cita
textual que la respalda, o la constancia explícita de que solo consta en la
imagen. **Conviene revisarlo antes de entregar el informe al cliente.**

Los colores no se dedujeron ni se clasificaron a ojo: `muestrear_colores.py`
los mide sobre el PNG original, detecta cada barra por su geometría y asigna el
color de la paleta más cercano. El emparejamiento se autocomprueba —el orden de
anchuras de las barras detectadas tiene que seguir al orden de los valores— y
avisa en vez de adivinar cuando algo no cuadra.

Todos los gráficos se dibujan como SVG en línea, generados a mano. Sin
librerías. `g4` va en columnas verticales con la banda de referencia detrás,
como en la figura original, y con su propia escala por panel: las tres métricas
no son comparables entre sí. El único que se recalcula en el navegador es `g9`,
que cuenta las prioridades de los 267 puntos.

## Lo que hace el informe

- **Buscador global** sobre enunciado, hallazgo, tabla y acción de los 267
  puntos. Normaliza acentos, resalta las coincidencias y dice cuántos puntos y
  cuántos módulos quedan.
- **Filtros** por prioridad y por tipo de evidencia, combinables entre sí y con
  el buscador.
- **Modo compacto**: colapsa los 267 puntos a su encabezado y sus distintivos.
- **Enlaces profundos**: cada punto tiene su `id` (`#m03-p13`) y el hash de la
  URL se sincroniza al navegar.
- **Hoja de ruta** con casilla por acción y barra de progreso por bloque y
  global. El estado se guarda en `localStorage` dentro de `try/catch`: si el
  almacenamiento no está disponible, el informe funciona igual.
- **Modo oscuro** con su propio juego de tonos. Respeta `prefers-color-scheme`
  y el conmutador manual gana sobre la preferencia del sistema.
- **Impresión**: oculta navegación y controles, despliega todo el contenido y
  evita cortar tablas y figuras.

## Comprobado

En Chromium, sobre `file://`, sin servidor:

- 267 puntos, 21 módulos, 69 tablas y 10 capturas contados en el DOM.
- Los 10 gráficos dibujan; 156 barras en total.
- Buscador y filtros se combinan y el contador cuadra en los tres casos.
- Con `localStorage` inutilizable —lanzando `SecurityError` al acceder— no hay
  ni un error en consola y todo sigue funcionando.
- A 375 px de ancho el cuerpo no hace scroll horizontal.
- En modo oscuro no queda texto por debajo del umbral de contraste.
- En vista de impresión se ocultan barra y navegación y se expanden los 267
  cuerpos, incluso partiendo del modo compacto.

## Archivos

| | |
|---|---|
| `informe.html` | el entregable, para abrir con doble clic |
| `informe_artifact.html` | el mismo informe listo para publicar (regenerable) |
| `contenido.json` | fuente de verdad, derivada del DOCX y el XLSX |
| `graficos.json` | series de los diez gráficos, con el color medido |
| `graficos_trazabilidad.json` | de dónde sale cada cifra de cada gráfico |
| `capturas/` | las diez figuras en PNG |
| `extraer_contenido.py` | DOCX + XLSX → `contenido.json` |
| `normalizar_graficos.py` | salida del flujo de extracción → `graficos.json` |
| `muestrear_colores.py` | mide el color real de cada barra en los PNG |
| `build.py` | → `informe.html` |
| `regenerar.sh` | ejecuta la cadena entera |
