#!/usr/bin/env python3
"""Genera los XML de las formas de Contratistas (F0-02) a partir de defs.py.

Uso (desde clave10-sdk):  python3 bin/contratistas_forms/gen.py            -> escribe XML + field_ids.json + models_snippet.py
      python3 gen.py --check    -> solo valida y muestra el resumen

- Toma como plantilla campos reales de formas de accesos ya instaladas (un
  <item> por field_type) y les cambia id, etiqueta, opciones y grupo.
- Los field_id se guardan en field_ids.json para que no cambien entre corridas.
- Sube la versión (<description>version: N</description>) solo si el XML cambió,
  para que lkfaddons lo reinstale.
"""
import copy
import json
import os
import re
import sys
import time
import unicodedata
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(__file__))
from defs import EXTENSIONS, FORMS, flat  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))  # clave10-sdk
ADDONS = f"{ROOT}/addons/lkf_addons/addons/accesos/items/forms"
SRC = f"{ADDONS}/Seguridad"
OUT_DIR = f"{ADDONS}/Seguridad/Contratistas"
IDS_FILE = os.path.join(HERE, "field_ids.json")
SANIC_FIELDS = f"{ROOT}/lkf-sanic-apps/addons/accesos/contratistas_fields.py"

HEADER_SRC = f"{SRC}/Config/plantilla_por_caseta.xml"
TEMPLATE_SRCS = [
    f"{SRC}/Config/plantilla_por_caseta.xml",
    f"{SRC}/Config/horarios.xml",
    f"{SRC}/registro_de_asistencia.xml",
    f"{SRC}/pase_de_entrada_transportista.xml",
]
KINDS = ["text", "textarea", "integer", "decimal", "date", "datetime", "time",
         "files", "images", "select", "checkbox", "radio", "group"]

# Lo que se limpia en cada campo clonado (no debe arrastrar reglas ni catálogos).
RESET = {
    "affecting_rules": "[]", "buttons_ids": "[]", "catalog": "None", "catalog_fields": "[]",
    "catalog_relation": "None", "default": "False", "descriptor": "None", "fav": "False",
    "grading_criteria": "{}", "group": "None", "groups_fields": "[]", "number_type": "None",
    "options": "[]", "rules": "[]", "show_for_rule": "True", "validations": "{}", "visible": "True",
}


def slug(s):
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def new_id():
    return os.urandom(12).hex()


def set_simple(el, tag, text):
    child = el.find(tag)
    if child is None:
        child = ET.SubElement(el, tag)
    for c in list(child):
        child.remove(c)
    child.text = text


def load_templates():
    tpl = {}
    for path in TEMPLATE_SRCS:
        root = ET.parse(path).getroot()
        for it in root.iter("item"):
            ft = it.find("field_type")
            if ft is not None and ft.text in KINDS and ft.text not in tpl and it.find("properties") is not None:
                tpl[ft.text] = copy.deepcopy(it)
    missing = set(KINDS) - set(tpl)
    if missing:
        raise SystemExit(f"Sin plantilla para: {missing}")
    return tpl


def make_item(tpl, f, field_id, group_id=None, children_ids=None):
    it = copy.deepcopy(tpl[f["kind"]])
    for tag, val in RESET.items():
        set_simple(it, tag, val)
    set_simple(it, "field_id", field_id)
    set_simple(it, "label", f["label"])
    set_simple(it, "required", "True" if f.get("req") else "False")
    set_simple(it, "help_text", f.get("help") or "")
    props = it.find("properties")
    set_simple(props, "help_text", "True" if f.get("help") else "False")
    dv = it.find("default_value")
    if dv is not None:
        for c in list(dv):
            dv.remove(c)
        dv.text = None

    if f.get("opts"):
        opts = it.find("options")
        opts.text = None
        for label in f["opts"]:
            o = ET.SubElement(opts, "item")
            for tag, text in (("label", label), ("points", "None"), ("selected", "False"), ("value", slug(label))):
                ET.SubElement(o, tag).text = text
    if group_id:
        g = it.find("group")
        g.text = None
        ET.SubElement(g, "group_id").text = group_id
        ET.SubElement(g, "group_set_id").text = "0"
    if children_ids is not None:
        gf = it.find("groups_fields")
        gf.text = None
        for cid in children_ids:
            ET.SubElement(gf, "item").text = cid
        set_simple(props, "max", "0")
        set_simple(props, "min", "0")
    return it


def build_items(spec, tpl, ids):
    """Items de campo de spec['fields'] (grupos seguidos de sus hijos) y claves usadas."""
    form_ids = ids.setdefault(spec["slug"], {})

    def fid(key):
        if key not in form_ids:
            form_ids[key] = new_id()
        return form_ids[key]

    items, seen = [], set()

    def check(key):
        if key in seen:
            raise SystemExit(f"{spec['slug']}: clave repetida {key}")
        seen.add(key)

    for f in flat(spec["fields"]):
        check(f["key"])
        if f["kind"] == "group":
            gid = fid(f["key"])
            child_ids = []
            for ch in f["children"]:
                check(ch["key"])
                child_ids.append(fid(ch["key"]))
            items.append(make_item(tpl, f, gid, children_ids=child_ids))
            for ch, cid in zip(f["children"], child_ids):
                items.append(make_item(tpl, ch, cid, group_id=gid))
        else:
            items.append(make_item(tpl, f, fid(f["key"])))
    return items, [k for k in form_ids if k in seen]


