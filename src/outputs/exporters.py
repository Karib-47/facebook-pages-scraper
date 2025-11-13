thonimport json
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

import pandas as pd

logger = logging.getLogger(__name__)

def _ensure_output_dir(path: Path) -> None:
    if not path.exists():
        logger.debug("Creating output directory: %s", path)
        path.mkdir(parents=True, exist_ok=True)

def export_data(
    records: Iterable[Mapping[str, Any]],
    output_directory: str,
    formats: List[str],
    base_filename: str = "facebook_pages_data",
) -> Dict[str, Path]:
    """
    Export scraped records to the configured formats.

    Supported formats:
      - json: newline-delimited JSON
      - csv: comma-separated values
      - xlsx: Excel workbook
    """
    records_list = list(records)
    output_dir = Path(output_directory)
    _ensure_output_dir(output_dir)

    if not records_list:
        logger.warning("No records provided to export.")
        return {}

    df = pd.DataFrame(records_list)
    exported_paths: Dict[str, Path] = {}

    formats_normalized = {fmt.lower().strip() for fmt in formats}

    if "json" in formats_normalized:
        json_path = output_dir / f"{base_filename}.json"
        with json_path.open("w", encoding="utf-8") as f:
            for record in records_list:
                f.write(json.dumps(record, ensure_ascii=False))
                f.write("\n")
        exported_paths["json"] = json_path
        logger.info("Exported %d records to JSON at %s", len(records_list), json_path)

    if "csv" in formats_normalized:
        csv_path = output_dir / f"{base_filename}.csv"
        df.to_csv(csv_path, index=False)
        exported_paths["csv"] = csv_path
        logger.info("Exported %d records to CSV at %s", len(records_list), csv_path)

    if "xlsx" in formats_normalized or "excel" in formats_normalized:
        xlsx_path = output_dir / f"{base_filename}.xlsx"
        df.to_excel(xlsx_path, index=False)
        exported_paths["xlsx"] = xlsx_path
        logger.info(
            "Exported %d records to Excel at %s", len(records_list), xlsx_path
        )

    if not exported_paths:
        logger.warning(
            "No supported export formats requested. Received: %s", formats
        )

    return exported_paths