import csv
import json
from pathlib import Path
from typing import Dict, List, Set

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


def read_controls(control_csv_path: Path) -> dict:
    controls_by_id: dict[int, dict] = {}
    with control_csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                control_id = int(row["id"]) if row.get("id") else None
            except Exception:
                continue
            if control_id is None:
                continue
            controls_by_id[control_id] = {
                "control_name": row.get("control_name"),
                "family_name": row.get("family_name"),
                "control_long_name": row.get("control_long_name"),
            }
    return controls_by_id


def read_checks(checks_csv_path: Path) -> list[dict]:
    checks: list[dict] = []
    with checks_csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            check_id = row.get("id")
            name = row.get("name") or row.get("metadata.operation.name") or ""
            if not check_id:
                continue
            checks.append({
                "id": str(check_id),
                "name": name,
            })
    return checks


def build_mappings(checks: list[dict]) -> dict:
    # Structure: { "<check_id>": { "check_name": str, "controls": [int], "reasoning": str } }
    mappings: dict[str, dict] = {}
    for chk in checks:
        mappings[str(chk["id"])] = {
            "check_name": chk.get("name", ""),
            # Placeholder empty list; domain mappings can be added later or by separate logic
            "controls": [],
            "reasoning": ""
        }
    return mappings


def build_control_name_to_id_index(controls_by_id: Dict[int, dict]) -> Dict[str, int]:
    name_to_id: Dict[str, int] = {}
    for cid, info in controls_by_id.items():
        name = (info.get("control_name") or "").strip()
        if name:
            name_to_id[name] = cid
    return name_to_id


def extract_nist_control_code(unique_id: str) -> str | None:
    # Examples: "NIST-800-53-AU-2", "NIST-800-53-AC-6", "NIST-800-53-CM-3"
    if not unique_id:
        return None
    if not unique_id.startswith("NIST-800-53-"):
        return None
    try:
        parts = unique_id.split("-")
        # Expect ...-<FAMILY>-<NUMBER>[...]
        if len(parts) < 5:
            return None
        # Reconstruct control like "AU-2" from last two parts
        family = parts[3]
        number = parts[4]
        # Some controls may include subparts (e.g., AC-3-1-5). Capture any remaining suffix
        if len(parts) > 5:
            suffix = "-".join(parts[5:])
            return f"{family}-{number}-{suffix}"
        return f"{family}-{number}"
    except Exception:
        return None


def load_yaml_controls(yaml_dir: Path) -> Dict[str, Dict[str, List[str]]]:
    """Return mapping: check_unique_id -> { 'nist_codes': [..], 'reasons': [..] }"""
    result: Dict[str, Dict[str, List[str]]] = {}
    if yaml is None:
        return result
    if not yaml_dir.exists():
        return result

    for ypath in yaml_dir.glob("*.yaml"):
        try:
            with ypath.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        check = data.get("check") or {}
        check_id = (check.get("unique_id") or "").strip()
        if not check_id:
            continue
        controls: List[dict] = check.get("controls") or []
        nist_codes: List[str] = []
        reasons: List[str] = []
        for c in controls:
            uid = (c.get("unique_id") or "").strip()
            reason = (c.get("reason") or "").strip()
            code = extract_nist_control_code(uid)
            if code:
                nist_codes.append(code)
                if reason:
                    reasons.append(reason)
        if nist_codes:
            result[check_id] = {"nist_codes": nist_codes, "reasons": reasons}
    return result


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    data_dir = root / "data" / "csv"
    control_csv_path = data_dir / "control.csv"
    checks_csv_path = data_dir / "checks.csv"
    yaml_dir = root / "llm_generator" / "data" / "debugging" / "sec1_benchmark_and_checks_literature" / "step3_enrich_individual_checks" / "output"
    sec3_dir = root / "llm_generator" / "data" / "debugging" / "sec3_checks_with_python_logic" / "step4_consolidate_repaired_checks" / "output"

    # Read inputs
    controls_by_id = read_controls(control_csv_path)
    control_name_to_id = build_control_name_to_id_index(controls_by_id)
    checks = read_checks(checks_csv_path)
    yaml_map = load_yaml_controls(yaml_dir)

    # Build mappings skeleton
    mappings = build_mappings(checks)

    # Populate controls from YAML by matching NIST control codes to control.csv names
    # and YAML check unique_id to checks.csv id (which uses the same owasp-latest ids)
    for chk in checks:
        chk_id = str(chk["id"])
        y = yaml_map.get(chk_id)
        if not y:
            continue
        codes: List[str] = y.get("nist_codes", [])
        reasons: List[str] = y.get("reasons", [])
        matched_ids: List[int] = []
        seen: Set[int] = set()
        for code in codes:
            cid = control_name_to_id.get(code)
            if cid is not None and cid not in seen:
                matched_ids.append(cid)
                seen.add(cid)
        if matched_ids:
            mappings[chk_id]["controls"] = matched_ids
            if reasons:
                mappings[chk_id]["reasoning"] = "; ".join(reasons)

    # Expand mappings to resource-suffixed check IDs found in sec3 consolidated outputs
    suffixed_ids: list[str] = []
    if sec3_dir.exists():
        # Build a list of resource-suffixed IDs from filenames (stem without extension)
        suffixed_ids = [p.stem for p in sec3_dir.glob("*.yaml")]
        base_ids = set(mappings.keys())
        for full_id in suffixed_ids:
            # Map to base id by prefix match (base + '-')
            matched_base: str | None = None
            for b in base_ids:
                if full_id.startswith(b + "-"):
                    matched_base = b
                    break
            if not matched_base:
                continue
            # Clone mapping from base to full id
            base_map = mappings.get(matched_base)
            if not base_map:
                continue
            if full_id not in mappings:
                mappings[full_id] = {
                    "check_name": full_id,
                    "controls": list(base_map.get("controls", [])),
                    "reasoning": base_map.get("reasoning", "")
                }

    # If sec3 exists, restrict output strictly to suffixed ids present there
    if suffixed_ids:
        mappings = {k: v for k, v in mappings.items() if k in set(suffixed_ids)}

    # Write output
    output_path = root / "llm_analyzed_mappings.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(mappings, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(mappings)} mappings to {output_path}")


if __name__ == "__main__":
    main()


