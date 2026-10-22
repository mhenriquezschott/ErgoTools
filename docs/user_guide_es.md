# Guía de usuario de ErgoTools

Updated / Actualizado: 2026-10-17. Assessment gauge markers / Marcas del indicador.

## Iniciar la aplicación integrada

En esta instalación de desarrollo para Linux, ejecute bash tools/run.sh (installed / instalado: ergotools) desde la carpeta del proyecto nuevo. Se abre la aplicación integrada con LiFFT, DUET, Shoulder Tool (ST), PLOT, JROT y el avatar 3D. --disable-vtk se utiliza solo para diagnósticos sin renderizado.

Use la ventana normalmente y amplíela cuando sea necesario. Inglés y español están disponibles en Herramientas > Configuración. Configuración permanece en Herramientas; Ayuda permanece en el menú Ayuda. Las unidades y los decimales del proyecto se guardan al aplicar; idioma, separador decimal y animación del avatar siguen como preferencias personales. Restablecer tareas es opcional, requiere confirmación y permite Deshacer.

## Proyectos y conversión de proyectos originales

Nuevo inicia un proyecto; Guardar asigna un archivo .ergprj propio a un proyecto aún no guardado. Abrir carga un proyecto existente y una evaluación disponible automáticamente, sin preguntar qué evaluación abrir. Proyectos recientes utiliza el mismo flujo de apertura. Propiedades muestra los metadatos del proyecto.

Para un proyecto .ergprj XML original, conserve las carpetas originales de datos e imágenes junto al descriptor hasta completar la conversión. Abrir ofrece Migrar/Cancelar y un comando para la herramienta independiente; no modifica los originales. La copia convertida se abre temporalmente: use Guardar, elija un archivo .ergprj nuevo y confirme los datos prellenados. Después solo necesita ese archivo, con todas las imágenes de plantas y un resultado recalculado por versión de evaluación. No contiene una base de datos original archivada ni resultados duplicados. Cancelar o fallar Guardar conserva la copia temporal para reintentar. Los archivos faltantes, conflictos o formatos no compatibles se informan sin descartar registros.

Guardar como crea y activa otro archivo de proyecto. Copia de seguridad copia los datos ya guardados sin cambiar el proyecto abierto. Guarde primero las ediciones de evaluaciones, PLOT y JROT si desea incluirlas en la copia.

## Trabajadores, organización, trabajos y contexto

Trabajadores permite crear y editar registros. El ID es obligatorio; los datos opcionales de identidad, empleo y medidas corporales están en Detalles opcionales. Guardar cambios confirma el registro. La pestaña de asignaciones selecciona lugar, turno y asignación laboral. La franja principal permite buscar, filtrar por apellido, ordenar y navegar al primero/anterior/siguiente/último.

Lugar de trabajo > Organización mantiene plantas, secciones, líneas, estaciones y turnos independientes. Lugar de trabajo > Trabajos administra los trabajos, su disponibilidad y un único conjunto actual de valores LiFFT/DUET/ST por trabajo. Ingrese el daño directamente o use Calcular o copiar valores. Los trabajos y ubicaciones referenciados siguen protegidos.

Seleccionar contexto de evaluación elige la asignación exacta de planta/sección/línea/estación/turno. Una evaluación existente conserva su asignación original después de una reasignación: sigue siendo una observación histórica, y la nueva asignación puede tener su propia evaluación. Crear una evaluación en otra asignación no reemplaza otras herramientas o propietarios.

Buscar abre las evaluaciones guardadas de todos los trabajadores para la herramienta activa. Filtre por ID o nombre, inicial del apellido o lugar y pulse Usar evaluación. Cerrar conserva la evaluación actual.

## LiFFT, DUET y Shoulder Tool

Seleccione la pestaña e ingrese los datos de las tareas. LiFFT usa brazo de palanca, carga y repeticiones; DUET usa OMNI-Res y repeticiones; ST añade dirección de tarea. Respete las unidades indicadas. Calcular evalúa las tareas; Guardar conserva los datos y los resultados calculados. Calcular por sí solo no los guarda.

