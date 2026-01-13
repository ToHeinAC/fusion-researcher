#!/usr/bin/env python3
"""CLI script for running the full update pipeline: merge markdown + sync database."""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.database import get_database
from src.services.markdown_merger_service import MarkdownMergerService, MergeConfig
from src.services.database_sync_service import DatabaseSyncService, SyncConfig
from src.llm.chain_factory import get_llm


def main():
    parser = argparse.ArgumentParser(
        description="Run full research update pipeline: merge markdown + sync database"
    )
    parser.add_argument(
        "--update-file",
        default="Fusion_Research_UPDATE.md",
        help="Name of the update file (default: Fusion_Research_UPDATE.md)",
    )
    parser.add_argument(
        "--base-file",
        default="Fusion_Research.md",
        help="Name of the base file (default: Fusion_Research.md)",
    )
    parser.add_argument(
        "--research-dir",
        default="research",
        help="Directory containing research files (default: research)",
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
        "--skip-merge",
        action="store_true",
        help="Skip markdown merge step",
    )
    parser.add_argument(
        "--skip-sync",
        action="store_true",
        help="Skip database sync step",
    )
    parser.add_argument(
        "--auto-apply-threshold",
        type=float,
        default=0.90,
        help="Confidence threshold for auto-applying DB changes (default: 0.90)",
    )
    parser.add_argument(
        "--model",
        default="qwen3:8b",
        help="Ollama model to use (default: qwen3:8b)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Full Research Update Pipeline")
    print("=" * 60)
    print(f"\nModel: {args.model}")

    if args.dry_run:
        print("[DRY RUN - No changes will be applied]")

    # Check required files
    base_path = Path(args.research_dir) / args.base_file
    update_path = Path(args.research_dir) / args.update_file

    if not args.skip_merge:
        if not base_path.exists():
            print(f"Error: Base file not found: {base_path}")
            return 1
        if not update_path.exists():
            print(f"Error: Update file not found: {update_path}")
            return 1

    # Initialize LLM
    print("\nInitializing LLM...")
    try:
        llm = get_llm(model=args.model)
    except Exception as e:
        print(f"Error initializing LLM: {e}")
        print("Make sure Ollama is running: ollama serve")
        return 1

    # Initialize database
    print("Initializing database...")
    try:
        db = get_database(args.database)
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return 1

    # Step 1: Merge markdown files
    merge_result = None
    if not args.skip_merge:
        print("\n" + "-" * 60)
        print("[Step 1/2] Merging Markdown Files")
        print("-" * 60)
        print(f"Base:   {base_path}")
        print(f"Update: {update_path}")

        merger = MarkdownMergerService(
            llm=llm,
            config=MergeConfig(),
            research_dir=args.research_dir,
        )

        if args.dry_run:
            # Preview mode
            base_content = base_path.read_text(encoding="utf-8")
            update_content = update_path.read_text(encoding="utf-8")

            base_sections = merger.extract_sections(base_content)
            update_sections = merger.extract_sections(update_content)
            diffs = merger.compare_sections(base_sections, update_sections)

            modified = sum(1 for d in diffs if d.diff_type.value == "modified")
            new = sum(1 for d in diffs if d.diff_type.value == "new")

            print(f"\nPreview: {modified} sections to modify, {new} new sections")
        else:
            merge_result = merger.merge_files(
                base_file=args.base_file,
                update_file=args.update_file,
            )

            if not merge_result.success:
                print("\nMerge failed:")
                for error in merge_result.errors:
                    print(f"  - {error}")
                return 1

            print(f"\nMerge completed:")
            print(f"  Sections merged:   {merge_result.sections_merged}")
            print(f"  Companies added:   {merge_result.companies_added}")
            print(f"  Companies updated: {merge_result.companies_updated}")
            if merge_result.backup_path:
                print(f"  Backup:            {merge_result.backup_path}")
    else:
        print("\n[Skipping merge step]")

    # Step 2: Sync database
    sync_result = None
    if not args.skip_sync:
        print("\n" + "-" * 60)
        print("[Step 2/2] Syncing Database from Markdown")
        print("-" * 60)

        sync_config = SyncConfig(
            auto_apply_threshold=args.auto_apply_threshold,
            dry_run=args.dry_run,
        )

        sync_service = DatabaseSyncService(
            db=db,
            llm=llm,
            config=sync_config,
        )

        markdown_path = str(base_path)
        sync_result = sync_service.sync_from_markdown(markdown_path)

        print(f"\nSync completed:")
        print(f"  Companies processed: {sync_result.companies_processed}")
        print(f"  Companies added:     {sync_result.companies_added}")
        print(f"  Fields updated:      {sync_result.fields_updated}")
        print(f"  Auto-applied:        {sync_result.proposals_auto_applied}")
        print(f"  Proposals created:   {sync_result.proposals_created}")

        if sync_result.errors:
            print("\nSync errors:")
            for error in sync_result.errors:
                print(f"  - {error}")
    else:
        print("\n[Skipping sync step]")

    # Final summary
    print("\n" + "=" * 60)
    print("Pipeline Complete")
    print("=" * 60)

    if args.dry_run:
        print("\nThis was a dry run. No changes were applied.")
        print("Remove --dry-run to apply changes.")
    else:
        if merge_result:
            print(f"\nMarkdown: {merge_result.sections_merged} sections merged")
        if sync_result:
            print(f"Database: {sync_result.fields_updated} fields updated")
            if sync_result.proposals_created > 0:
                print(f"\n{sync_result.proposals_created} proposals pending review.")
                print("Use the Streamlit app to review and approve them.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
