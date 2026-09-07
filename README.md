# Diagnóstico Digital 360 — informe HTML interactivo

## Dónde está

**Web pública:** <https://rengifojjrr.github.io/freddy-bernal/>
Abre en cualquier dispositivo, sin instalar nada.

**Página privada:** <https://claude.ai/code/artifact/a4d342eb-a940-4d8e-9986-812ba9a5c3c4>
Solo la ve quien tenga el enlace y esté autorizado.

> ⚠️ El repositorio es **público**. Eso incluye `informe.docx` y `matriz.xlsx`,
> que cualquiera puede descargar. Si el informe no debe ser público, hay que
> poner el repositorio en privado — y entonces GitHub Pages deja de servirlo.

## Tres formas del mismo informe

Las tres se generan en la misma pasada de `build.py`, del mismo contenido:

| archivo | para qué | peso |
|---|---|---|
| `index.html` | GitHub Pages. Solo lectura. Las capturas van aparte | 0,58 MB (~184 KB comprimido) |
| `informe.html` | doble clic, sin servidor ni conexión. Todo incrustado | 4,9 MB |
| `informe_artifact.html` | copia privada en claude.ai, solo lectura | 4,9 MB |

El editor va en `index.html` y en `informe.html`. En el artifact de claude.ai
**no**: allí la política de seguridad de la página bloquea las llamadas a
servidores externos, así que esa copia es de solo lectura a propósito.

Para sacar un PDF conviene usar `informe.html`: tiene la hoja de impresión
probada y no depende de lo que permita el navegador anfitrión.

## Edición

**Cualquiera con el enlace de edición puede editar. No hace falta cuenta.**

| enlace | quién | qué puede |
|---|---|---|
| `…/freddy-bernal/` | cualquiera | leer |
| `…/freddy-bernal/#k=TOKEN` | quien tenga el enlace | escribir, formatear, subir imágenes |

Al abrir el enlace de edición, la página guarda el token y **lo borra de la
barra de direcciones**, para que no acabe en el historial ni en una captura.

Queda recordado en ese navegador: a partir de ahí, **el enlace normal también
abre en modo editor en ese equipo**. Por eso la barra superior muestra un
distintivo «Editor», y la barra de edición trae **Salir del modo editor**, que
olvida el token y devuelve ese navegador a solo lectura. En un navegador que
nunca ha visto el enlace de edición, el enlace normal es solo lectura y el
botón de editar ni aparece.

Qué se puede hacer:

- **Texto**: todo el informe. Portada, resumen ejecutivo, cómo leer, el
  resumen de cada módulo, el hallazgo y la acción de los 267 puntos, las notas
  del equipo por módulo, la descripción y el detalle de las 47 acciones del
  plan, la fase de profundización, las fuentes y la nota metodológica.
  **651 regiones.**
- **Deshacer y rehacer**: los dos primeros botones de la cinta, y Ctrl+Z /
  Ctrl+Y (también Ctrl+Mayús+Z). Ver más abajo.
- **Formato**: negrita, cursiva, subrayado, tachado; subtítulo, párrafo normal
  y cita; lista de puntos y numerada; más y menos sangría; alineación;
  color de texto y resaltado con la paleta del informe; enlaces; quitar el
  formato. Los botones se encienden según dónde esté el cursor.
- **Dos sitios para lo mismo**: una cinta fija abajo, siempre a la vista
  mientras se edita, y —en pantalla ancha— una barra que sale sobre el texto
  seleccionado. En el móvil la cinta se desplaza a lo ancho con el dedo y la
  barra flotante se apaga, porque pelea con el menú de selección del sistema.
- **Imágenes**: botón, **arrastrar y soltar**, o **pegar una captura** con
  Ctrl+V. Se reducen en el navegador antes de subirlas.
- **Guardado**: automático 1,6 s tras dejar de escribir, más botón y Ctrl+S,
  con el estado siempre visible y aviso al salir con cambios pendientes.
- **Descargar**: exporta todas las ediciones a un JSON.

### Deshacer: qué alcanza y qué no

