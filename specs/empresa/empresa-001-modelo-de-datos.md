# SPEC empresa-001 — Modelo de datos de Contratistas: base común, Empresa y Empleados

> **Status:** Borrador
> **Depends on:** ninguna
> **Date:** 2026-11-18
> **Objective:** Fijar dónde y cómo se guardan los datos del proyecto Contratistas (convenciones comunes a todas las formas) y definir la entidad Empresa, sus contactos y registros patronales, y la extensión de Empleados para personal de contratistas.

---

## Por qué existe esta spec

Es la parte de F0-01 que desbloquea todo lo demás del plan (F0-02, F0-03, F0-08 y las pantallas de Mi Empresa). Las otras dos partes del modelo están en SPEC relaciones-001 (relación cliente↔contratista) y SPEC contratos-001 (contrato, requerimientos, documentos, cumplimiento y sesiones). Las tres se leen juntas; las convenciones de esta spec aplican a las tres.

## Alcance

**Dentro:**

- Convenciones comunes: dónde viven los datos, nombres de formas, referencias entre formas, folios, estatus y fechas.
- Cómo se resuelve "Mi Empresa" del usuario que entra.
- Forma **Empresas** con contactos, registros patronales y actividades STPS.
- Campos nuevos en la forma **Empleados** existente para el personal de una empresa contratista.
- Tipos TypeScript que usarán los mocks y servicios del front (F0-08).

**Fuera de alcance:**

- Crear las formas en LinkaForm y sus ids: F0-02.
- Rutas de Sanic: cada tarea de back define las suyas (R-01, ME-14, ME-15…).
- Alta de cuenta independiente por empresa con dominio `xxx.clave10.com`: mediano/largo plazo (RG-01 define su alcance sin eso).
- Usuarios de Mi Empresa, Ubicaciones y Áreas (ME-02 reusa lo actual), Activos (ME-08), Sanciones (R-07), Invitaciones (R-02), catálogo maestro y mapeo (ME-13).

## Convenciones comunes (aplican a las tres specs)

1. **Todo en LinkaForm, dentro de la cuenta del cliente.** Cada entidad es una forma (registros en Mongo). No hay base de datos aparte ni cuenta propia por empresa.
2. **Todas las empresas son registros de la misma forma.** La empresa dueña de la cuenta, sus clientes, sus contratistas y los subcontratistas son registros de **Empresas**. Si un contratista trabaja para dos cuentas distintas, existe una vez en cada cuenta (consecuencia del punto 1).
3. **Back único en Sanic, dentro de `accesos`.** Ids de formas en `lkf-sanic-apps/addons/accesos/models.py` (`self.lkm.form_id(...)`) y de campos en `accesos/contratistas_fields.py` (`self.ctr_f[<forma>][<clave>]`), lógica en `service.py`, rutas `/accesos/...` en `routes.py`. En `addons` solo van los XML de las formas (`accesos/items/forms/Seguridad/Contratistas/`) y, si hace falta, puentes sin lógica para workflows. Los XML y `contratistas_fields.py` se generan desde la definición de estas specs con un script, para no editarlos a mano.
4. **Nombres que no chocan.** Ninguna forma nueva se llama "Contratistas" (la usa `produccion_pci`), "Configuración de perfiles" (es de pases en accesos) ni "Definición de requerimientos" (existe en otra cuenta). Los nombres de forma de cada spec son los definitivos para F0-02.
5. **Campos.** En esta spec cada campo se nombra con su clave (`snake_case`), que es la que usa `self.f[...]` en Sanic y la propiedad del objeto en el front. El `field_id` lo asigna F0-02 al crear la forma.
6. **Referencias entre formas por `_id`, sin catálogos** (decisión de F0-02, 2026-11-18). LinkaForm no deja usar el mismo catálogo dos veces en una forma, y el modelo lo necesita (cliente y contratista, servicios/perfiles/equipos, examen y otorga). Una referencia son dos campos de texto: `<clave>_id` con el `_id` del registro y `<clave>` con su nombre visible; los escribe el back. Una lista de referencias es un grupo repetible con `<clave>_id` y `<clave>_nombre`. Todo se captura desde Clave10 vía Sanic, así que no hacen falta catálogos ni workflows de sincronización; las búsquedas y agregaciones usan el `_id`.
7. **Grupos repetibles** para listas que solo existen dentro de su registro (contactos, versiones de un documento, renglones de un contrato). Si algo se consulta por sí solo en varias pantallas o cruza registros, va en su propia forma. Lo que en estas specs aparece como «grupo (no repetible)» se guarda aplanado con prefijo (`domicilio_cp`, `acta_notario`, `repse_fin`…); el back lo regresa anidado como en los tipos del front.
8. **Folios.** Prefijo por entidad más consecutivo de la cuenta: Empresa cliente `CL-0001`, contratista `CT-0001`, contrato `C-0001`, documento `D-0001`, empleado `E-0001`. Lo pone el back al crear; no se captura.
9. **Estatus calculados por el back.** Si un estatus depende de fechas o de otros registros (Por vencer, Vencido, % de cumplimiento), lo calcula el back y lo guarda; el front no lo deduce. Así las listas filtran y ordenan en Mongo.
10. **Fechas** en ISO (`YYYY-MM-DD`; con hora, `YYYY-MM-DD HH:MM:SS`) en la zona del usuario, como el resto de Clave10.
11. **Archivos** (PDF, imágenes, XML) en campos de archivo de LinkaForm; el front recibe `{ name, file_url, size }`.
12. **Borrar = desactivar.** Las entidades de este modelo no se borran desde Clave10: pasan a estatus Inactivo (o Cancelado en contratos).