Los resultados incompletos usan solo las filas completadas y se identifican como incompletos. Los valores vacíos o no disponibles no prueban riesgo cero. Los resultados importados aparecen como Registrado; los cálculos nuevos guardados conservan su estado. Editar un dato elimina resultados obsoletos de la vista. Los datos y resultados guardados conservan la precisión del cálculo. Los valores predeterminados son un decimal para entradas, momentos y probabilidad, cuatro para daño por tarea/acumulado y uno para contribución porcentual. Las repeticiones se muestran sin decimales. Cambiar unidades o formato no redondea los valores guardados sin editar.

Restablecer cambia el borrador actual; Eliminar borra la evaluación guardada seleccionada solo tras confirmar. El botón de cuadrícula muestra datos guardados de la herramienta. Cambiar el número de tareas reemplaza la cuadrícula activa; revise la confirmación y use Deshacer cuando corresponda. ST conserva los significados de selectores y el orden de Tab originales; esta migración no cambia las fórmulas científicas.

## Idioma, separador decimal y unidades

Configuración permite inglés/español, visualización métrica/imperial y entrada decimal con punto/coma. No se admiten separadores de miles. Las unidades de origen de cada evaluación permanecen asociadas a sus datos; cambiar la visualización no reinterpreta números guardados. La estatura/peso se muestra en cm/kg o in/lb y se almacena en cm/kg.

Los CSV mantienen identificadores de columna en inglés y decimales con punto independientemente del idioma. Se conservan las etiquetas de unidades registradas y la precisión guardada. Las coordenadas de PLOT son píxeles de imagen en ambos sistemas.

## PLOT: filtros, plano y gráficos

Abra PLOT desde la barra principal. Seleccione herramienta, lugar, vista de riesgo y filtros demográficos opcionales, y aplique los filtros. El plano y los resúmenes usan evaluaciones guardadas y datos de riesgo laboral aprobados. Revise las vistas Individual, Trabajo y Comparación, los datos faltantes y los detalles destacados.

Abrir/Guardar administra la imagen de planta; zoom, tamaño real, opacidad y captura controlan su presentación. Seleccione un marcador para localizarlo o editar coordenadas, escala, visibilidad, inclusión y bloqueo. Guardar confirma las ediciones seleccionadas; Guardar todo confirma el lote validado. Otras ediciones pendientes siguen sin guardarse tras un guardado parcial. Deshacer/Rehacer y Cancelar actúan sobre el borrador geométrico; guardar lo confirma.

Use exportación CSV para los resultados guardados de trabajadores con los filtros aplicados. Los gráficos de resumen tienen configuración y exportación de imagen propias. No se habilitan el experimento D3 oculto ni los metadatos de transformación de planta sin uso.

## JROT: rotaciones y optimización

Abra JROT, seleccione o cree una rotación, defina su ámbito organizacional/lugar y complete trabajadores y trabajos de cada bloque. Defina los valores actuales de riesgo en Trabajos. Las rotaciones guardadas conservan sus asignaciones de trabajadores/trabajos y usan los valores actuales. Cambiar valores numéricos relevantes invalida la optimización anterior; vuelva a optimizar explícitamente cuando corresponda.

Optimizar actual usa CBC para la herramienta elegida; Optimizar todas usa HiGHS para LiFFT, DUET y ST en conjunto. No se usa GLPK. Ingrese un límite válido en minutos. Revise la vista previa/comparación y aplique explícitamente Usar como actual/Aplicar antes de Guardar. La vista previa no reemplaza la rotación guardada. Cancelar detiene una optimización sin aplicarla.

Deshacer/Rehacer cubre ediciones y vistas previas aplicadas dentro de la rotación seleccionada. Cargar otra reinicia ese historial; una eliminación confirmada es una operación guardada separada. La optimización usa riesgos laborales congelados, no valores de evaluación recién editados sin guardar.

## Copiar/Mover, exportar y deshacer

Transferir selecciona herramientas actuales guardadas de la asignación de origen y un trabajador/lugar/turno de destino exacto. Copiar conserva el origen; Mover elimina solo las versiones actuales seleccionadas tras completar toda la transferencia. Ambos conservan datos, resultados, unidades y estado registrado/calculado exactos. Los datos existentes en destino producen un conflicto en vez de sobrescribirse. Otras evaluaciones, valores de trabajo y propietarios permanecen intactos.

Copiar usa datos guardados: guarde antes para incluir ediciones pendientes. Mover solicita Guardar/Descartar/Cancelar cuando corresponde. Guardar puede confirmar el origen antes de un conflicto posterior; revertir la transferencia no revierte ese guardado solicitado por separado. Exportar CSV lee evaluaciones actuales guardadas; no guarda el editor silenciosamente.

