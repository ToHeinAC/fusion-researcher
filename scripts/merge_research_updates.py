#!/usr/bin/env python3
"""CLI script for merging Fusion_Research_UPDATE.md into Fusion_Research.md."""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.markdown_merger_service import MarkdownMergerService, MergeConfig
from src.llm.chain_factory import get_llm


def main():
    parser = argparse.ArgumentParser(
        description="Merge Fusion Research update file into base file using LLM"
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
        "--output-file",
        default=None,
        help="Name of output file (default: overwrite base file)",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating backup of base file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing files",
    )
    parser.add_argument(
        "--model",
        default="qwen3:8b",
        help="Ollama model to use (default: qwen3:8b)",
    )
    parser.add_argument(
        "--research-dir",
        default="research",
        help="Directory containing research files (default: research)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Fusion Research Markdown Merger")
    print("=" * 60)

    # Check files exist
    base_path = Path(args.research_dir) / args.base_file
    update_path = Path(args.research_dir) / args.update_file

    if not base_path.exists():
        print(f"Error: Base file not found: {base_path}")
        return 1

    if not update_path.exists():
        print(f"Error: Update file not found: {update_path}")
        return 1

    print(f"\nBase file:   {base_path}")
    print(f"Update file: {update_path}")
    print(f"Model:       {args.model}")

    if args.dry_run:
        print("\n[DRY RUN - No changes will be written]")

    # Initialize LLM
    print("\nInitializing LLM...")
    try:
        llm = get_llm(model=args.model)
    except Exception as e:
        print(f"Error initializing LLM: {e}")
        print("Make sure Ollama is running: ollama serve")
        return 1

    # Configure merger
    config = MergeConfig(
        backup_suffix="" if args.no_backup else ".backup",
    )

    merger = MarkdownMergerService(
        llm=llm,
        config=config,
        research_dir=args.research_dir,
    )

    # Preview mode for dry run
    if args.dry_run:
        print("\nAnalyzing files...")

        base_content = base_path.read_text(encoding="utf-8")
        update_content = update_path.read_text(encoding="utf-8")

        base_sections = merger.extract_sections(base_content)
        update_sections = merger.extract_sections(update_content)

        diffs = merger.compare_sections(base_sections, update_sections)

        print("\nSection Analysis:")
        print("-" * 40)
        for diff in diffs:
            status = diff.diff_type.value.upper()
            print(f"  [{status:10}] {diff.section_name[:40]}")

        new_sections = sum(1 for d in diffs if d.diff_type.value == "new")
        modified_sections = sum(1 for d in diffs if d.diff_type.value == "modified")
        unchanged_sections = sum(1 for d in diffs if d.diff_type.value == "unchanged")

        print(f"\nSummary:")
        print(f"  New sections:       {new_sections}")
        print(f"  Modified sections:  {modified_sections}")
        print(f"  Unchanged sections: {unchanged_sections}")

        return 0

    # Perform merge
    print("\nMerging files...")
    result = merger.merge_files(
        base_file=args.base_file,
        update_file=args.update_file,
        output_file=args.output_file,
    )

    # Report results
    print("\n" + "=" * 60)
    print("Merge Results")
    print("=" * 60)
    print(f"  Success:            {result.success}")
    print(f"  Sections merged:    {result.sections_merged}")
    print(f"  Companies added:    {result.companies_added}")
    print(f"  Companies updated:  {result.companies_updated}")
    print(f"  Conflicts resolved: {result.conflicts_resolved}")

    if result.backup_path:
        print(f"  Backup created:     {result.backup_path}")

    if result.merged_path:
        print(f"  Output file:        {result.merged_path}")

    if result.errors:
        print("\nErrors:")
        for error in result.errors:
            print(f"  - {error}")
        return 1

    print("\nMerge completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
