#!/usr/bin/env python3
"""
Receipt Verification CLI

Verifies receipts across IDE/Tenant/Shared planes for end-to-end lineage.
"""

import json
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List
from validator.receipt_validator import ReceiptValidator

logger = logging.getLogger(__name__)


def verify_receipt_file(file_path: Path) -> Dict[str, Any]:
    """Verify a single receipt JSONL file."""
    validator = ReceiptValidator()
    return validator.validate_jsonl_file(file_path)


def find_receipt_files(root_dir: Path) -> List[Path]:
    """Find all receipt.jsonl files in directory tree."""
    receipt_files = []
    for jsonl_file in root_dir.rglob('receipts.jsonl'):
        if jsonl_file.is_file():
            receipt_files.append(jsonl_file)
    return sorted(receipt_files)


def verify_receipts_in_plane(plane_dir: Path, plane_name: str) -> Dict[str, Any]:
    """Verify all receipts in a storage plane."""
    logger.info(f"\nVerifying {plane_name} plane: {plane_dir}")

    if not plane_dir.exists():
        return {
            'plane': plane_name,
            'status': 'missing',
            'message': f"Plane directory does not exist: {plane_dir}"
        }

    receipt_files = find_receipt_files(plane_dir)

    if not receipt_files:
        return {
            'plane': plane_name,
            'status': 'empty',
            'message': f"No receipt files found in {plane_dir}",
            'files_checked': 0
        }

    total_valid = 0
    total_receipts = 0
    all_errors = []

    for receipt_file in receipt_files:
        result = verify_receipt_file(receipt_file)
        if result['valid']:
            total_valid += result['valid_count']
        total_receipts += result['total_count']
        all_errors.extend(result.get('errors_by_line', []))

    return {
        'plane': plane_name,
        'status': 'ok' if len(all_errors) == 0 else 'errors',
        'files_checked': len(receipt_files),
        'total_receipts': total_receipts,
        'valid_receipts': total_valid,
        'errors': all_errors
    }


def main():
    """Main entry point."""
    import os

    zu_root = os.getenv('ZU_ROOT', os.path.expanduser('~/.zeroui'))
    zu_root_path = Path(zu_root)

    logger.info("=" * 80)
    logger.info("RECEIPT VERIFICATION - END-TO-END LINEAGE CHECK")
    logger.info("=" * 80)
    logger.info(f"ZU_ROOT: {zu_root_path}")

    # Verify receipts in each plane
    planes = {
        'IDE': zu_root_path / 'ide' / 'receipts',
        'Tenant': zu_root_path / 'tenant' / 'evidence',
        'Shared': zu_root_path / 'shared' / 'audit'
    }

    results = []
    for plane_name, plane_dir in planes.items():
        result = verify_receipts_in_plane(plane_dir, plane_name)
        results.append(result)

        if result['status'] == 'ok':
            logger.info(f"  [OK] {plane_name}: {result.get('valid_receipts', 0)}/{result.get('total_receipts', 0)} receipts valid")
        elif result['status'] == 'errors':
            logger.error(f"  [FAIL] {plane_name}: {len(result.get('errors', []))} errors found")
            for error in result['errors'][:5]:  # Show first 5 errors
                logger.error(f"    Line {error['line']}: {error['errors'][0]}")
        else:
            logger.warning(f"  [SKIP] {plane_name}: {result.get('message', 'N/A')}")

    # Summary
    logger.info("\n" + "=" * 80)
    total_errors = sum(len(r.get('errors', [])) for r in results)
    if total_errors == 0:
        logger.info("[SUCCESS] All receipts valid")
        return 0
    else:
        logger.error(f"[FAILURE] {total_errors} receipt validation errors found")
        return 1


if __name__ == '__main__':
    sys.exit(main())