Editar > Deshacer/Rehacer revierte cambios del borrador de evaluación. En campos de texto, Deshacer actúa sobre el editor enfocado. PLOT y JROT tienen historiales de borrador propios. Guardar confirma datos; eliminar registros no es una acción global recuperable. Use una copia de seguridad para recuperar registros guardados eliminados.

## Copias de seguridad, recuperación y límites

Antes de recuperar, conserve otra copia del archivo .ergprj actual. Abra una copia de seguridad con otro nombre y revise trabajador/contexto, las tres herramientas, imagen/marcadores de PLOT y rotaciones JROT. Guardar como puede convertirla en su copia de trabajo. Los proyectos nuevos contienen todas las imágenes y los datos nativos en un solo archivo; los XML necesitan sus carpetas asociadas hasta la conversión.

Un guardado fallido conserva el borrador para corregir o reintentar. No suponga que un error guardó datos; abra otra copia para inspeccionar lo persistido. Las copias no incluyen ediciones sin guardar ni historiales de Deshacer. Si falla Abrir/conversión, conserve originales y detalles del error; no modifique filas arbitrariamente para evitar validaciones.

Este hito se valida en Linux XCB con las versiones exactas aprobadas. La aceptación nativa en Windows/macOS queda pendiente. Los cálculos conservan el comportamiento original, incluidas las convenciones documentadas de momento métrico y dirección ST; la migración no es una revalidación científica. Los prototipos antropométricos ocultos permanecen solo en la referencia original externa; no se incluyen como herramientas validadas ni se archivan dentro del proyecto nativo.

## Abrir un proyecto desde la terminal

Ejecute `bash tools/run.sh "/ruta/al/proyecto.ergprj"` desde el proyecto nuevo,
o `ergotools "/ruta/al/proyecto.ergprj"` en una instalación independiente.
Use comillas si la ruta contiene espacios. Se utiliza el flujo normal de apertura,
selección de evaluación y conversión; no se guarda automáticamente.
Proyecto > Proyectos recientes recuerda hasta diez aperturas correctas.
Cancelar o fallar no añade entradas; borrar el historial no elimina proyectos.


## Historial de filtros y selecciones

Editar > Deshacer/Rehacer y Ctrl+Z / Ctrl+Mayús+Z (escritorio Linux verificado) también
funcionan en la ventana principal. Los campos conservan el historial local.
PLOT recuerda filtros aceptados, activación/valores demográficos, herramienta,
vista y lugar junto con marcadores. JROT conserva herramienta y selección
pendiente por separado del ámbito aplicado. Hay múltiples pasos durante
la sesión; no se guarda automáticamente y se conservan los botones Guardar.


## Proyectos preparados y entrega Linux final

Los seis hitos de limpieza están completos (100%). Puede comenzar las pruebas con
copias de los proyectos ya convertidos; no necesitan carpetas de datos/imágenes ni
la herramienta de conversión:

```sh
bash tools/run.sh "test_projects/native/comparative_risk_test.ergprj"
bash tools/run.sh "test_projects/native/integrated_test.ergprj"
```

El primero contiene 194 evaluaciones/resultados, cuatro imágenes y siete esquemas
JROT; el segundo, 194 evaluaciones/resultados, cuatro imágenes y cinco esquemas.
Use Guardar como para una copia personal. La entrega independiente está en
dist/linux; consulte linux_delivery.md. Los originales permanecen intactos en
test_projects/originals. Dos muestras adicionales tienen límites documentados de
esquema/metadatos; no se declaran convertidas. Windows/macOS se validarán después.

## Navegación del contexto de evaluación

Seguir al trabajador es el modo predeterminado. Restaura su último contexto guardado para la herramienta activa, o el primer contexto guardado disponible. Se puede navegar por todos los trabajadores; si faltan datos se indica Sin evaluación. Mantener contexto conserva el lugar seleccionado al cambiar de trabajador. Estos modos no filtran la lista de trabajadores.

