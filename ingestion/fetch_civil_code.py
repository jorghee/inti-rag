"""Script to download, structure, and persist the Peruvian Civil Code from SPIJ."""

import argparse
import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from ingestion.spij_client import SpijClient

logger = logging.getLogger("inti.ingestion.fetch_civil_code")

STATUTE_CODE = "CODIGO_CIVIL_1984"
OFFICIAL_SPIJ_URL = "https://spij.minjus.gob.pe/spij-ext-web/#/detallenorma/H682695"
SPIJ_ENDPOINT = "/spij-ext-web/detallenorma/H682695"

ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_RAW_DIR = ROOT_DIR / "data" / "raw"
DEFAULT_OUTPUT_FILE = DEFAULT_RAW_DIR / "codigo_civil_1984.html"
DEFAULT_LOG_FILE = DEFAULT_RAW_DIR / "ingestion_civil_code.json"
FIXTURE_MIRROR_PATH = Path(__file__).resolve().parent / "fixtures" / "spij_civil_code_mirror.html"


async def fetch_civil_code(
    output_path: Optional[Path] = None,
    log_path: Optional[Path] = None,
    allow_fallback: bool = True,
    force_fallback: bool = False,
    client: Optional[SpijClient] = None,
) -> Dict[str, Any]:
    """Download Peruvian Civil Code text from official SPIJ portal with fallback.

    Args:
        output_path: Path to save the extracted raw HTML content.
        log_path: Path to save JSON telemetry execution log.
        allow_fallback: Whether to use bundled official mirror if network fails.
        force_fallback: Directly use bundled official mirror without remote call.
        client: Optional pre-configured SpijClient instance.

    Returns:
        Execution telemetry dictionary.
    """
    target_output = output_path or DEFAULT_OUTPUT_FILE
    target_log = log_path or DEFAULT_LOG_FILE

    target_output.parent.mkdir(parents=True, exist_ok=True)
    target_log.parent.mkdir(parents=True, exist_ok=True)

    start_time = time.monotonic()
    raw_content: Optional[str] = None
    source = "spij_live"
    http_status: Optional[int] = None

    if not force_fallback:
        own_client = client is None
        spij_client = client or SpijClient()
        try:
            logger.info("Connecting to official SPIJ portal at %s...", OFFICIAL_SPIJ_URL)
            response = await spij_client.get(SPIJ_ENDPOINT)
            http_status = response.status_code
            raw_content = response.text
            logger.info(
                "Successfully downloaded raw Civil Code payload (%d bytes)",
                len(raw_content),
            )
        except Exception as exc:
            logger.warning("SPIJ remote extraction encountered error: %s", exc)
            if not allow_fallback:
                raise
        finally:
            if own_client:
                await spij_client.close()

    if raw_content is None:
        if not allow_fallback and not force_fallback:
            raise RuntimeError(
                "Failed to retrieve statutory text from SPIJ and fallback was disabled."
            )
        logger.info(
            "Loading bundled official SPIJ mirror fixture from %s...",
            FIXTURE_MIRROR_PATH,
        )
        if not FIXTURE_MIRROR_PATH.is_file():
            raise FileNotFoundError(f"Fixture mirror file not found at {FIXTURE_MIRROR_PATH}")
        raw_content = FIXTURE_MIRROR_PATH.read_text(encoding="utf-8")
        source = "official_spij_mirror_fallback"
        http_status = 200

    duration = time.monotonic() - start_time
    content_bytes = raw_content.encode("utf-8")
    sha256_checksum = hashlib.sha256(content_bytes).hexdigest()

    # Persist raw statutory payload
    target_output.write_text(raw_content, encoding="utf-8")

    telemetry: Dict[str, Any] = {
        "statute_code": STATUTE_CODE,
        "official_spij_url": OFFICIAL_SPIJ_URL,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": round(duration, 3),
        "bytes_extracted": len(content_bytes),
        "sha256": sha256_checksum,
        "source": source,
        "http_status": http_status,
        "output_file": str(target_output),
        "status": "success",
    }

    # Persist execution log
    target_log.write_text(json.dumps(telemetry, indent=2), encoding="utf-8")

    logger.info(
        "Civil Code extraction completed in %.2fs. Checksum: %s",
        duration,
        sha256_checksum[:12],
    )
    return telemetry


def main() -> None:
    """CLI execution entrypoint."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    parser = argparse.ArgumentParser(
        description="Extract and structure Peruvian Civil Code from SPIJ.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_FILE,
        help="Destination path for raw HTML payload.",
    )
    parser.add_argument(
        "--log",
        type=Path,
        default=DEFAULT_LOG_FILE,
        help="Destination path for telemetry log JSON.",
    )
    parser.add_argument(
        "--no-fallback",
        action="store_true",
        help="Disable mirror fallback if remote SPIJ is unreachable.",
    )
    parser.add_argument(
        "--force-mirror",
        action="store_true",
        help="Directly use bundled official mirror without remote call.",
    )

    args = parser.parse_args()

    asyncio.run(
        fetch_civil_code(
            output_path=args.output,
            log_path=args.log,
            allow_fallback=not args.no_fallback,
            force_fallback=args.force_mirror,
        )
    )


if __name__ == "__main__":
    main()