### "Mi Empresa" del usuario

- La empresa dueña de la cuenta es el registro de Empresas con `es_propia = sí`. Hay exactamente uno por cuenta.
- La empresa activa de un usuario sale de su registro en **Empleados** (ligado por `usuario`): el campo `empresa` nuevo. Si no tiene empleado o el campo está vacío, su empresa es la propia.
- Con eso el back resuelve en cada ruta, desde el JWT, quién es "propio" y quién "otro" en relaciones y contratos (lo que el diseño llama `kLbl` y `ctoBackMode`). El front no manda el id de su empresa.

## Modelo de datos

### Forma **Empresas**

| Clave | Tipo | Notas |
| --- | --- | --- |
| `folio` | texto | `CL-` / `CT-` según el tipo con el que nació; no cambia si después tiene ambos papeles |
| `razon_social` | texto | requerido |
| `nombre_comercial` | texto | |
| `rfc` | texto | requerido, 12 (moral) o 13 (física) caracteres, único en la cuenta |
| `tipo_persona` | select | `moral` \| `fisica` |
| `curp` | texto | solo persona física, 18 caracteres |
| `regimen_fiscal` | texto | de la CSF |
| `actividad_preponderante` | texto | |
| `objeto_social` | texto largo | |
| `estatus_sat` | select | `Activo` \| `Inactivo` (padrón SAT, de la CSF) |
| `domicilio_fiscal` | grupo (no repetible) | `cp`, `tipo_vialidad`, `vialidad`, `num_exterior`, `num_interior`, `colonia`, `localidad`, `municipio`, `estado`, `entre_calle`, `y_calle` |
| `repse_folio` | texto | |
| `repse_inicio` / `repse_fin` | fecha | |
| `repse_aviso` | archivo | aviso de registro |
| `repse_estatus` | select, calculado | `Vigente` \| `Por vencer` (≤ 60 días) \| `Vencido` \| `Sin REPSE` |
| `actividades_stps` | grupo repetible | `clave`, `descripcion` |
| `acta` | grupo (no repetible) | `num_escritura`, `fecha_protocolizacion`, `notario`, `num_notaria`, `entidad`, `archivo` |
| `registros_patronales` | grupo repetible | `nrp`, `descripcion`, `trabajadores_registrados` |
| `contactos` | grupo repetible | `nombre`, `rol` (`Representante legal` \| `Apoderado legal` \| `Contacto`), `telefono`, `email` |
| `logo` | imagen | |
| `es_propia` | casilla | sí solo en la empresa dueña de la cuenta |
| `estatus` | select | `Activo` \| `Inactivo` |

