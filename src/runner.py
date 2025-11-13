thonimport argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

from extractors.facebook_parser import FacebookPageScraper
from outputs.exporters import export_data

def _configure_logging(level_name: str) -> None:
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )

def _load_config(config_path: Path) -> Dict[str, Any]:
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found at {config_path}")
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)

def _resolve_paths(config: Dict[str, Any], project_root: Path) -> Dict[str, Any]:
    """
    Resolve paths relative to the project root for inputs and outputs.
    """
    resolved_config = dict(config)

    input_file = Path(config.get("input_file", "data/inputs.sample.txt"))
    if not input_file.is_absolute():
        input_file = project_root / input_file
    resolved_config["input_file"] = input_file

    output_directory = Path(config.get("output_directory", "data/output"))
    if not output_directory.is_absolute():
        output_directory = project_root / output_directory
    resolved_config["output_directory"] = output_directory

    return resolved_config

def _read_input_urls(input_file: Path, max_pages: int) -> List[str]:
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found at {input_file}")

    urls: List[str] = []
    with input_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            urls.append(line)
            if max_pages and len(urls) >= max_pages:
                break

    return urls

def main(argv: List[str] | None = None) -> None:
    """
    Entry point for the Facebook Pages Scraper.

    Usage: