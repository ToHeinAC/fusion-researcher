#!/usr/bin/env python3
"""CLI script for syncing database from merged Fusion_Research.md."""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.database import get_database
from src.services.database_sync_service import DatabaseSyncService, SyncConfig
from src.llm.chain_factory import get_llm


def main():
    parser = argparse.ArgumentParser(
        description="Sync database from Fusion Research markdown file using LLM"
    )
    parser.add_argument(
        "--markdown-file",
        default="research/Fusion_Research.md",
        help="Path to markdown file (default: research/Fusion_Research.md)",
    )
    parser.add_argument(
        "--database",
        default="research/fusion_research.db",
        help="Path to SQLite database (default: research/fusion_research.db)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying them",
    )
    parser.add_argument(
        "--auto-apply-threshold",
        type=float,
        default=0.90,
        help="Confidence threshold for auto-applying changes (default: 0.90)",
    )
    parser.add_argument(
        "--review-threshold",
        type=float,
        default=0.70,
        help="Minimum confidence to create proposal for review (default: 0.70)",
    )
    parser.add_argument(
        "--model",
        default="qwen3:8b",
        help="Ollama model to use for validation (default: qwen3:8b)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of companies to process per batch (default: 10)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Database Sync from Markdown")
    print("=" * 60)

    # Check markdown file exists
    markdown_path = Path(args.markdown_file)
    if not markdown_path.exists():
        print(f"Error: Markdown file not found: {markdown_path}")
        return 1

    print(f"\nSource:     {markdown_path}")
    print(f"Database:   {args.database}")
    print(f"Model:      {args.model}")
    print(f"Auto-apply: >= {args.auto_apply_threshold:.0%} confidence")
    print(f"Review:     >= {args.review_threshold:.0%} confidence")

    if args.dry_run:
        print("\n[DRY RUN - No changes will be applied]")

    # Initialize database
    print("\nInitializing database...")
    try:
        db = get_database(args.database)
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return 1

    # Initialize LLM
    print("Initializing LLM...")
    try:
        llm = get_llm(model=args.model)
    except Exception as e:
        print(f"Error initializing LLM: {e}")
        print("Make sure Ollama is running: ollama serve")
        return 1

    # Configure sync service
    config = SyncConfig(
        auto_apply_threshold=args.auto_apply_threshold,
        require_review_threshold=args.review_threshold,
        batch_size=args.batch_size,
        dry_run=args.dry_run,
    )

    sync_service = DatabaseSyncService(
        db=db,
        llm=llm,
        config=config,
    )

    # Perform sync
    print("\nSyncing database from markdown...")
    print("-" * 40)

    result = sync_service.sync_from_markdown(args.markdown_file)

    # Report results
    print("\n" + "=" * 60)
    print("Sync Results")
    print("=" * 60)
    print(f"  Companies processed:    {result.companies_processed}")
    print(f"  Companies added:        {result.companies_added}")
    print(f"  Companies updated:      {result.companies_updated}")
    print(f"  Fields updated:         {result.fields_updated}")
    print(f"  Proposals created:      {result.proposals_created}")
    print(f"  Auto-applied:           {result.proposals_auto_applied}")
    print(f"  Conflicts found:        {result.conflicts_found}")

    if result.errors:
        print("\nErrors:")
        for error in result.errors:
            print(f"  - {error}")
        return 1

    # Show pending proposals if any
    if result.proposals_created > 0 and not args.dry_run:
        print(f"\n{result.proposals_created} proposals pending review.")
        print("Use the Streamlit app or API to review and approve them.")

    print("\nSync completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
