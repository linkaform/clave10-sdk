# SPEC relaciones-001 — Modelo de datos de Contratistas: relación cliente↔contratista y subcontratación

> **Status:** Borrador
> **Depends on:** SPEC empresa-001
> **Date:** 2026-11-18
> **Objective:** Definir la relación entre dos empresas (quién es cliente y quién contratista), cómo se ve desde cada lado con etiquetas espejo, y cómo se encadena la subcontratación.

---

## Por qué existe esta spec

En el diseño, Clientes y Contratistas son dos menús con la misma pantalla. Para no duplicar datos, la relación existe una sola vez y cada lado la lee con su etiqueta. Esta spec fija ese registro, sus estatus y la regla de subcontratación, para que R-01 (back), R-03 (subcontratación), R-04/R-05 (pantallas) y F0-03 (contexto) partan del mismo modelo. Las convenciones comunes están en SPEC empresa-001.

## Alcance

**Dentro:**

- Forma **Relaciones entre empresas**.
- Cómo se calcula la vista Clientes y la vista Contratistas de la empresa activa.
- Subcontratación: `relacion_padre`, validación de ciclos y nivel máximo.
- Datos calculados que muestran las listas (número de contratos, % de cumplimiento, vigencia del REPSE).
- Tipos TypeScript para F0-08.

**Fuera de alcance:**

- Invitaciones (cómo nace una relación desde un correo): R-02, **por definir**. Mientras tanto la relación se da de alta directamente.
- Árbol de subcontratistas en pantalla: R-08.
- Sanciones e incidencias de la relación: R-07.

## Modelo de datos

### Forma **Relaciones entre empresas**

| Clave | Tipo | Notas |
| --- | --- | --- |
| `folio` | texto | `R-0001`, lo pone el back |
| `cliente_id` / `cliente` | referencia a Empresas | requerido; la empresa que recibe el servicio |
| `contratista_id` / `contratista` | referencia a Empresas | requerido; la empresa que lo presta; distinta de `cliente` |
| `relacion_padre_id` / `relacion_padre` | referencia a Relaciones | vacío = relación directa; lleno = subcontratación (ver abajo) |
| `nivel` | número, calculado | 1 = directa; `nivel` del padre + 1 |
| `estatus` | select | `Activo` \| `Inactivo` |
| `fecha_alta` | fecha | |
| `notas` | texto largo | |
| `requerimientos_asignados` | lista de referencias a Requerimientos | requerimientos de ámbito Empresa que el cliente le exige al contratista fuera de un contrato (MX-05); por defecto los `limitante` |
| `num_contratos` | número, calculado | contratos de la relación que no están `Cancelado` |
| `cumplimiento_pct` | número, calculado | ver SPEC contratos-001, "Cumplimiento" |

Reglas:
- Solo una relación `Activo` por par (`cliente`, `contratista`, `relacion_padre`). Dar de alta otra igual reactiva la existente.
- Desactivar una relación no borra sus contratos; los contratos activos se tienen que pausar o cancelar antes (el back lo valida).

### Vistas desde la empresa activa (`kLbl`)

Con `E` = empresa activa del usuario (SPEC empresa-001):

- **Mis contratistas** = relaciones con `cliente = E`. La lista muestra a `contratista`.
- **Mis clientes** = relaciones con `contratista = E`. La lista muestra a `cliente`.

Es el mismo registro: la relación "Grupo Viso contrata a Limpieza SA" aparece en Contratistas para Grupo Viso y en Clientes para Limpieza SA. El back recibe `direccion = clientes | contratistas` y regresa siempre el mismo tipo de fila, con la contraparte ya resuelta.

### Subcontratación

