# Guía de usuario de ErgoTools

Linux · 2026-10-29

Un único Guardar principal escribe todo el proyecto: trabajadores, organización, trabajos,
asignaciones, evaluaciones, PLOT y rotaciones JROT completas. Cerrar un editor conserva los
cambios aceptados sin escribir el archivo. Al cerrar o cambiar el proyecto se ofrece
Guardar/Descartar/Cancelar. Deshacer/Rehacer comparte un historial cronológico entre ventanas.
Quitar registros mediante el historial requiere confirmación; restaurar registros, editar
valores y navegar no. Los campos conservan Deshacer de escritura. Guardar conserva el
historial hasta finalizar la sesión del proyecto.

Abra un proyecto desde la terminal con `bash tools/run.sh "/ruta/proyecto.ergprj"`, o
`ergotools "/ruta/proyecto.ergprj"` en una instalación independiente. Use comillas si la ruta
contiene espacios. Los proyectos nativos cargan una evaluación disponible automáticamente; los
originales conservan el flujo de conversión; no se guarda automáticamente. Proyecto >
Proyectos recientes recuerda hasta diez aperturas correctas. Borrar historial no elimina
archivos de proyectos.

## Iniciar la aplicación integrada

En esta instalación de desarrollo para Linux, ejecute bash tools/run.sh (instalado: ergotools)
desde la carpeta del proyecto nuevo. Se abre la aplicación integrada con LiFFT, DUET, Shoulder
Tool (ST), PLOT, JROT y el avatar 3D. --disable-vtk se utiliza solo para diagnósticos sin
renderizado.

Use la ventana normalmente y amplíela cuando sea necesario. Inglés y español están en
Herramientas > Configuración. Aplicar acepta los ajustes; las preferencias personales son
compartidas inmediatamente. La precisión y las unidades predeterminadas del proyecto se
escriben con Guardar principal. La visualización nunca redondea los datos científicos
guardados. El número de tareas pertenece al trabajador/herramienta/contexto seleccionado y es
reversible.

## Proyectos y conversión de proyectos originales

Nuevo inicia un proyecto; Guardar asigna un archivo .ergprj propio a un proyecto aún no
guardado. Abrir carga automáticamente una evaluación disponible del proyecto seleccionado.
Proyectos recientes utiliza el mismo flujo de apertura. Las entradas muestran la ruta completa
para distinguir archivos con el mismo nombre en carpetas diferentes; la ayuda conserva la ruta
literal completa. Propiedades muestra los metadatos del proyecto.

Los proyectos anteriores necesitan actualizarse. Abrir explica el cambio, ofrece
Migrar/Cancelar y muestra un comando copiable para la herramienta de migración independiente.
Conserve las carpetas originales de datos e imágenes junto al descriptor hasta completar la
conversión. Los originales no se modifican. La conversión recalcula desde las tareas guardadas
e incorpora todas las imágenes de plantas al proyecto nuevo; no conserva un archivo duplicado
de resultados originales.

La copia actualizada se abre temporalmente. Use Guardar, elija un archivo .ergprj nuevo y
confirme los datos prellenados antes de cerrar; después ya no necesita carpetas originales ni
la herramienta. Si cancela o falla Guardar, la copia temporal permanece abierta para
reintentar. Cerrar solicita Guardar/Descartar/Cancelar incluso si la evaluación no tiene
cambios. Las rutas temporales no aparecen en Proyectos recientes. Guarde primero para usar
gestión/PLOT/JROT/exportación. Los errores de herramienta, archivos o datos dejan abierto el
proyecto actual.

Guardar como valida y publica el contenido aceptado en otro archivo sin modificar el original.
Copia de seguridad copia el último estado guardado con Guardar principal, sin cambiar de
proyecto. Use Guardar principal primero para incluir los cambios recientes. Ni la copia ni el
archivo del proyecto contienen el historial de Deshacer.

## Trabajadores, organización, trabajos y contexto

Trabajadores permite crear y editar registros. El ID es obligatorio; los datos personales,
laborales y medidas cm/kg o in/lb están en Datos opcionales. Agregar trabajador acepta un
registro y prepara el siguiente. Seleccionar otro trabajador o cerrar conserva los cambios
válidos en el proyecto abierto. Los datos inválidos permanecen para corregirlos o cancelar. Un
calendario de nacimiento vacío abre dieciocho años antes de hoy sin asignar una fecha.
Deshacer/Rehacer comparte el historial principal: cuatro altas se deshacen individualmente,
W04 y luego W03. Solo Guardar principal escribe el archivo.

Lugar de trabajo > Organización mantiene plantas, secciones, líneas, estaciones y turnos
independientes. Lugar de trabajo > Trabajos administra trabajos, disponibilidad y un único
conjunto actual de riesgos por trabajo. Revise y edite tareas en las pestañas, o elija un
resultado directo o una copia independiente. JROT conserva las asignaciones y usa los valores
actuales. Los registros referenciados no se pueden eliminar arbitrariamente.

