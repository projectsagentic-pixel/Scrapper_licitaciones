"""Parse PLACSP ATOM feeds for lote A — CPV 72000000/72200000/72260000, presupuesto 20k-200k EUR, plazo vigente."""
import os
import glob
import json
import re
import hashlib
import datetime
from xml.etree import ElementTree as ET

ATOM_NS = "{http://www.w3.org/2005/Atom}"
CBC = "{urn:dgpe:names:draft:codice:schema:xsd:CommonBasicComponents-2}"
CAC = "{urn:dgpe:names:draft:codice:schema:xsd:CommonAggregateComponents-2}"
CACE = "{urn:dgpe:names:draft:codice-place-ext:schema:xsd:CommonAggregateComponents-2}"
CBCE = "{urn:dgpe:names:draft:codice-place-ext:schema:xsd:CommonBasicComponents-2}"

CPV_TARGETS_PREFIX = ("72000000", "72200000", "72260000")
# Also accept any CPV starting with 7220, 7226 for broader match (still software dev/services)
CPV_BROAD_PREFIXES = ("722", "7226")

PRESUP_MIN = 20000.0
PRESUP_MAX = 200000.0
TODAY = datetime.date(2026, 5, 16)
MIN_PLAZO_DIAS = 7

EXTRACTED_DIR = os.path.dirname(os.path.abspath(__file__)) + "/extracted"

# Load hashes/ids to skip
HASHES_PATH = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "_tmp_hashes_a_evitar.json"))
with open(HASHES_PATH, "r", encoding="utf-8") as f:
    avoid = json.load(f)
AVOID_HASHES = set(avoid["hashes"])
AVOID_IDS = set(avoid["ids_oficiales"])


def get_text(el, path):
    if el is None:
        return None
    n = el.find(path)
    if n is None:
        return None
    return (n.text or "").strip() or None


def get_all_text(el, path):
    if el is None:
        return []
    return [(n.text or "").strip() for n in el.findall(path) if n.text]


def parse_iso_date(s):
    if not s:
        return None
    s = s.strip()
    m = re.match(r"(\d{4}-\d{2}-\d{2})", s)
    if not m:
        return None
    try:
        return datetime.date.fromisoformat(m.group(1))
    except Exception:
        return None