def build_form(spec, tpl, ids):
    header = ET.parse(HEADER_SRC).getroot()
    page_fields = header.find("form_pages/item/page_fields")
    for c in list(page_fields):
        page_fields.remove(c)
    items, keys = build_items(spec, tpl, ids)
    page_fields.extend(items)
    set_simple(header, "name", spec["name"])
    return header, keys


PAGE_OPEN = "        <item>\n            <page_description>None</page_description>\n"


def extend_form(spec, tpl, ids, now):
    """Agrega (o reemplaza) la página spec['page'] al final del XML existente.

    Trabaja sobre el texto para no reformatear el resto del archivo. Regresa
    (texto, claves, estado)."""
    path = f"{ROOT}/addons/lkf_addons/addons/{spec['xml']}"
    old = open(path).read()
    base = old
    marker = f"<page_name>{spec['page']}</page_name>"
    if marker in base:
        end = base.index("</item>\n", base.index(marker)) + len("</item>\n")
        start = base.rindex(PAGE_OPEN, 0, base.index(marker))
        base = base[:start] + base[end:]
    items, keys = build_items(spec, tpl, ids)
    page = ET.Element("item")
    ET.SubElement(page, "page_description").text = "None"
    pf = ET.SubElement(page, "page_fields")
    pf.extend(items)
    ET.SubElement(page, "page_name").text = spec["page"]
    ET.SubElement(page, "page_type").text = "fields"
    ET.indent(page, space="    ", level=2)
    page_txt = "    " * 2 + ET.tostring(page, encoding="unicode").rstrip() + "\n"
    i = base.index("    </form_pages>")
    body = base[:i] + page_txt + base[i:]
    norm = lambda s: re.sub(r"<(description|updated_at)>.*?</\1>", "", s)
    if norm(old) == norm(body):
        return path, old, keys, "sin cambios"
    body = with_version(body, now)
    body = re.sub(r"<updated_at>.*?</updated_at>", f"<updated_at>{now}.0</updated_at>", body, count=1)
    return path, body, keys, "cambió"


def serialize(root):
    ET.indent(root, space="    ")
    return "<?xml version='1.0' encoding='utf-8'?>\n" + ET.tostring(root, encoding="unicode") + "\n"


def with_version(xml_text, version):
    return re.sub(r"<description>.*?</description>", f"<description>version: {version}</description>", xml_text, count=1)


def main():
    check_only = "--check" in sys.argv
    tpl = load_templates()
    ids = json.load(open(IDS_FILE)) if os.path.exists(IDS_FILE) else {}
    os.makedirs(OUT_DIR, exist_ok=True)
    now = int(time.time())
    snippet = [
        "# -*- coding: utf-8 -*-",
        "# Ids de campo de las formas de Contratistas (F0-02).",
        "# Generado desde las specs de clave10-sdk (specs/empresa, relaciones, contratos)",
        "# por clave10-sdk/bin/contratistas_forms/gen.py — no editar a mano: regenerar.",
        "#",
        "# Referencias entre formas por id (sin catálogos): <clave>_id guarda el _id",
        "# del registro y <clave> su nombre visible.",
        "",
        "CONTRATISTAS_FIELDS = {",
    ]
    for spec in FORMS:
        root, keys = build_form(spec, tpl, ids)
        set_simple(root, "created_at", f"{now}.0")
        body = serialize(root)
        path = f"{OUT_DIR}/{spec['slug']}.xml"
        old = open(path).read() if os.path.exists(path) else None
        # Comparar ignorando versión y fechas: solo subir versión si cambió algo real.
        norm = lambda s: re.sub(r"<(description|created_at|updated_at)>.*?</\1>", "", s or "")
        if old is not None and norm(old) == norm(body):
            status, out = "sin cambios", old
        else:
            status = "nuevo" if old is None else "cambió"
            out = with_version(body, now)
            out = re.sub(r"<updated_at>.*?</updated_at>", f"<updated_at>{now}.0</updated_at>", out, count=1)
        ET.fromstring(out.split("\n", 1)[1])  # well-formed
        n = len(keys)
        print(f"{spec['slug']:34} {n:3} campos  {status}")
        if not check_only and status != "sin cambios":
            open(path, "w").write(out)
        snippet.append(f"    '{spec['slug']}': {{")
        for k in keys:
            v = ids[spec["slug"]][k]
            snippet.append(f"        '{k}': '{v}',")
        snippet.append("    },")
    for spec in EXTENSIONS:
        path, out, keys, status = extend_form(spec, tpl, ids, now)
        ET.fromstring(out.split("\n", 1)[1])  # well-formed
        print(f"{spec['slug']:34} {len(keys):3} campos  {status} (página {spec['page']} en {spec['xml']})")
        if not check_only and status != "sin cambios":
            open(path, "w").write(out)
        snippet.append(f"    '{spec['slug']}': {{")
        for k in keys:
            snippet.append(f"        '{k}': '{ids[spec['slug']][k]}',")
        snippet.append("    },")
    snippet.append("}")
    snippet.append("")
    if not check_only:
        json.dump(ids, open(IDS_FILE, "w"), indent=2, ensure_ascii=False)
        open(SANIC_FIELDS, "w").write("\n".join(snippet))
        print(f"campos en {SANIC_FIELDS}")
        print(f"\nXML en {OUT_DIR}\nids en {IDS_FILE}")


if __name__ == "__main__":
    main()