El grupo Evaluación de la ventana principal selecciona una evaluación guardada del trabajador
y herramienta en planta/sección/línea/estación/turno. Una evaluación existente conserva su
asignación original después de una reasignación: sigue siendo una observación histórica, y la
nueva asignación puede tener su propia evaluación. Crear una evaluación en otra asignación no
reemplaza otras herramientas o propietarios.

El selector de trabajador, orden, primero/anterior/siguiente/último, Trabajadores, Buscar y
Transferir comparten la fila superior; las letras del apellido quedan debajo. Evaluación
independiente y el resumen de la selección están dentro del mismo grupo. Evaluación revela un
grupo compacto de ancho completo debajo del alfabeto, dentro del marco del trabajador.
Evaluación independiente está a la derecha del selector; el botón Evaluación y el resumen
ocupan la fila compacta inferior. El alfabeto queda junto al selector. La animación no mueve
ni reconstruye el alfabeto/resumen; al abrir un proyecto el estado se restaura directamente.
Sin una elección guardada comienza oculto; Guardar conserva la elección explícita de desplegar
o contraer. La navegación de trabajadores abre primero la evaluación independiente de la
herramienta activa. Si no existe, abre la primera evaluación guardada por orden alfabético de
Planta, Sección, Línea, Estación y Turno; sin datos guardados muestra una vista previa
independiente identificada, sin crear datos. Las listas incluyen solo las evaluaciones
guardadas de este trabajador y herramienta y actualizan las opciones pertinentes en cascada.
Las cantidades aparecen en los encabezados, no en los nombres guardados. Estación muestra el
porcentaje seleccionado y los colores de riesgo; otras estaciones con resultados distintos
muestran un intervalo, sin inventar promedios. Turno contiene solo su identidad. Trabajo tiene
una celda informativa separada; se vuelve selector únicamente si varios propietarios guardados
comparten estación y turno. Un borde sutil identifica el lugar abierto o el botón de
evaluación independiente; el resumen identifica la selección incluso con el contexto oculto.
Las evaluaciones de lugares disponibles siguen indicadas al abrir la independiente. El
explorador no filtra trabajadores, asigna trabajos, crea evaluaciones ni copia datos.
Transferir conserva la elección explícita de Copiar o Mover.

Use Añadir evaluación… al extremo derecho del grupo Evaluación para elegir estación y turno en
el selector jerárquico compartido. El trabajador y la herramienta corresponden a los controles
principales. Trabajo es opcional; se reutiliza una asignación existente sin cambiar su trabajo
o se crea una junto con la evaluación vacía. Si ya existe una evaluación de esta herramienta
para la asignación, se pide confirmación antes de reemplazar entradas/resultados; No es la
opción predeterminada. Sí abre 15 tareas vacías conservando la identidad de la evaluación.
Puede guardar la evaluación vacía y completarla después. Guardar escribe el proyecto;
Deshacer/Rehacer restaura la creación o el reemplazo, incluidos los resultados anteriores. Las
evaluaciones independientes y otras herramientas no cambian.

Use Transferir para elegir Copiar o Mover las herramientas seleccionadas. Se admiten tanto
evaluaciones independientes como evaluaciones de lugares de trabajo. Elija trabajador y
Evaluación independiente o estación/turno de destino. Copiar conserva el origen y crea datos
que pueden editarse de forma independiente; Mover elimina el origen seleccionado solo después
de crear correctamente el destino. Reemplazar las herramientas seleccionadas existentes
requiere confirmación; las demás herramientas y observaciones históricas se conservan. Se
conservan exactamente tareas, unidades y resultados calculados correspondientes. La operación
es atómica y utiliza Deshacer/Rehacer compartido; Guardar principal publica los cambios
aceptados. No hay un comando separado Copiar a lugares.

Cambiar herramienta, trabajador o contexto conserva los datos aceptados y el historial del
proyecto sin pedir un guardado local. Guardar principal y Guardar como incluyen los cambios
aceptados de todos los editores. Solo al salir del proyecto se pide
Guardar/Descartar/Cancelar. Las entradas numéricas inválidas deben corregirse o cancelarse
antes de aceptar el formulario. Los contextos recordados son preferencias personales.

Agregar/Eliminar están junto a los datos del trabajo. Las pestañas usan los iconos
principales; los resultados coloreados aparecen sobre Limpiar evaluación/Calcular. El panel
derecho agrupa el indicador de riesgo, la barra animada de daño, el estado y la leyenda. Datos
de tareas/Resultado directo son botones de selección. Copiar de trabajador y Copiar de trabajo
abren un buscador con ID/nombre, navegación e iniciales. Los contextos distinguen evaluaciones
independientes y lugares reales; las vistas previas muestran daño y probabilidad con colores.
Cancelar no copia datos. Deshacer/Rehacer reemplaza la acción separada de descartar cambios.