Notas:
- El **representante legal** que muestran las listas es el primer contacto con rol `Representante legal`; no hay un campo aparte.
- El **dominio** (`xxx.clave10.com`) del registro queda fuera hasta que exista alta de cuenta independiente.
- Que una empresa sea cliente o contratista de otra **no** es un campo de Empresas: lo dice la relación (SPEC relaciones-001). Una misma empresa puede ser cliente de una y contratista de otra.

### Forma **Empleados** (existente) — campos nuevos

La forma ya tiene nombre, foto, RFC, CURP, NSS, nacimiento, género, domicilio, puesto, departamento, jefe directo, tipo de contrato, fechas de ingreso y baja, y motivo de baja (incluye "Petición del contratista"). Se reusa para el personal de las empresas contratistas, agregando:

| Clave | Tipo | Notas |
| --- | --- | --- |
| `empresa_id` / `empresa` | referencia a Empresas | vacía = empresa propia |
| `registro_patronal` | texto | NRP de la empresa con el que está dado de alta |
| `salario_base_cotizacion` | número | SBC |
| `alta_imss` | fecha | |
| `perfiles` | lista de referencias a Recursos de contrato (`tipo = Perfil`) | definido en SPEC contratos-001 |
| `disponible_para_contratos` | casilla | |
| `vetado` | grupo (no repetible) | `fecha`, `motivo`, `por` |

Los contratos en los que participa el empleado y los perfiles que cubre en cada uno **no** van aquí: van en el contrato (SPEC contratos-001), para no tener la misma información en dos lugares.

Reglas: CURP única en la cuenta; el usuario de la app se crea con el flujo existente de Usuarios (SPEC usuarios-002), no con uno nuevo.

### Tipos para el front (F0-08)

```ts
type Id = string;                       // _id del registro en LinkaForm
type Estatus = 'Activo' | 'Inactivo';
interface Archivo { name: string; file_url: string; size?: number }

interface Domicilio {
  cp: string; tipo_vialidad?: string; vialidad: string; num_exterior?: string;
  num_interior?: string; colonia?: string; localidad?: string; municipio: string;
  estado: string; entre_calle?: string; y_calle?: string;
}

interface Contacto { nombre: string; rol: 'Representante legal' | 'Apoderado legal' | 'Contacto'; telefono?: string; email?: string }

interface Empresa {
  id: Id; folio: string; razon_social: string; nombre_comercial?: string; rfc: string;
  tipo_persona: 'moral' | 'fisica'; curp?: string; regimen_fiscal?: string;
  actividad_preponderante?: string; objeto_social?: string; estatus_sat?: Estatus;
  domicilio_fiscal?: Domicilio;
  repse?: { folio: string; inicio: string; fin: string; aviso?: Archivo;
            estatus: 'Vigente' | 'Por vencer' | 'Vencido' | 'Sin REPSE' };
  actividades_stps: { clave: string; descripcion: string }[];
  acta?: { num_escritura: string; fecha_protocolizacion: string; notario: string;
           num_notaria: string; entidad: string; archivo?: Archivo };
  registros_patronales: { nrp: string; descripcion?: string; trabajadores_registrados?: number }[];
  contactos: Contacto[];
  logo?: Archivo; es_propia: boolean; estatus: Estatus;
}

interface EmpleadoContratista {
  id: Id; folio: string; nombre: string; foto?: Archivo; curp: string; rfc?: string; nss?: string;
  empresa: { id: Id; razon_social: string } | null;     // null = empresa propia
  puesto?: string; registro_patronal?: string; salario_base_cotizacion?: number; alta_imss?: string;
  perfiles: { id: Id; nombre: string }[];
  disponible_para_contratos: boolean;
  vetado?: { fecha: string; motivo: string; por: string };
  estatus: Estatus; usuario_id?: number;
}
```