- Si Limpieza SA (contratista de Grupo Viso) subcontrata a Vigilancia SA **para ese cliente**, se crea la relación `cliente = Limpieza SA`, `contratista = Vigilancia SA`, `relacion_padre = (Grupo Viso → Limpieza SA)`.
- Validaciones del back al guardar:
  1. El `cliente` de la hija es el `contratista` del padre.
  2. Sin ciclos: el `contratista` de la hija no aparece en la cadena de padres.
  3. `nivel` ≤ **3** (constante en `accesos/models.py`, fácil de cambiar).
  4. Solo se subcontrata si algún contrato activo de la relación padre tiene `permite_subcontratacion = sí` (SPEC contratos-001).
- La empresa raíz (Grupo Viso) ve a toda la cadena para cumplimiento; cada intermedio solo ve hacia abajo. Las pantallas del árbol son R-08.

### Tipos para el front (F0-08)

```ts
type Direccion = 'clientes' | 'contratistas';

interface Relacion {
  id: Id; folio: string;
  cliente: { id: Id; razon_social: string; rfc: string };
  contratista: { id: Id; razon_social: string; rfc: string };
  relacion_padre: Id | null; nivel: number;
  requerimientos_asignados: { id: Id; nombre: string }[];
  estatus: Estatus; fecha_alta: string; notas?: string;
  num_contratos: number; cumplimiento_pct: number;
}

// Fila de la lista única Clientes/Contratistas (R-04): contraparte ya resuelta
interface RelacionFila {
  id: Id; folio: string;
  contraparte: { id: Id; razon_social: string; rfc: string; logo?: Archivo };
  representante?: { nombre: string; email?: string };
  repse?: { folio: string; fin: string; dias_restantes: number;
            estatus: 'Vigente' | 'Por vencer' | 'Vencido' | 'Sin REPSE' };
  num_contratos: number; cumplimiento_pct: number; estatus: Estatus;
}
```

## Plan de implementación

1. **Revisión** de esta spec con Maricruz junto con empresa-001 y contratos-001.
2. **F0-02** crea la forma y registra los ids en `accesos/models.py`.
3. **R-01** implementa list/get/create/update/change_status con `direccion`, las reglas de unicidad y el cálculo de `num_contratos`.
4. **R-03** implementa las validaciones de subcontratación y el endpoint de árbol.

## Criterios de aceptación

- [ ] Una relación se guarda una vez y aparece en Clientes de un lado y en Contratistas del otro.
- [ ] Están definidas las reglas de unicidad, desactivación, ciclos y nivel máximo.
- [ ] `RelacionFila` cubre las columnas de R-04 (razón social, RFC, folio, REPSE con días, representante, contratos, % cumplimiento, estatus).
- [ ] Maricruz revisó las tres specs del modelo.

## Decisiones tomadas y descartadas

- **Sí:** un registro por relación con `cliente` y `contratista` explícitos. **No** campos de "tipo" en Empresas: una empresa puede ser ambas cosas con distintas contrapartes.
- **Sí:** subcontratación como relación hija con `relacion_padre`, ligada a un cliente concreto. **No** una relación genérica "A subcontrata a B" sin cliente: el cumplimiento se revisa por cadena de cliente.
- **Sí:** nivel máximo 3 como constante. Es un supuesto; se ajusta si el cliente lo pide.
- **Sí:** `num_contratos` y `cumplimiento_pct` guardados por el back para ordenar y filtrar.
- **Pendiente (R-02):** cómo nace una relación desde una invitación y quién la acepta.

## Riesgos identificados

| Riesgo | Mitigación |
| --- | --- |
| Los contadores guardados (`num_contratos`, `cumplimiento_pct`) se desfasan | Se recalculan en el back cada vez que cambia un contrato o el cumplimiento de la relación; ruta de recálculo manual para soporte |
| Las invitaciones (por definir) obliguen a cambiar el modelo | La relación no depende de cómo nació; la invitación será su propia forma y al aceptarse crea la relación |
| Ciclos o cadenas largas que hagan lento el árbol | Validación al guardar y nivel máximo 3 |

## Lo que **no** está en esta spec

- Invitaciones (R-02), árbol en pantalla (R-08), sanciones (R-07).
- Contratos y cumplimiento: SPEC contratos-001.