Una herramienta de trabajo vacía muestra una tarea inicial en Datos de tareas. Use + Tarea y -
Tarea para ajustar las filas; Deshacer restaura los datos/resultados eliminados. Resultado
directo no tiene tareas. Los datos completos se calculan automáticamente y Calcular sigue
disponible. Los campos numéricos, selectores descriptivos, orden de columnas, encabezados
fijos, totales y tarjetas derechas corresponden a los de la interfaz principal. Expanda la
fila del origen para inspeccionar sus tareas sin editarlas. El alfabeto ocupa el ancho del
selector y amplía la inicial al pasar el puntero. Deshacer/Rehacer usa iconos con texto, más
pequeños que en la interfaz principal; la ayuda conserva el detalle de la acción.

Use las casillas de tareas y Todas/Ninguna dentro del origen expandido para copiar las filas
seleccionadas. Copiar todas conserva los resultados exactos; una selección parcial calculada
se recalcula al copiar, incluidos sus porcentajes de aporte. Las selecciones vacías de datos o
sin calcular conservan solo los datos de entrada. El origen nunca se modifica. Los totales se
alinean con Daño; +/- Tarea está entre Limpiar y Calcular. Los nombres completos coinciden con
la interfaz principal. Cambiar de herramienta participa en Deshacer/Rehacer sin dejar datos
del proyecto pendientes de guardar.

En Resultado directo, edite el daño acumulado en la celda de color bajo la cuadrícula; la
probabilidad se deriva en la siguiente fila, sin un formulario duplicado. Los detalles para
copiar muestran solo tareas con datos, con su numeración original y controles Todas/Ninguna
junto a Tarea #. Las ventanas secundarias comparten botones contiguos de Deshacer/Rehacer con
icono y texto; la barra principal no cambia.

Buscar abre las evaluaciones guardadas de todos los trabajadores para la herramienta activa.
Filtre por ID o nombre, inicial del apellido o lugar y pulse Usar evaluación. Cerrar conserva
la evaluación actual.

## LiFFT, DUET y Shoulder Tool

Seleccione la pestaña e ingrese los datos de las tareas. LiFFT usa brazo de palanca, carga y
repeticiones; DUET usa OMNI-Res y repeticiones; ST añade dirección de tarea. Respete las
unidades indicadas. Calcular evalúa las tareas; Guardar conserva los datos y los resultados
calculados. Calcular por sí solo no los guarda.

Las filas totalmente vacías se ignoran y no hacen incompleta una evaluación con datos. Las
filas iniciadas sin valores obligatorios siguen incompletas; esos resultados incluyen solo las
filas completadas. Los valores vacíos o no disponibles no prueban riesgo cero. Los resultados
importados aparecen como Registrado; los cálculos nuevos guardados conservan su estado. Editar
un dato elimina resultados obsoletos de la vista. Los datos y resultados guardados conservan
la precisión del cálculo. Los valores predeterminados son un decimal para entradas, momentos y
probabilidad, cuatro para daño por tarea/acumulado y uno para contribución porcentual. Las
repeticiones se muestran sin decimales. Cambiar unidades o formato no redondea los valores
guardados sin editar.

Limpiar evaluación sustituye los controles Restablecer y papelera. Tras confirmar, limpia solo
los datos y resultados del trabajador, herramienta y contexto seleccionados, conservando el
número de tareas, las unidades y la asociación. Deshacer restaura los datos y resultados
anteriores; Cancelar conserva el texto pendiente. Guardar principal escribe la evaluación
vacía. Los demás trabajadores y herramientas no cambian. Buscar encuentra evaluaciones
independientes y de lugares de trabajo para la herramienta activa, con valores de riesgo en
colores. Herramientas > Configuración > Evaluación identifica proyecto, trabajador,
herramienta y lugar de trabajo o contexto independiente. Marque Cambiar número de tareas al
aplicar: cada evaluación admite de 1 a 100 filas, inicialmente 15. Aumentar añade filas
vacías; reducir conserva las primeras y pide confirmación antes de eliminar datos de las
últimas filas. Mantener el número no cambia nada. Deshacer/Rehacer restaura los datos
eliminados y sus resultados correspondientes. Guardar principal escribe los cambios aceptados.
ST conserva los significados de selectores y el orden de Tab originales; esta migración no
cambia las fórmulas científicas.

En las herramientas principales y Gestión de trabajos, los resultados se actualizan al
completar una celda (Intro, Tab o al salir de ella), si las tareas iniciadas están completas y
son válidas. Se ignoran las filas sin datos. Las tareas incompletas o inválidas borran los
totales automáticos. Calcular sigue disponible. Cada celda y su resultado comparten un paso de
Deshacer; solo Guardar escribe el proyecto.

