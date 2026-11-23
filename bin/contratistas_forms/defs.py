# Definición de las formas de Contratistas (F0-02), desde las specs de
# clave10-sdk: specs/empresa, specs/relaciones, specs/contratos (-001).
#
# Decisión 2026-11-18 (Paco): las referencias entre formas van POR ID, sin
# catálogos (LinkaForm no deja usar el mismo catálogo dos veces en una forma).
# Una referencia = dos textos: <clave>_id (el _id del registro) y <clave> (nombre).
# Una lista de referencias = grupo repetible con <clave>_id y <clave>_nombre.
# Los grupos "no repetibles" de la spec se aplanan con prefijo (domicilio_*, acta_*...).

SI_NO = ["Sí", "No"]


def T(key, label, req=False, help=None):
    return dict(kind="text", key=key, label=label, req=req, help=help)


def TA(key, label, req=False, help=None):
    return dict(kind="textarea", key=key, label=label, req=req, help=help)


def INT(key, label, req=False, help=None):
    return dict(kind="integer", key=key, label=label, req=req, help=help)


def DEC(key, label, req=False, help=None):
    return dict(kind="decimal", key=key, label=label, req=req, help=help)


def DATE(key, label, req=False, help=None):
    return dict(kind="date", key=key, label=label, req=req, help=help)


def DT(key, label, req=False, help=None):
    return dict(kind="datetime", key=key, label=label, req=req, help=help)


def TIME(key, label, req=False, help=None):
    return dict(kind="time", key=key, label=label, req=req, help=help)


def FILES(key, label, req=False, help=None):
    return dict(kind="files", key=key, label=label, req=req, help=help)


def IMG(key, label, req=False, help=None):
    return dict(kind="images", key=key, label=label, req=req, help=help)


def SEL(key, label, opts, req=False, help=None):
    return dict(kind="select", key=key, label=label, req=req, help=help, opts=opts)


def MULTI(key, label, opts, req=False, help=None):
    return dict(kind="checkbox", key=key, label=label, req=req, help=help, opts=opts)


def YN(key, label, req=False, help=None):
    return dict(kind="radio", key=key, label=label, req=req, help=help, opts=SI_NO)


def REF(key, label, req=False, help=None):
    """Referencia a otro registro: _id + nombre visible (los escribe el back)."""
    return [
        T(f"{key}_id", f"{label} (id)", req=req, help=help or "Id del registro; lo llena Clave10."),
        T(key, label, req=req),
    ]


def GROUP(key, label, children, help=None):
    return dict(kind="group", key=key, label=label, req=False, help=help, children=flat(children))


def REFLIST(key, label, help=None):
    return GROUP(key, label, [T(f"{key}_id", f"{label} · id"), T(f"{key}_nombre", f"{label} · nombre")], help=help)


def flat(items):
    out = []
    for it in items:
        if isinstance(it, list):
            out.extend(flat(it))
        else:
            out.append(it)
    return out


DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto",
         "Septiembre", "Octubre", "Noviembre", "Diciembre"]
ESTATUS = ["Activo", "Inactivo"]
AMBITO = ["Empresa", "Persona", "Equipo"]


def RECURRENCIA(p="recurrencia"):
    return [
        SEL(f"{p}_tipo", "Recurrencia", ["Por día", "Semanal", "Mensual", "Configurable"]),
        MULTI(f"{p}_dias_semana", "Días de la semana", DIAS),
        INT(f"{p}_cada_horas", "Cada cuántas horas"),
        MULTI(f"{p}_semanas_mes", "Semanas del mes", ["1", "2", "3", "4", "5"]),
        SEL(f"{p}_mensual_modo", "Mensual por", ["Día del mes", "Ordinal"]),
        INT(f"{p}_mensual_dia", "Día del mes"),
        INT(f"{p}_mensual_ordinal", "Ordinal (1.º, 2.º…)"),
        SEL(f"{p}_mensual_dia_semana", "Día de la semana (ordinal)", DIAS),
        MULTI(f"{p}_meses", "Meses", MESES),
        INT(f"{p}_cada_n", "Cada"),
        SEL(f"{p}_unidad", "Unidad", ["día", "semana", "mes", "año"]),
        TIME(f"{p}_hora_desde", "Hora desde"),
        TIME(f"{p}_hora_hasta", "Hora hasta"),
    ]