El deshacer del navegador no servía. Se pierde en cuanto la página reescribe
un bloque por su cuenta —al llegar un cambio de otra persona, al insertar una
imagen, al devolver un bloque con ↺— y no cruza de un bloque a otro. Así que
la historia se lleva aparte: **una sola línea de tiempo para todo el informe**,
con el bloque, el antes, el después y dónde estaba el cursor.

- Va **de un bloque a otro**: si se escribe en el M03 y luego en el M05, dos
  Ctrl+Z devuelven primero el M05 y después el M03, y el cursor viaja hasta
  allí. Si el punto está plegado, se abre.
- La escritura seguida se junta en un paso, como en un procesador de texto:
  hay corte al hacer una pausa, al pulsar Intro, al salir del bloque y antes
  de cualquier botón de formato.
- Entran también la **imagen insertada**, el **pegado** y el propio **↺**.
- Guarda **150 pasos**. Escribir algo nuevo después de deshacer borra lo que
  quedaba por rehacer, como es costumbre.
- **Se pierde al recargar la página.** La historia vive en memoria; lo escrito
  ya está guardado en el servidor. Para volver atrás después de recargar está
  ↺, que devuelve un bloque entero a su texto del informe.
- **Deshacer hasta el principio borra la fila del servidor**: el bloque no se
  queda guardado como una copia idéntica del original, vuelve a estar limpio.
- Con dos personas a la vez, deshacer restaura la foto del bloque tal y como
  estaba: puede pisar lo que la otra acabara de escribir en ese mismo bloque.

En el móvil, entrar en edición despliega los puntos plegados —no se puede
editar lo que no se ve— y al salir vuelve el modo compacto.

### El original no se toca

El texto del informe sigue siendo el JSON incrustado, literal. Lo que se
escribe se guarda **aparte**. Cada región editada lleva un filo verde —que se
apaga solo si el bloque vuelve a su texto de partida— y puede devolverse a su
original con ↺. El buscador reindexa lo escrito.

### Cómo está montado

```
página estática (GitHub Pages)
   │  lee     →  REST con la clave pública  →  fb360_ediciones (solo SELECT)
   └─ escribe →  función fb360              →  valida el token → escribe
```

Las tablas **no admiten escritura directa**: no tienen políticas de escritura,
así que la clave pública no puede insertar ni modificar nada. Todo lo que se
guarda pasa por la función de servidor, que compara el token contra
`fb360_config` —una tabla sin políticas, que solo el servidor puede leer—
antes de tocar nada. Las imágenes se suben por la misma vía a un depósito
público; subir directamente al depósito también está cerrado.

Comprobado: escritura anónima a la tabla → rechazada por RLS; lectura del
token con la clave pública → vacío; subida directa al depósito → 403; token
equivocado → 401.

### Cambiar el token (revocar los enlaces repartidos)

```sql
update public.fb360_config set token = 'nuevo-token-aqui' where id = 1;
```

Todos los enlaces antiguos dejan de editar al instante. Quien los tuviera
guardados pasa a modo lectura con un aviso.

> El enlace de edición es una llave: quien lo reciba puede editar, y puede
> reenviarlo. No hay forma de saber quién escribió qué. Si eso importa, hay
> que cambiar a cuentas con nombre — es otro trabajo.

## Qué contiene## Qué contiene

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

## En el teléfono

Con 267 puntos densos, un móvil necesita otra cosa que un escritorio encogido:

- **Los puntos llegan plegados.** Un módulo se recorre de un vistazo: enunciado
  y distintivos. Se toca uno y se abre. En pantalla ancha siguen desplegados.
- **Los 37 puntos críticos llevan un filo rojo** en el borde de la tarjeta: se
  localizan sin leer.
- **Los filtros suben desde abajo** en una hoja, en vez de comerse tres filas de
  pantalla. El botón muestra cuántos hay puestos.
- **El índice baja como panel**, con los controles de tema, compacto e impresión
  dentro.
- **Pasos entre módulos** al final de cada uno, para no volver al índice.
- Campo de búsqueda a 16 px, que es lo que evita que Safari amplíe la página al
  tocarlo.

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
- **La posición de lectura se conserva** al buscar y al limpiar: filtrar encoge
  el documento y el navegador recorta el desplazamiento, así que se ancla a un
  elemento y se devuelve.

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
| `index.html` | el sitio de GitHub Pages |
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