Configuración > Apariencia > Animaciones agrupa opciones independientes para el avatar,
indicador de riesgo y daño acumulado. Son preferencias personales y no cambian los cálculos.

## Idioma, separador decimal y unidades

Configuración permite inglés/español, visualización métrica/imperial y entrada decimal con
punto/coma. No se admiten separadores de miles. Las unidades de origen de cada evaluación
permanecen asociadas a sus datos; cambiar la visualización no reinterpreta números guardados.
La estatura/peso se muestra en cm/kg o in/lb y se almacena en cm/kg.

Los CSV mantienen identificadores de columna en inglés y decimales con punto
independientemente del idioma. Se conservan las etiquetas de unidades registradas y la
precisión guardada. Las coordenadas de PLOT son píxeles de imagen en ambos sistemas.

## PLOT: filtros, plano y gráficos

Abra PLOT desde la barra principal. Seleccione herramienta, lugar, vista de riesgo y filtros
demográficos opcionales, y aplique los filtros. El plano y los resúmenes usan evaluaciones
guardadas y datos de riesgo laboral aprobados. Revise las vistas Individual, Trabajo y
Comparación, los datos faltantes y los detalles destacados.

Abrir importa y acepta la imagen de planta en el proyecto abierto. Los movimientos completados
y los cambios válidos de coordenadas, escala, visibilidad, inclusión y bloqueo se conservan
sin controles locales de Guardar. Aplicar a todos es una edición de lote validada. Cerrar PLOT
conserva los cambios; Guardar principal escribe imagen y geometría junto con el resto del
proyecto. Zoom, opacidad, capturas y exportaciones de gráficos/CSV mantienen sus funciones
independientes.

Use exportación CSV para los resultados guardados de trabajadores con los filtros aplicados.
Los gráficos de resumen tienen configuración y exportación de imagen propias. No se habilitan
el experimento D3 oculto ni los metadatos de transformación de planta sin uso.

Individual muestra los símbolos de las evaluaciones de trabajadores. Trabajo muestra un
cuadrado con el riesgo del trabajo en cada asignación visible y posicionada: los mismos
cuadrados, tamaños y posiciones de Comparación, sin el símbolo individual. Las etiquetas
identifican trabajos; un cuadrado gris discontinuo indica que falta un resultado utilizable.
Un trabajo puede aparecer en varias asignaciones. Los gráficos del ámbito y el promedio
inferior de trabajos conservan su agregación por ubicaciones; no promedian los cuadrados
repetidos del mapa. Pulse el selector del resumen para buscar por jerarquía, ID o nombre de
trabajador o trabajo dentro de los filtros aplicados. Elegir una hoja selecciona esa
asignación exacta; Cancelar conserva la selección.

Seleccionar, Acercar, Alejar y Desplazar son herramientas persistentes. El primer botón
restaura la selección y el movimiento normal de marcadores. Las lupas siguen activas entre
clics y Desplazar entre arrastres. Escape o clic derecho también restauran la selección. No
hay instrucciones superpuestas al plano. La imagen y todos sus símbolos se amplían juntos
conservando sus anclajes originales. La rueda, los arrastres completos del plano, Ajustar
imagen y la opacidad de marcadores comparten Deshacer/Rehacer. Elegir herramientas y
redimensionar automáticamente no añade pasos. Este historial dura durante la sesión del
proyecto y no escribe geometría ni requiere Guardar. El plano no tiene barras de
desplazamiento. El zoom máximo es el 400% de la imagen ajustada. Alejar y Desplazar se
desactivan al 100%; si estaban activos, se restaura el cursor normal. Las ayudas de ambas
lupas muestran el zoom actual y el máximo, también después de Deshacer/Rehacer. Los símbolos
individuales tienen un contorno oscuro. Localizar centra la vista ampliada en el trabajador
seleccionado, respetando los bordes de la imagen y conservando el zoom. Este desplazamiento
permite Deshacer/Rehacer sin cambiar la geometría de las asignaciones.

Resumen de trabajos incluye Localizar debajo de Riesgo actual del trabajo; centra y resalta el
cuadrado seleccionado conservando el zoom. El gráfico muestra una barra de riesgo por trabajo,
sin sufijos de cantidad de ubicaciones. Cuadrados en el mapa cuenta las repeticiones visibles
del trabajo seleccionado en la vista aplicada. Es distinto del número de ubicaciones y del
resumen ponderado existente. El registro del trabajo no contiene posición ni escala;
pertenecen al marcador de la asignación del trabajador, con posiciones iniciales heredables de
la estación.