def parse_entry(entry_el):
    """Return dict with relevant fields, or None if not matching filters."""
    summary = (get_text(entry_el, f"{ATOM_NS}summary") or "").strip()
    title = (get_text(entry_el, f"{ATOM_NS}title") or "").strip()
    link_el = entry_el.find(f"{ATOM_NS}link")
    link_href = link_el.get("href") if link_el is not None else None

    cfs = entry_el.find(f"{CACE}ContractFolderStatus")
    if cfs is None:
        return None

    id_oficial = get_text(cfs, f"{CBC}ContractFolderID")
    status_code = get_text(cfs, f"{CBCE}ContractFolderStatusCode")
    # Only PUB (published, open for bids)
    if status_code != "PUB":
        return None

    # CPV codes
    cpv_codes = []
    for rcc in cfs.findall(f"{CAC}ProcurementProject/{CAC}RequiredCommodityClassification"):
        c = get_text(rcc, f"{CBC}ItemClassificationCode")
        if c:
            cpv_codes.append(c)
    # Also possibly in lots
    for rcc in cfs.findall(f".//{CAC}RequiredCommodityClassification"):
        c = get_text(rcc, f"{CBC}ItemClassificationCode")
        if c and c not in cpv_codes:
            cpv_codes.append(c)

    if not cpv_codes:
        return None

    # Filter: target CPVs
    target_cpv_match = False
    for c in cpv_codes:
        if c in CPV_TARGETS_PREFIX or c.startswith("722") or c.startswith("7226"):
            target_cpv_match = True
            break
    if not target_cpv_match:
        return None

    # Budget
    ba = cfs.find(f"{CAC}ProcurementProject/{CAC}BudgetAmount")
    presup_base = None
    presup_total = None
    if ba is not None:
        try:
            v = get_text(ba, f"{CBC}TaxExclusiveAmount")
            if v:
                presup_base = float(v)
        except Exception:
            pass
        try:
            v = get_text(ba, f"{CBC}TotalAmount")
            if v:
                presup_total = float(v)
        except Exception:
            pass

    # Use TaxExclusiveAmount (base) for filter, fallback total
    presup_filter = presup_base if presup_base is not None else presup_total
    if presup_filter is None:
        return None
    if presup_filter < PRESUP_MIN or presup_filter > PRESUP_MAX:
        return None

    # Title and description
    proj_name = get_text(cfs, f"{CAC}ProcurementProject/{CBC}Name") or title

    # Object / description
    descripcion = None
    for cand in [
        f"{CAC}ProcurementProject/{CBC}Description",
        f"{CAC}ProcurementProject/{CAC}ContractExtension/{CBCE}Description",
    ]:
        v = get_text(cfs, cand)
        if v:
            descripcion = v
            break

    # Organo de contratación
    organo = None
    org_el = cfs.find(f"{CACE}LocatedContractingParty/{CAC}Party/{CAC}PartyName/{CBC}Name")
    if org_el is not None:
        organo = (org_el.text or "").strip()

    # Tender deadline
    plazo = None
    # tender period end
    tp = cfs.find(f"{CAC}TenderingProcess/{CAC}TenderSubmissionDeadlinePeriod")
    if tp is not None:
        d = get_text(tp, f"{CBC}EndDate")
        plazo = parse_iso_date(d)
    if plazo is None:
        # try other paths
        for p in [
            f"{CAC}TenderingTerms/{CAC}TendererQualificationRequest/{CAC}SpecificTendererRequirement/{CBC}Description",
        ]:
            pass

    if plazo is None:
        # If no deadline visible in feed, skip (cannot verify vigente)
        return None
    days_left = (plazo - TODAY).days
    if days_left < MIN_PLAZO_DIAS:
        return None

    # Lugar de ejecución
    lugar = None
    rl = cfs.find(f"{CAC}ProcurementProject/{CAC}RealizedLocation")
    if rl is not None:
        lugar = get_text(rl, f"{CBC}CountrySubentity") or get_text(rl, f"{CAC}Address/{CBC}CityName")

    # Type of contract
    type_code = get_text(cfs, f"{CAC}ProcurementProject/{CBC}TypeCode")
    subtype_code = get_text(cfs, f"{CAC}ProcurementProject/{CBC}SubTypeCode")

    # Pliego URLs
    url_pcap = None
    url_ppt = None
    for doc in cfs.findall(f".//{CAC}LegalDocumentReference"):
        att = doc.find(f"{CAC}Attachment/{CAC}ExternalReference/{CBC}URI")
        if att is not None and att.text:
            if url_pcap is None:
                url_pcap = att.text.strip()
    for doc in cfs.findall(f".//{CAC}TechnicalDocumentReference"):
        att = doc.find(f"{CAC}Attachment/{CAC}ExternalReference/{CBC}URI")
        if att is not None and att.text:
            if url_ppt is None:
                url_ppt = att.text.strip()

    # Duration
    duracion = None
    for p in [f"{CAC}ProcurementProject/{CAC}PlannedPeriod/{CBC}DurationMeasure",
              f"{CAC}ProcurementProject/{CAC}PlannedPeriod/{CBC}EndDate"]:
        v = get_text(cfs, p)
        if v:
            duracion = v
            break

    return {
        "id_oficial": id_oficial,
        "url_oficial": link_href,
        "titulo": proj_name or title,
        "descripcion": descripcion,
        "summary_atom": summary,
        "organo_contratante": organo,
        "presupuesto_base_eur": presup_base,
        "presupuesto_total_eur": presup_total,
        "plazo_presentacion": plazo.isoformat() if plazo else None,
        "cpv_codigos": cpv_codes,
        "lugar_ejecucion": lugar,
        "tipo_contrato_codigo": type_code,
        "subtipo_contrato_codigo": subtype_code,
        "url_pliego_pcap": url_pcap,
        "url_pliego_ppt": url_ppt,
        "duracion": duracion,
        "dias_hasta_plazo": days_left,
    }


def process_file(path):
    out = []
    try:
        # iterparse to control memory
        ctx = ET.iterparse(path, events=("end",))
        for event, el in ctx:
            tag = el.tag
            if tag == f"{ATOM_NS}entry":
                try:
                    r = parse_entry(el)
                    if r is not None:
                        out.append(r)
                except Exception as e:
                    pass
                el.clear()
    except ET.ParseError as e:
        print(f"  parse error in {os.path.basename(path)}: {e}")
    return out


def main():
    files = sorted(glob.glob(EXTRACTED_DIR + "/*.atom"))
    print(f"Found {len(files)} atom files")
    all_matches = []
    seen_ids = set()
    for i, f in enumerate(files):
        results = process_file(f)
        for r in results:
            if r["id_oficial"] in seen_ids:
                continue
            seen_ids.add(r["id_oficial"])
            all_matches.append(r)
        if (i + 1) % 20 == 0:
            print(f"  processed {i+1}/{len(files)} files, {len(all_matches)} matches so far")
    print(f"TOTAL matches before dedup: {len(all_matches)}")

    # Dedup against avoid list
    final = []
    descartes_dedup = 0
    for r in all_matches:
        id_oficial = r["id_oficial"]
        h = hashlib.sha256(id_oficial.encode("utf-8")).hexdigest()[:16]
        if h in AVOID_HASHES or id_oficial in AVOID_IDS:
            descartes_dedup += 1
            continue
        r["hash"] = h
        final.append(r)

    print(f"After dedup: {len(final)} (descartes dedup: {descartes_dedup})")

    # Save raw matches
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "matches_raw.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "total_raw": len(all_matches),
            "total_after_dedup": len(final),
            "descartes_dedup": descartes_dedup,
            "matches": final,
        }, f, indent=2, ensure_ascii=False)
    print(f"Saved to {out_path}")


if __name__ == "__main__":
    main()