El selector muestra asignaciones reales de lugar y turno como Guardada o Nueva, con trabajo opcional para la herramienta activa e identifica planta, sección, línea, estación y turno exactos. Nueva abre un borrador; solo Guardar crea la evaluación. Crear otra evaluación para el mismo trabajador, herramienta y trabajo en otro lugar requiere confirmar una lista de lugares existentes. Otros trabajos y herramientas no activan la advertencia. Las evaluaciones independientes y las asignaciones reales sin trabajo se pueden guardar y actualizar normalmente.

Cambiar de herramienta conserva el lugar, las entradas sin guardar y el historial de cada pestaña. Guardar y Guardar como incluyen las pestañas editadas; cambiar de trabajador/contexto/proyecto o cerrar resuelve Guardar/Descartar/Cancelar. Corrija las entradas numéricas incompletas antes de cambiar de herramienta. Los contextos recordados se guardan en las preferencias del usuario, no en los datos del proyecto.

El avatar colorea todas las regiones con evaluación para el trabajador y la asignación/contexto exactos. El panel lateral y el enfoque de cámara siguen la herramienta activa.


Deshacer y Rehacer son las dos primeras acciones de la barra principal. PLOT y JROT ofrecen Deshacer/Rehacer al extremo derecho de su fila de título, con el mismo historial y los mismos atajos. Se eliminaron su menú Editar y la barra de historial independiente. Pulse una región coloreada del avatar para seleccionar LiFFT (zona lumbar), DUET (antebrazos/manos) o ST (hombros). Las zonas neutras y el fondo no seleccionan herramientas; arrastrar sigue rotando el modelo. La selección conserva contexto y ediciones y respeta la preferencia de animación de cámara.


La barra principal agrupa Deshacer/Rehacer, Nuevo/Abrir/Guardar, PLOT/JROT y Organización/Trabajos. Exportar está en Proyecto; Lugar de trabajo contiene Organización y Trabajos. Los diálogos de proyecto ofrecen solo .ergprj; una base SQLite cualquiera no es un proyecto ErgoTools válido. Propiedades muestra los detalles de un proyecto guardado y no está disponible antes de guardarlo.

Deshacer/Rehacer en evaluaciones incluye navegación aceptada entre herramientas, trabajadores y lugares/contextos, en orden con las ediciones de datos. La escala DUET y el tipo de tarea ST confirman inmediatamente las entradas válidas como ediciones reversibles. Las entradas numéricas sin terminar o inválidas permanecen visibles y deben corregirse antes de confirmar. Los campos de texto conservan su Deshacer de escritura. El historial de navegación dura la sesión del proyecto y se borra al cerrarlo/cambiarlo; una operación nueva descarta la rama pendiente de Rehacer. Salir de un trabajador/contexto conserva Guardar/Descartar/Cancelar y finaliza su historial de edición de datos: Deshacer navegación restaura la vista, pero no revierte un guardado ni recupera ediciones descartadas o registros eliminados. Cancelar conserva el paso de navegación disponible.


Propiedades del proyecto muestra solo los datos aplicables al archivo único: nombre del proyecto, archivo, ubicación completa, fecha/hora de creación registrada, idioma del proyecto y sistema de medidas, además de la descripción completa desplazable. Los valores son de solo lectura y se pueden copiar; el diálogo se puede ampliar. Los metadatos opcionales ausentes indican Sin registro. Ya no se muestran carpetas antiguas de base de datos, imágenes o datos.

Deshacer/Rehacer una edición de evaluación restaura el desplazamiento horizontal y vertical capturado cuando comenzó la edición. En cuadrículas largas, editar la tarea 1 y deshacer conserva esa ubicación; las ediciones intermedias vuelven a su ubicación aunque se haya desplazado después. Se retira el foco de los controles anteriores antes de reconstruir la cuadrícula y el rango de desplazamiento se actualiza al cambiar el número de filas. Este estado visual dura la sesión y nunca se guarda como dato científico.


Gestión de trabajadores ofrece iconos Cambiar y Quitar en cada asignación. Cambiar selecciona otro trabajo, lugar y turno activos; Quitar pide confirmación y finaliza la asignación activa conservando las evaluaciones existentes. Ambas acciones guardan de inmediato como Agregar; los datos personales sin guardar permanecen en el formulario. Guarde primero los cambios pendientes de las listas. La lista de cada fila solo ofrece trabajos asignados a ese lugar y turno; Cambiar permite otro lugar. Se rechaza un destino ya ocupado sin sobrescribirlo. Puestos (2) cuenta dos ubicaciones de estación y turno del trabajo, no dos secciones; los padres parcialmente marcados contienen algunas estaciones seleccionadas.