En la vista integrada de trabajos, Cancelar movimiento restaura el último movimiento aceptado
del cuadrado seleccionado en la vista actual. La restauración permite Deshacer/Rehacer. Las
coordenadas pendientes se descartan conservando la posición aceptada. El panel informa del
resultado; el historial general sigue disponible al cambiar de vista o reabrir la ventana.
Guardar principal escribe los cambios de geometría aceptados.

## JROT: rotaciones y optimización

Abra JROT, seleccione o cree una rotación, defina su ámbito organizacional/lugar y complete
trabajadores y trabajos de cada bloque. Defina los valores actuales de riesgo en Trabajos. Las
rotaciones guardadas conservan sus asignaciones de trabajadores/trabajos y usan los valores
actuales. Cambiar valores numéricos relevantes invalida la optimización anterior; vuelva a
optimizar explícitamente cuando corresponda.

Optimizar actual usa CBC para la herramienta elegida; Optimizar todas usa HiGHS para LiFFT,
DUET y ST en conjunto. No se usa GLPK. Ingrese un límite válido en minutos. Revise la vista
previa/comparación y aplique explícitamente Usar como actual/Aplicar antes de Guardar. La
vista previa no reemplaza la rotación guardada. Cancelar detiene una optimización sin
aplicarla.

JROT comparte el historial cronológico de Deshacer/Rehacer del proyecto. La cuadrícula
parcial, el ID, los asignaciones de trabajadores/trabajos y el ámbito aceptado sobreviven al
cerrar y reabrir la ventana. Guardar principal o Guardar como requiere completar o cancelar
explícitamente una rotación ingresada; nunca se omiten filas incompletas. Los esquemas
completos se escriben junto con el proyecto. Las vistas previas del optimizador requieren
Aplicar/Usar como actual, y el historial permanece bloqueado mientras el solver trabaja.

## Copiar/Mover, exportar y deshacer

Transferir selecciona herramientas actuales guardadas de la asignación de origen y un
trabajador/lugar/turno de destino exacto. Copiar conserva el origen; Mover elimina solo las
versiones actuales seleccionadas tras completar toda la transferencia. Ambos conservan datos,
resultados, unidades y estado registrado/calculado exactos. Los datos seleccionados existentes
en destino requieren confirmación explícita para reemplazarlos; No es la opción inicial. El
destino idéntico al origen se bloquea. Otras evaluaciones, valores de trabajo y propietarios
permanecen intactos.

Copiar/Mover usa datos aceptados y sus resultados coincidentes, incluidos cambios de la sesión
aún sin guardar. Las entradas inválidas sin aceptar no se copian. Se conserva la confirmación
explícita de la transferencia, pero no se pide otro guardado del proyecto. Guardar principal
publica los registros juntos. Exportar CSV lee los datos aceptados del proyecto abierto sin
guardarlo.

Deshacer/Rehacer principal y de los editores comparte un historial cronológico. Agregar o
editar un trabajador es un paso; cerrar su ventana no agrega pasos. Quitar registros mediante
el historial los identifica y requiere confirmación, con Cancelar predeterminado. Cancelar no
consume el paso. Restaurar registros, editar valores y navegar no requiere esa advertencia.
Los campos conservan Deshacer de escritura. Guardar conserva el historial; cerrar o cambiar el
proyecto lo finaliza.

## Copias de seguridad, recuperación y límites

Antes de recuperar, conserve otra copia del archivo .ergprj actual. Abra una copia de
seguridad con otro nombre y revise trabajador/contexto, las tres herramientas,
imagen/marcadores de PLOT y rotaciones JROT. Guardar como puede convertirla en su copia de
trabajo. Los proyectos nuevos contienen todas las imágenes y los datos nativos en un archivo,
con un resultado calculado por versión y sin un archivo original oculto; los XML necesitan sus
carpetas asociadas hasta la conversión.

Un guardado fallido conserva el borrador para corregir o reintentar. No suponga que un error
guardó datos; abra otra copia para inspeccionar lo persistido. Las copias no incluyen
ediciones sin guardar ni historiales de Deshacer. Si falla Abrir/conversión, conserve
originales y detalles del error; no modifique filas arbitrariamente para evitar validaciones.

Este hito se valida en Linux XCB con las versiones exactas aprobadas. La aceptación nativa en
Windows/macOS queda pendiente. Los cálculos conservan el comportamiento original, incluidas
las convenciones documentadas de momento métrico y dirección ST; la migración no es una
revalidación científica. Los prototipos antropométricos ocultos permanecen solo en la
referencia original externa, no dentro de los proyectos nativos ni como herramientas
validadas.

El avatar colorea todas las regiones con evaluación para el trabajador y la
asignación/contexto exactos; el panel lateral y el enfoque siguen la herramienta activa.