## Plan de implementación

1. **Revisión de esta spec** con Maricruz (revisora de F0-01) junto con relaciones-001 y contratos-001.
2. **F0-02** crea la forma Empresas, agrega los campos a Empleados (subiendo su `updated_at`) y registra los ids en `accesos/models.py`. Prueba: `lkfaddons install` en una cuenta de pruebas sin errores y la forma Empleados sigue guardando registros viejos.
3. **Registro de la empresa propia** en cada cuenta al instalar (uno con `es_propia = sí`, con la razón social de la cuenta). Lo hace F0-02 con un script idempotente.
4. **F0-08** escribe estos tipos en el front y sus mocks.

## Criterios de aceptación

- [ ] Cada entidad de esta spec tiene nombre de forma, claves de campo, tipo y valores de select definidos.
- [ ] Ninguna forma nueva reusa los nombres "Contratistas", "Configuración de perfiles" ni "Definición de requerimientos".
- [ ] Está definido cómo se obtiene "Mi Empresa" de un usuario sin que el front mande su empresa.
- [ ] Los tipos TypeScript cubren lo que necesitan las pantallas de Mi Empresa · Generales (ME-01) y Empleados (ME-03, ME-04).
- [ ] Maricruz revisó las tres specs del modelo.

## Decisiones tomadas y descartadas

- **Sí:** todo dentro de la cuenta del cliente. **No** base aparte ni cuenta por empresa: la plataforma no tiene alta de cuenta (`create_user` cuelga al usuario de la cuenta del APIKEY).
- **Sí:** una sola forma para todas las empresas. **No** formas separadas de clientes y contratistas: el diseño es una relación vista desde dos lados.
- **Sí:** reusar la forma **Empleados** con un campo `empresa`. Ya tiene casi todos los datos del diseño y así el personal del contratista sirve después para pases y check-in. **No** una forma nueva de empleados de contratista.
- **No** reusar Clientes, Proveedores ni el catálogo `compaia` de base: tienen otro uso y pocos campos.
- **No** tocar la forma ni el catálogo "Contratistas" de addons: los usa `produccion_pci`. Tampoco el módulo viejo `addons/contratistas` de Sanic.
- **Sí:** referencias por `_id` y sin catálogos en todas las formas nuevas (ver convención 6). **No** catálogos: chocan cuando una forma usa el mismo dos veces y obligan a mantener workflows de sincronización.
- **Sí:** estatus calculados guardados por el back, para filtrar y ordenar en Mongo.
- **Sí:** representante legal = contacto con ese rol, no un campo suelto.

## Riesgos identificados

| Riesgo | Mitigación |
| --- | --- |
| Agregar campos a Empleados afecta a todas las cuentas y módulos que la usan | Solo campos nuevos y opcionales, sin cambiar los existentes; probar en una cuenta de pruebas que pases, asistencia y check-in siguen igual antes del rollout, y revisar en todas las cuentas (solo lectura) que su Empleados no tenga cambios propios antes de instalar |
| Una cuenta queda sin empresa propia o con dos | El script de F0-02 es idempotente y la ruta de "Mi Empresa" falla con mensaje claro si encuentra cero o más de una |
| Un contratista que trabaja para dos cuentas se registra dos veces | Aceptado en v1; se resuelve con cuenta independiente (mediano/largo plazo) |
| El catálogo de Empleados crece con personal de contratistas y ensucia selectores de otros módulos | Los selectores existentes filtran por `empresa` vacía cuando no deben mostrar contratistas; se revisa en F0-02 qué selectores usan el catálogo |

## Lo que **no** está en esta spec

- Relación cliente↔contratista y subcontratación: SPEC relaciones-001.
- Contratos, requerimientos, documentos, cumplimiento y sesiones: SPEC contratos-001.
- Rutas de Sanic, permisos de menú (`RequireMenuAccess`) y pantallas.
