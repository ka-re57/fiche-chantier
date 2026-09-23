#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Remplit la note de dimensionnement MaPrime Facile (gabarit « NDD MPF 171-172.xlsx »)
à partir d'une fiche chantier KA-RÉ (payload JSON de l'appli, clé note_de_dimensionnement).

Le gabarit n'est jamais réécrit par une bibliothèque : on ne touche que les cellules
variables dans xl/worksheets/sheet1.xml, tout le reste du paquet est recopié à l'octet.
Excel recalcule les formules à l'ouverture (fullCalcOnLoad) ; Google Sheets aussi.

Usage : ndd_remplir.py <gabarit.xlsx> <fiche.json> <sortie.xlsx>
"""
import io, json, re, sys, zipfile
from xml.sax.saxutils import escape

ENTREPRISE = {"B2": "SARL KA-RÉ", "B3": "13 Rue de la Lâche", "B4": "57530", "B5": "Raville",
              "B6": "983 668 567 00016"}
CRANS = [0.4, 0.6, 0.65, 0.8, 1, 1.4, 2]

def nombre(v):
    if v is None or v == "": return None
    try: return float(str(v).replace(",", "."))
    except ValueError: return None

def valeurs_depuis_fiche(fiche):
    """Cellule -> valeur (str = texte, float/int = nombre, None = vider)."""
    N = fiche.get("note_de_dimensionnement") or {}
    C = fiche.get("client") or {}
    M = fiche.get("maison") or {}
    B = N.get("beneficiaire") or {}
    pac = N.get("pac") or {}
    v = dict(ENTREPRISE)
    civ = (B.get("civilite") or "").strip()
    nom = (B.get("nom") or C.get("nom") or "").strip()
    v["C10"] = (civ + " " + nom).strip()
    adr = " ".join(x for x in [(B.get("adresse") or C.get("adresse") or "").strip(),
                               (B.get("commune") or C.get("commune") or "").strip()] if x)
    if B.get("parcelle"): adr += " — parcelle n° " + str(B["parcelle"]).strip()
    v["C11"] = adr
    v["E8"] = "AIR/EAU"
    g = nombre(N.get("coefficient_G"))
    v["D23"] = g if g in CRANS else None            # doit être un cran du gabarit, sinon vide
    v["D24"] = nombre(N.get("surface_chauffee_m2"))
    v["D25"] = nombre(N.get("hauteur_sous_plafond_m"))
    tb = nombre(N.get("temperature_base_C"))
    if tb is None: tb = nombre(M.get("temperature_base_C"))
    v["B42"] = tb
    ta = nombre(pac.get("temperature_arret_C"))
    # une température d'arrêt au-dessus de 0 °C est une erreur de saisie (65 vu sur MAGAR) : on laisse vide
    v["E57"] = ta if (ta is not None and ta <= 0) else None
    p = nombre(pac.get("puissance_kW"))
    donnee = (pac.get("puissance_donnee_a") or "").lower()
    v["E58"] = v["E59"] = v["E60"] = None
    if p is not None:
        if "nominale" in donnee: v["E60"] = p
        elif "7" in donnee:      v["E59"] = p
        else:                    v["E58"] = p        # à T base (défaut de l'appli)
    return v

def cellule_xml(ref, style_attrs, val):
    """Reconstruit <c r=ref ...> avec la valeur voulue, en gardant le style s="..."."""
    s = re.search(r'\ss="\d+"', style_attrs)
    s = s.group(0) if s else ""
    if val is None:
        return '<c r="%s"%s/>' % (ref, s)
    if isinstance(val, str):
        return '<c r="%s"%s t="inlineStr"><is><t xml:space="preserve">%s</t></is></c>' % (ref, s, escape(val))
    num = ("%g" % val) if isinstance(val, float) else str(val)
    return '<c r="%s"%s><v>%s</v></c>' % (ref, s, num)

def remplacer_cellule(xml, ref, val):
    # cellule vide : <c r="B2" s="27"/>  — ou pleine : <c r="E57" s="17"><v>0</v></c>
    pat = re.compile(r'<c r="%s"([^>]*?)(/>|>.*?</c>)' % re.escape(ref), re.S)
    m = pat.search(xml)
    if not m:
        raise SystemExit("cellule absente du gabarit : " + ref)
    attrs = m.group(1)
    if "<f" in m.group(2):
        raise SystemExit("refus : la cellule %s porte une formule du gabarit" % ref)
    return xml[:m.start()] + cellule_xml(ref, attrs, val) + xml[m.end():]

def remplir(gabarit, fiche, sortie):
    fiche = json.load(io.open(fiche, encoding="utf-8"))
    vals = valeurs_depuis_fiche(fiche)
    zin = zipfile.ZipFile(gabarit)
    zout = zipfile.ZipFile(sortie, "w", zipfile.ZIP_DEFLATED)
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename == "xl/worksheets/sheet1.xml":
            xml = data.decode("utf-8")
            for ref, val in vals.items():
                xml = remplacer_cellule(xml, ref, val)
            data = xml.encode("utf-8")
        elif item.filename == "xl/workbook.xml":
            xml = data.decode("utf-8")
            if "fullCalcOnLoad" not in xml:
                xml = xml.replace("<calcPr ", '<calcPr fullCalcOnLoad="1" ', 1)
            data = xml.encode("utf-8")
        zout.writestr(item, data)
    zout.close()
    return vals

if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    v = remplir(sys.argv[1], sys.argv[2], sys.argv[3])
    for k in sorted(v): print(k, "=", v[k])