Deshacer y Rehacer son las dos primeras acciones de la barra principal. PLOT y JROT ofrecen
Deshacer/Rehacer al extremo derecho de su fila de título, con el mismo historial y los mismos
atajos. Se eliminaron su menú Editar y la barra de historial independiente. Pulse una región
coloreada del avatar para seleccionar LiFFT (zona lumbar), DUET (antebrazos/manos) o ST
(hombros). Las zonas neutras y el fondo no seleccionan herramientas; arrastrar sigue rotando
el modelo. La selección conserva contexto y ediciones y respeta la preferencia de animación de
cámara.

La barra principal agrupa Deshacer/Rehacer, Nuevo/Abrir/Guardar, PLOT/JROT y
Organización/Trabajos. Exportar está en Proyecto; Lugar de trabajo contiene Organización y
Trabajos. Los diálogos de proyecto ofrecen solo .ergprj; una base SQLite cualquiera no es un
proyecto ErgoTools válido. Propiedades muestra los detalles de un proyecto guardado y no está
disponible antes de guardarlo.

La navegación aceptada entre herramientas, trabajadores y contextos se ordena con las
ediciones en el historial compartido. Las elecciones válidas DUET/ST y las entradas numéricas
siguen siendo reversibles al cambiar de trabajador o contexto. Los datos inválidos permanecen
para corregirlos. El desplazamiento de las tareas es estado visual transitorio. Guardar
principal escribe todo el proyecto aceptado y conserva la rama de Deshacer/Rehacer.

Propiedades del proyecto muestra solo los datos aplicables al archivo único: nombre del
proyecto, archivo, ubicación completa, fecha/hora de creación registrada, idioma del proyecto
y sistema de medidas, además de la descripción completa desplazable. Los valores son de solo
lectura y se pueden copiar; el diálogo se puede ampliar. Los metadatos opcionales ausentes
indican Sin registro. Ya no se muestran carpetas antiguas de base de datos, imágenes o datos.

Deshacer/Rehacer una edición de evaluación restaura el desplazamiento horizontal y vertical
capturado cuando comenzó la edición. En cuadrículas largas, editar la tarea 1 y deshacer
conserva esa ubicación; las ediciones intermedias vuelven a su ubicación aunque se haya
desplazado después. Se retira el foco de los controles anteriores antes de reconstruir la
cuadrícula y el rango de desplazamiento se actualiza al cambiar el número de filas. Este
estado visual dura la sesión y nunca se guarda como dato científico.

Cambiar y Quitar asignaciones conserva la propiedad histórica de las evaluaciones. Agregar,
Cambiar y Quitar acepta primero los datos válidos del trabajador y sus listas en la sesión,
sin Guardar local. La clasificación se limita a trabajos disponibles en ese lugar y turno, y
se rechazan destinos ocupados. Guardar principal escribe estos cambios. Puestos cuenta
ubicaciones de estación y turno, no secciones.

Se eliminaron la creación de versiones de evaluación y la selección de versión vigente.
Proyecto conserva Nueva evaluación y Contexto de evaluación. Cada asignación de trabajo del
trabajador y herramienta ergonómica admite una sola evaluación guardada; Guardar actualiza esa
evaluación. No existen acciones Nueva versión vacía ni Definir versión vigente. Reasignar al
trabajador a otro trabajo crea otra asignación, no otra versión de la evaluación. Los datos y
resultados reales conservan su asignación original.

Los proyectos de prueba actuales en formato 19 están en
test_projects/native/comparative_risk_test.ergprj y
test_projects/native/integrated_test.ergprj. Los archivos de prueba habituales se han
actualizado al formato 19 y se abren directamente sin conversión. Abrir un proyecto nativo
anterior ofrece la migración externa existente y crea otro archivo en formato 19. El conversor
elimina únicamente un borrador LiFFT duplicado comprobado como vacío, sin valores ingresados
ni resultado; si hay evaluaciones duplicadas con datos, detiene la conversión y solicita una
decisión específica. Nunca elige silenciosamente qué evaluación real descartar.

Use Transferir para elegir Copiar o Mover las herramientas seleccionadas. Se admiten tanto
evaluaciones independientes como evaluaciones de lugares de trabajo. Elija trabajador y
Evaluación independiente o estación/turno de destino. Copiar conserva el origen y crea datos
que pueden editarse de forma independiente; Mover elimina el origen seleccionado solo después
de crear correctamente el destino. Reemplazar las herramientas seleccionadas existentes
requiere confirmación; las demás herramientas y observaciones históricas se conservan. Se
conservan exactamente tareas, unidades y resultados calculados correspondientes. La operación
es atómica y utiliza Deshacer/Rehacer compartido; Guardar principal publica los cambios
aceptados. No hay un comando separado Copiar a lugares.