FORMS = [
    dict(
        slug="empresas",
        name="Empresas",
        desc="Empresas del proyecto Contratistas: la propia, clientes, contratistas y subcontratistas.",
        fields=[
            T("folio", "Folio", help="CL-0001 / CT-0001; lo pone Clave10."),
            T("razon_social", "Razón social", req=True),
            T("nombre_comercial", "Nombre comercial"),
            T("rfc", "RFC", req=True),
            SEL("tipo_persona", "Tipo de persona", ["Moral", "Física"], req=True),
            T("curp", "CURP", help="Solo persona física."),
            T("regimen_fiscal", "Régimen fiscal"),
            T("actividad_preponderante", "Actividad preponderante"),
            TA("objeto_social", "Objeto social"),
            SEL("estatus_sat", "Estatus en el padrón SAT", ESTATUS),
            T("domicilio_cp", "Código postal"),
            T("domicilio_tipo_vialidad", "Tipo de vialidad"),
            T("domicilio_vialidad", "Vialidad"),
            T("domicilio_num_exterior", "Número exterior"),
            T("domicilio_num_interior", "Número interior"),
            T("domicilio_colonia", "Colonia"),
            T("domicilio_localidad", "Localidad"),
            T("domicilio_municipio", "Municipio"),
            T("domicilio_estado", "Estado"),
            T("domicilio_entre_calle", "Entre calle"),
            T("domicilio_y_calle", "Y calle"),
            T("repse_folio", "REPSE · folio"),
            DATE("repse_inicio", "REPSE · inicio"),
            DATE("repse_fin", "REPSE · fin"),
            FILES("repse_aviso", "REPSE · aviso de registro"),
            SEL("repse_estatus", "REPSE · estatus", ["Vigente", "Por vencer", "Vencido", "Sin REPSE"],
                help="Lo calcula Clave10 (Por vencer: 60 días o menos)."),
            GROUP("actividades_stps", "Actividades STPS", [
                T("actividad_clave", "Clave"), T("actividad_descripcion", "Descripción")]),
            T("acta_num_escritura", "Acta · número de escritura"),
            DATE("acta_fecha_protocolizacion", "Acta · fecha de protocolización"),
            T("acta_notario", "Acta · notario"),
            T("acta_num_notaria", "Acta · número de notaría"),
            T("acta_entidad", "Acta · entidad"),
            FILES("acta_archivo", "Acta · archivo"),
            GROUP("registros_patronales", "Registros patronales", [
                T("nrp", "Registro patronal (NRP)"), T("nrp_descripcion", "Descripción"),
                INT("nrp_trabajadores", "Trabajadores registrados")]),
            GROUP("contactos", "Contactos", [
                T("contacto_nombre", "Nombre"),
                SEL("contacto_rol", "Rol", ["Representante legal", "Apoderado legal", "Contacto"]),
                T("contacto_telefono", "Teléfono"), T("contacto_email", "Correo")]),
            IMG("logo", "Logo"),
            YN("es_propia", "Es la empresa de la cuenta", help="Solo una por cuenta."),
            SEL("estatus", "Estatus", ESTATUS, req=True),
        ],
    ),
    dict(
        slug="relaciones_entre_empresas",
        name="Relaciones entre empresas",
        desc="Relación cliente↔contratista; un registro sirve para las dos vistas.",
        fields=[
            T("folio", "Folio", help="R-0001; lo pone Clave10."),
            REF("cliente", "Cliente", req=True),
            REF("contratista", "Contratista", req=True),
            REF("relacion_padre", "Relación padre", help="Vacío = directa; lleno = subcontratación."),
            INT("nivel", "Nivel", help="1 = directa. Lo calcula Clave10."),
            REFLIST("requerimientos_asignados", "Requerimientos asignados"),
            SEL("estatus", "Estatus", ESTATUS, req=True),
            DATE("fecha_alta", "Fecha de alta"),
            TA("notas", "Notas"),
            INT("num_contratos", "Número de contratos", help="Lo calcula Clave10."),
            DEC("cumplimiento_pct", "% de cumplimiento", help="Lo calcula Clave10."),
        ],
    ),
    dict(
        slug="recursos_de_contrato",
        name="Recursos de contrato",
        desc="Servicios, perfiles y equipos que se contratan, con sus requerimientos.",
        fields=[
            SEL("tipo", "Tipo", ["Servicio", "Perfil", "Equipo"], req=True),
            T("nombre", "Nombre", req=True),
            TA("descripcion", "Descripción"),
            T("categoria", "Categoría"),
            SEL("clase", "Clase de equipo", ["Equipo", "Vehículo", "Herramienta"], help="Solo Equipo."),
            REFLIST("requerimientos", "Requerimientos"),
            SEL("estatus", "Estatus", ESTATUS, req=True),
        ],
    ),
    dict(
        slug="requerimientos_de_cumplimiento",
        name="Requerimientos de cumplimiento",
        desc="Documentos, exámenes e inspecciones que se exigen a empresas, personas y equipos.",
        fields=[
            T("nombre", "Nombre", req=True),
            TA("descripcion", "Descripción"),
            SEL("tipo", "Tipo", ["Documento", "Examen", "Inspección"], req=True),
            SEL("ambito", "Ámbito", AMBITO, req=True),
            SEL("plataforma", "Plataforma", ["Sin plataforma", "SAT", "IMSS", "INFONAVIT", "STPS",
                                             "Registro Público de Comercio", "INE", "Otra"]),
            T("plataforma_url", "Liga de la plataforma"),
            SEL("vigencia_modo", "Modo de vigencia", ["Vigencia", "Periodo"], req=True),
            INT("vigencia_n", "Vigencia (cantidad)", help="Vacío = permanente."),
            SEL("vigencia_unidad", "Vigencia (unidad)", ["días", "meses", "años"]),
            SEL("periodicidad", "Periodicidad", ["Única", "Mensual", "Bimestral", "Trimestral", "Cuatrimestral",
                                                 "Semestral", "Anual", "Cada 3 años", "Cada 10 años"]),
            MULTI("meses_periodo", "Meses en que vence", MESES),
            INT("dia_limite", "Día límite", help="Día del mes en que vence el periodo; default 17."),
            RECURRENCIA(),
            INT("tolerancia_dias", "Tolerancia (días)"),
            YN("aviso_activo", "Avisar antes de vencer"),
            INT("aviso_n", "Aviso (cantidad)"),
            SEL("aviso_unidad", "Aviso (unidad)", ["días", "semanas", "meses"]),
            YN("aviso_repetir", "Repetir aviso"),
            YN("requiere_acuse", "Requiere acuse"),
            YN("limitante", "Limitante", help="Si no se cumple, el contrato queda En documentación."),
            GROUP("criterios", "Criterios de revisión", [T("criterio", "Criterio")]),
            FILES("documento_ejemplo", "Documento de ejemplo"),
            SEL("examen_modalidad", "Examen · modalidad", ["Físico", "Digital"]),
            INT("examen_intentos", "Examen · intentos"),
            DEC("examen_calificacion_minima", "Examen · calificación mínima", help="Default 80."),
            YN("examen_preguntas_aleatorias", "Examen · preguntas aleatorias"),
            YN("examen_respuestas_aleatorias", "Examen · respuestas aleatorias"),
            INT("examen_vigencia_resultado_n", "Examen · vigencia del resultado (cantidad)"),
            SEL("examen_vigencia_resultado_unidad", "Examen · vigencia del resultado (unidad)", ["días", "meses", "años"]),
            T("inspeccion", "Inspección"),
            SEL("estatus", "Estatus", ESTATUS, req=True),
        ],
    ),
    dict(
        slug="contratos_de_servicio",
        name="Contratos de servicio",
        desc="Contratos entre un cliente y un contratista, con sus recursos, ubicaciones y empleados.",
        fields=[
            T("folio", "Folio", help="C-0001; lo pone Clave10."),
            T("numero_contrato", "Número de contrato"),
            REF("relacion", "Relación", req=True),
            REF("cliente", "Cliente", help="Copia de la relación."),
            REF("contratista", "Contratista", help="Copia de la relación."),
            T("objeto", "Objeto", req=True),
            TA("descripcion", "Descripción"),
            DEC("monto", "Monto"),
            DATE("inicio", "Inicio", req=True),
            DATE("fin", "Fin", req=True),
            REF("responsable", "Responsable", help="Usuario de LinkaForm (id numérico)."),
            FILES("contrato_firmado", "Contrato firmado"),
            YN("permite_subcontratacion", "Permite subcontratación"),
            GROUP("servicios", "Servicios", [T("servicio_id", "Servicio · id"), T("servicio", "Servicio")]),
            GROUP("perfiles", "Perfiles", [
                T("perfil_id", "Perfil · id"), T("perfil", "Perfil"), INT("perfil_cantidad", "Cantidad"),
                TA("perfil_requerimientos_excluidos", "Requerimientos excluidos (ids)", help="Lista JSON de ids.")]),
            GROUP("equipos", "Equipos", [
                T("equipo_id", "Equipo · id"), T("equipo", "Equipo"),
                SEL("equipo_clase", "Clase", ["Equipo", "Vehículo", "Herramienta"]),
                INT("equipo_cantidad", "Cantidad"),
                TA("equipo_requerimientos_excluidos", "Requerimientos excluidos (ids)", help="Lista JSON de ids.")]),
            GROUP("ubicaciones", "Ubicaciones", [
                T("ubicacion_id", "Ubicación · id"), T("ubicacion", "Ubicación"),
                SEL("ubicacion_estatus", "Estatus", ["Activa", "En apertura", "Inactiva"])]),
            GROUP("empleados", "Empleados", [
                T("empleado_id", "Empleado · id"), T("empleado", "Empleado"),
                T("empleado_perfil_id", "Perfil · id"), T("empleado_perfil", "Perfil"),
                T("empleado_ubicacion_id", "Ubicación · id"), T("empleado_ubicacion", "Ubicación"),
                DATE("empleado_fecha_alta", "Fecha de alta")]),
            RECURRENCIA(),
            SEL("estatus_manual", "Estatus manual", ["Pausado", "Cancelado"]),
            TA("motivo_estatus", "Motivo del estatus"),
            SEL("estatus", "Estatus", ["Activo", "Por vencer", "En documentación", "Vencido", "Pausado", "Cancelado"],
                help="Lo calcula Clave10."),
            DEC("cumplimiento_pct", "% cumplimiento", help="Lo calcula Clave10."),
            DEC("cumplimiento_contrato_pct", "% cumplimiento · contrato"),
            DEC("cumplimiento_empleados_pct", "% cumplimiento · empleados"),
            DEC("cumplimiento_periodicos_pct", "% cumplimiento · periódicos"),
        ],
    ),
    dict(
        slug="historial_de_contratos",
        name="Historial de contratos",
        desc="Un registro por cambio de un contrato; lo escribe Clave10.",
        fields=[
            REF("contrato", "Contrato", req=True),
            SEL("evento", "Evento", ["Creación", "Ubicaciones", "Perfiles", "Equipos", "Servicios", "Empleados",
                                     "Monto", "Vigencia", "Estatus", "Pausa", "Reanudación", "Cancelación",
                                     "Modificatorio"], req=True),
            T("detalle", "Detalle"),
            TA("antes", "Antes (JSON)"),
            TA("despues", "Después (JSON)"),
            FILES("documento", "Documento"),
            T("autor", "Autor"),
            DT("fecha", "Fecha"),
        ],
    ),
    dict(
        slug="documentos_de_cumplimiento",
        name="Documentos de cumplimiento",
        desc="Documentos que cumplen requerimientos, con versiones, comentarios y aprobaciones por cliente.",
        fields=[
            T("folio", "Folio", help="D-0001; lo pone Clave10."),
            T("nombre", "Nombre", req=True),
            T("categoria", "Categoría"),
            REF("requerimiento", "Requerimiento"),
            SEL("dueno_tipo", "Tipo de dueño", AMBITO, req=True),
            REF("dueno_empresa", "Empresa dueña", req=True),
            REF("dueno_empleado", "Empleado dueño"),
            REF("dueno_equipo", "Equipo dueño"),
            T("periodo_clave", "Periodo · clave"),
            DATE("periodo_inicio", "Periodo · inicio"),
            DATE("periodo_fin", "Periodo · fin"),
            YN("en_ceros", "Declaración en ceros"),
            DATE("vigencia_inicio", "Vigencia · inicio"),
            DATE("vigencia_fin", "Vigencia · fin", help="Vacío = permanente."),
            FILES("archivo", "Archivo", req=True),
            SEL("estatus", "Estatus", ["Por revisar", "Aceptado", "Rechazado", "Vencido"], help="Lo calcula Clave10."),
            REFLIST("compartido_con", "Compartido con"),
            REFLIST("contratos", "Contratos"),
            SEL("origen", "Origen", ["Carga", "Carga masiva", "Sesión"]),
            TA("lectura_ia", "Lectura IA (JSON)"),
            GROUP("versiones", "Versiones", [
                INT("version_numero", "Número"), FILES("version_archivo", "Archivo"),
                SEL("version_estatus", "Estatus", ["Por revisar", "Aceptado", "Rechazado", "Vencido"]),
                T("version_subido_por", "Subido por"), DT("version_fecha", "Fecha"),
                TA("version_motivo_rechazo", "Motivo de rechazo")]),
            GROUP("comentarios", "Comentarios", [
                T("comentario_autor", "Autor"), DT("comentario_fecha", "Fecha"), TA("comentario_texto", "Texto")]),
            GROUP("aprobaciones", "Aprobaciones", [
                T("aprobacion_cliente_id", "Cliente · id"), T("aprobacion_cliente", "Cliente"),
                SEL("aprobacion_decision", "Decisión", ["Pendiente", "Aprobado", "Rechazado"]),
                T("aprobacion_revisor", "Revisor"), DT("aprobacion_fecha", "Fecha"),
                TA("aprobacion_motivo", "Motivo")]),
        ],
    ),
    dict(
        slug="cumplimiento_de_requerimientos",
        name="Cumplimiento de requerimientos",
        desc="Una fila por sujeto × requerimiento × periodo. La escribe solo el motor de cumplimiento.",
        fields=[
            REF("relacion", "Relación", req=True),
            REF("contrato", "Contrato"),
            REF("requerimiento", "Requerimiento", req=True),
            YN("limitante", "Limitante"),
            SEL("sujeto_tipo", "Tipo de sujeto", AMBITO, req=True),
            REF("sujeto_empresa", "Empresa", req=True),
            REF("sujeto_empleado", "Empleado"),
            REF("sujeto_equipo", "Equipo"),
            T("periodo_clave", "Periodo · clave", req=True),
            DATE("periodo_inicio", "Periodo · inicio"),
            DATE("periodo_fin", "Periodo · fin"),
            DATE("periodo_vence", "Periodo · vence"),
            REF("documento", "Documento"),
            SEL("estado", "Estado", ["Por transcurrir", "En plazo", "Por subir", "Por revisar", "Cumplido",
                                     "Rechazado", "Vencido", "En ceros", "No aplica"], req=True),
            SEL("estado_manual", "Estado manual", ["No aplica", "Cumplido", "Rechazado", "Vencido"]),
            TA("motivo_manual", "Motivo manual"),
        ],
    ),
    dict(
        slug="sesiones_de_capacitacion",
        name="Sesiones de capacitación",
        desc="Cursos, talleres y pláticas con temario, participantes y el requerimiento que otorgan.",
        fields=[
            T("nombre", "Nombre", req=True),
            TA("descripcion", "Descripción"),
            SEL("tipo", "Tipo", ["Curso", "Taller", "Webinar", "Plática"], req=True),
            T("instructor", "Instructor"),
            DATE("fecha_inicio", "Fecha de inicio", req=True),
            DATE("fecha_fin", "Fecha de fin", req=True),
            TIME("hora_inicio", "Hora de inicio"),
            TIME("hora_fin", "Hora de fin"),
            RECURRENCIA(),
            DATE("recurrencia_repetir_hasta", "Repetir hasta"),
            T("lugar", "Lugar"),
            T("enlace", "Enlace"),
            REFLIST("areas", "Áreas"),
            INT("cupo", "Cupo"),
            REF("examen", "Examen"),
            REF("otorga", "Requerimiento que otorga"),
            GROUP("temario", "Temario", [
                T("tema", "Tema"), T("leccion", "Lección"), INT("minutos", "Minutos"),
                SEL("material_tipo", "Tipo de material", ["Video", "Lectura", "Presentación", "Cuestionario", "Clase en vivo"]),
                SEL("material_origen", "Origen del material", ["Archivo", "Enlace"]),
                FILES("material_archivo", "Archivo"), T("material_enlace", "Enlace")]),
            GROUP("participantes", "Participantes", [
                T("participante_id", "Empleado · id"), T("participante", "Empleado"),
                TA("participante_asistencia", "Asistencia (JSON)"), DEC("participante_calificacion", "Calificación"),
                SEL("participante_resultado", "Resultado", ["Aprobado", "No aprobado"])]),
            YN("cancelada", "Cancelada"),
            TA("motivo_cancelacion", "Motivo de cancelación"),
            SEL("estatus", "Estatus", ["Programada", "En curso", "Finalizada", "Cancelada"], help="Lo calcula Clave10."),
        ],
    ),
]


# Campos nuevos en formas EXISTENTES (no se generan completas: se agrega una
# página al XML que ya vive en addons, sin tocar sus campos).
EXTENSIONS = [
    dict(
        slug="empleados",
        xml="employee/items/forms/RecursosHumanos/empleados.xml",
        page="Contratista",
        fields=[
            REF("empresa", "Empresa contratista",
                help="Id del registro de Empresas; vacío = empresa propia. Lo llena Clave10."),
            T("registro_patronal", "Registro patronal (NRP)"),
            DEC("salario_base_cotizacion", "Salario base de cotización"),
            DATE("alta_imss", "Alta ante el IMSS"),
            REFLIST("perfiles", "Perfiles"),
            YN("disponible_para_contratos", "Disponible para contratos"),
            DATE("vetado_fecha", "Vetado · fecha"),
            TA("vetado_motivo", "Vetado · motivo"),
            T("vetado_por", "Vetado · por"),
        ],
    ),
]