Se eliminaron la creación de versiones de evaluación y la selección de versión vigente. Proyecto conserva Nueva evaluación y Contexto de evaluación. Cada asignación de trabajo del trabajador y herramienta ergonómica admite una sola evaluación guardada; Guardar actualiza esa evaluación. No existen acciones Nueva versión vacía ni Definir versión vigente. Reasignar al trabajador a otro trabajo crea otra asignación, no otra versión de la evaluación. Los datos y resultados reales conservan su asignación original.

Los proyectos de prueba actuales en formato 16 están en test_projects/native/comparative_risk_test.ergprj y test_projects/native/integrated_test.ergprj. Los archivos de prueba habituales se han actualizado al formato 16 y se abren directamente sin conversión. Abrir un proyecto nativo anterior ofrece la migración externa existente y crea otro archivo en formato 16. El conversor elimina únicamente un borrador LiFFT duplicado comprobado como vacío, sin valores ingresados ni resultado; si hay evaluaciones duplicadas con datos, detiene la conversión y solicita una decisión específica. Nunca elige silenciosamente qué evaluación real descartar.

Las evaluaciones independientes no requieren organización ni trabajo. La casilla Contexto de evaluación muestra los controles; se expanden al abrir un proyecto con organización. Asociar evaluación vincula solo la herramienta seleccionada a una asignación real sin cambiar sus datos o resultado. PLOT individual admite asignaciones sin trabajo. JROT Todos los trabajos sigue siendo independiente de evaluaciones individuales y organización.


## Marcas del indicador de evaluación

La evaluación principal y todos los indicadores de riesgo de PLOT comparten marcas y etiquetas opcionales en los límites de riesgo (0, 25, 37,5, 50 y 100). Haga clic derecho en cualquier indicador para cambiar su visibilidad o separación al instante, o use Herramientas > Configuración > Apariencia > Indicadores de riesgo y Aplicar. Configuración tiene un árbol de secciones para General, Apariencia, Proyecto y Evaluación; cambiar de sección conserva los ajustes pendientes. El intervalo inicial es de 10 puntos porcentuales; hay opciones de 5, 20 y 25, y el intervalo personalizado admite 1–100. Desactive ambas opciones de visibilidad para recuperar el indicador sin marcas. Estas preferencias personales se conservan al reiniciar y no cambian los cálculos ni los datos del proyecto. Cancelar en Configuración conserva la apariencia actual. Los formularios y las solicitudes de entrada de ErgoTools usan el tema de la aplicación; los selectores de archivos, colores y fuentes conservan la apariencia predeterminada del sistema.


## Valores del trabajo, calculadoras y copias de evaluaciones

Cada trabajo tiene un único conjunto actual e independiente de valores LiFFT, DUET y ST. El daño ingresado directamente determina la probabilidad. Expanda Calcular o copiar valores, seleccione una herramienta y elija Cálculo con tareas para usar una grilla compacta sin avatar. Comience con una tarea; + agrega filas hasta 100 y - quita la fila seleccionada. Calcular conserva momentos, daño, aportes y totales exactos. Editar datos invalida las salidas anteriores hasta volver a Calcular. Limpiar herramienta afecta solo a la seleccionada y pide confirmación. Usar evaluación de trabajador selecciona una evaluación independiente o asignada de esa herramienta y copia sus datos y resultados exactos sin recalcular, asignar ni crear vínculos. Los cambios posteriores del trabajador y del trabajo son independientes. Reemplazar o quitar tareas guardadas requiere confirmación. Cerrar acepta los cambios válidos en la sesión privada; Guardar en la ventana principal escribe el proyecto completo. Deshacer/Rehacer usa el mismo historial compartido, con un paso por dato aceptado. Los datos de trabajo sin calcular sobreviven al guardado y reapertura; PLOT/JROT no los usan como valores calculados.


Los tres archivos mantenidos—workflow_4_workers.ergprj, comparative_risk_test.ergprj e integrated_test.ergprj—siguen en sus rutas de test_projects/native y usan el formato 19. La conversión externa conserva los valores seleccionados del trabajo y elimina perfiles/evidencias anteriores sin cambiar datos/resultados de trabajadores ni asignaciones de rotación.