La evaluación principal y todos los indicadores de riesgo de PLOT comparten marcas y etiquetas
opcionales en los límites de riesgo (0, 25, 37,5, 50 y 100). Haga clic derecho en cualquier
indicador para cambiar su visibilidad o separación al instante, o use Herramientas >
Configuración > Apariencia > Indicadores de riesgo y Aplicar. Configuración tiene un árbol de
secciones para General, Apariencia, Proyecto y Evaluación; cambiar de sección conserva los
ajustes pendientes. El intervalo inicial es de 10 puntos porcentuales; hay opciones de 5, 20 y
25, y el intervalo personalizado admite 1–100. Desactive ambas opciones de visibilidad para
recuperar el indicador sin marcas. Estas preferencias personales se conservan al reiniciar y
no cambian los cálculos ni los datos del proyecto. Cancelar en Configuración conserva la
apariencia actual. Los formularios y las solicitudes de entrada de ErgoTools usan el tema de
la aplicación; los selectores de archivos, colores y fuentes conservan la apariencia
predeterminada del sistema.

Las horas de inicio y fin usan controles estándar de hora en formato de 24 horas HH:mm
(00:00-23:59). Escriba 8:30 o 0830 para ingresar 08:30; al escribir 8: se seleccionan los
minutos. También puede usar las flechas. Sin especificar es distinto de medianoche (00:00);
Ctrl+A y Suprimir borra una hora opcional. En Turnos, el fin del mismo día debe ser posterior
al inicio. Marque Termina al día siguiente para un turno nocturno como 22:00-06:00. Cada par
completo representa un intervalo diario de hasta 24 horas; horas iguales requieren esa opción
para un turno de 24 horas. Los turnos nocturnos existentes se abren con la opción marcada. La
opción se deduce del orden de las horas y no agrega un campo al proyecto. Los cambios válidos
en los datos de una organización o turno habilitan Deshacer de inmediato. Al pulsarlo se
acepta y revierte la edición pendiente del registro; Deshacer con el teclado dentro de un
campo de texto sigue siendo local. Cerrar o cambiar de registro acepta los cambios válidos en
el proyecto privado; Guardar en la ventana principal escribe el archivo. La organización
conserva los datos opcionales abiertos o cerrados y las ramas de ubicaciones expandidas o
contraídas al editar, eliminar y deshacer/rehacer. Deshacer vuelve a seleccionar un registro
eliminado y restaurado, salvo que haya seleccionado otro registro después. Estas preferencias
de vista duran mientras el diálogo está abierto y no agregan cambios al proyecto.

Los turnos describen un horario recurrente, no un día específico. Incidentes informados y
Eventos de riesgo ergonómico se han eliminado del formulario y del almacenamiento. La
conversión de proyectos anteriores elimina esos atributos de turno y conserva las entradas y
los resultados de evaluación exactos.

Las fechas de apertura y creación usan calendarios opcionales. Un calendario vacío comienza en
hoy, pero no asigna una fecha hasta elegirla; Ctrl+A y Supr la borran. La duración operativa
de Planta usa horas y minutos de 0 a 24 horas, incluido un día completo; se almacena en horas
decimales. Turnos en uso muestra los turnos distintos utilizados por trabajos activos o
asignaciones de trabajadores en esa planta, incluidos los trabajadores sin trabajo
clasificado. Los turnos definidos sin uso no cuentan. Se eliminaron el recuento editable de
Planta y los campos de Estación descripción de tarea, equipo, riesgo ergonómico, indicador de
rendimiento, consumo eléctrico y materiales, del formulario y del almacenamiento.

Las asignaciones de lugares de trabajo son distintas de la asociación de evaluaciones. En
Gestión de trabajadores, abra Lugares de trabajo y elija Asignar lugar…. Seleccione una
estación en la jerarquía, un turno y un trabajo opcional. Sin trabajo es válido; el resumen
cuenta por separado las asignaciones y las que tienen trabajo. Cambiar utiliza el mismo
selector y conserva los propietarios históricos de evaluaciones. Use Transferir para elegir
Copiar o Mover las herramientas seleccionadas. Se admiten tanto evaluaciones independientes
como evaluaciones de lugares de trabajo. Elija trabajador y Evaluación independiente o
estación/turno de destino. Copiar conserva el origen y crea datos que pueden editarse de forma
independiente; Mover elimina el origen seleccionado solo después de crear correctamente el
destino. Reemplazar las herramientas seleccionadas existentes requiere confirmación; las demás
herramientas y observaciones históricas se conservan. Se conservan exactamente tareas,
unidades y resultados calculados correspondientes. La operación es atómica y utiliza
Deshacer/Rehacer compartido; Guardar principal publica los cambios aceptados. No hay un
comando separado Copiar a lugares.

La tabla Lugares de trabajo ajusta cada columna de ubicación a sus valores completos y
encabezado. La columna de trabajo opcional se ajusta a sus opciones, incluida la flecha y los
márgenes del selector, y mantiene un ancho útil cuando está vacía. Las barras de
desplazamiento horizontal y vertical aparecen solo cuando las columnas o filas superan el
espacio disponible. Los valores largos permanecen en una línea; las columnas de estación o
turno no se ensanchan solo porque el nombre de una planta sea largo.

Cuando caben las columnas del lugar de trabajo, la columna de trabajo opcional utiliza el
ancho restante y sus selectores ocupan ese espacio. Al cambiar el tamaño de la ventana se
recalcula la distribución; los valores largos conservan un ancho legible y usan desplazamiento
horizontal cuando hace falta. La altura de fila y el ancho de Acciones incluyen los controles
y márgenes para mostrar completos los bordes de ambos botones. Al pasar el puntero sobre un
valor se muestra su columna y texto completo; sobre un encabezado, su significado; sobre el
selector de trabajo, la opción actual y su ayuda; y sobre una acción, su operación. El espacio
vacío no muestra una ayuda genérica de trabajo.

## Valores del trabajo, calculadoras y copias de evaluaciones

Cada trabajo tiene un conjunto actual independiente de valores LiFFT, DUET y ST. Seleccione un
trabajo a la izquierda para revisar sus tareas en las pestañas de herramientas. Datos de
tareas es la opción inicial para una herramienta vacía; se muestra una tarea vacía inicial sin
crear datos guardados. Use + Tarea y - Tarea para ajustar la tabla. Los datos completos se
calculan automáticamente; Calcular sigue disponible. El indicador y la leyenda de rangos de
riesgo siguen la herramienta seleccionada; editar datos borra los resultados anteriores.
Resultado directo permite ingresar un daño acumulado y derivar su probabilidad sin tareas
registradas. Copiar evaluación selecciona una evaluación independiente o asignada de un
trabajador. Copiar de trabajo copia la herramienta seleccionada desde otro trabajo. Ambas
copias conservan los datos, unidades y resultados exactos y se pueden editar de forma
independiente. Reemplazar valores o quitar tareas requiere confirmación. Puestos administra
las ubicaciones físicas del trabajo por separado. Cerrar conserva las ediciones válidas;
Guardar principal escribe el proyecto. El mismo historial Deshacer/Rehacer restaura cambios,
copias y tareas eliminadas. Las tareas sin calcular se conservan al guardar y abrir, y no
están disponibles para PLOT/JROT hasta calcularlas.

El selector Añadir evaluación identifica las evaluaciones guardadas y sus porcentajes con los
colores de riesgo, incluso en la fila seleccionada. Guardada sin calcular, Nueva e Histórica
tienen etiquetas distintas. Se actualizan según el turno y la herramienta/trabajador actuales.
Las observaciones históricas se conservan.

## Buscar, eliminar y redimensionar evaluaciones

Buscar muestra las evaluaciones guardadas de la herramienta activa. Filtre por ID/nombre,
inicial o lugar de trabajo. Las independientes tienen una rama propia; las observaciones
históricas se seleccionan individualmente. Los porcentajes guardados conservan sus colores al
seleccionar filas. Sin calcular indica datos existentes sin resultado guardado.

Eliminar evaluación…, junto a Agregar, muestra solo las evaluaciones existentes del trabajador
y herramienta seleccionados. La confirmación elimina las tareas y resultados elegidos,
conserva el trabajador, trabajo y asignación, y actualiza los selectores de ubicación.
Deshacer restaura los datos y resultados exactos; Guardar en la ventana principal escribe la
eliminación. Cancelar/No no cambia nada. Limpiar evaluación conserva la evaluación y sus
filas, vaciando las entradas.

+ Tarea / - Tarea, entre Limpiar evaluación y Calcular, agrega una fila vacía o elimina la
última. Se permiten entre 1 y 100 tareas; eliminar datos ingresados requiere confirmación.
Deshacer restaura filas y resultados. Se muestra la nueva fila para ingresar datos. Las demás
herramientas, trabajadores y ubicaciones son independientes.

Transferir muestra valores de origen en colores y columnas por herramienta en las estaciones
de destino, según trabajador y turno seleccionados. Un guion indica ausencia de evaluación;
Sin calcular identifica entradas existentes. Seleccione la primera fila Evaluación
independiente para crear las herramientas faltantes sin estación/turno. El destino puede
pertenecer al mismo trabajador o a otro. Las herramientas seleccionadas ya existentes
requieren confirmación antes de reemplazarlas; No no cambia nada. Se bloquea el destino
idéntico al origen. Deshacer restaura tanto el destino previo como los datos movidos; Guardar
principal escribe la transferencia. Tras Mover la evaluación visible se abre su destino;
Copiar conserva el origen en vista. Buscar muestra primero las evaluaciones independientes y
luego todos los lugares.
