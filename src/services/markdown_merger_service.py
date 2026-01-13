"""Markdown merger service using local LLM for intelligent document merging."""

import re
import shutil
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional

from langchain_ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser

from src.models.merge_models import (
    MergeConfig,
    MergeResult,
    MergeReport,
    MergeOperation,
    MergeType,
    SectionDiff,
    CompanyDiff,
    DiffType,
)
from src.llm.merge_prompts import (
    SECTION_MERGE_PROMPT,
    COMPANY_MERGE_PROMPT,
    NEW_COMPANY_PROMPT,
)
from src.llm.chain_factory import get_llm


class MarkdownMergerService:
    """Service for merging markdown research documents using LLM."""

    # Pattern to extract ## sections
    SECTION_PATTERN = re.compile(r"^##\s+(.+)$", re.MULTILINE)

    # Pattern to extract #### company entries
    COMPANY_PATTERN = re.compile(r"^####\s+(.+?)\s*\((.+?)\)\s*$", re.MULTILINE)

    def __init__(
        self,
        llm: Optional[ChatOllama] = None,
        config: Optional[MergeConfig] = None,
        research_dir: str = "research",
    ):
        self.llm = llm
        self.config = config or MergeConfig()
        self.research_dir = Path(research_dir)
        self.report = MergeReport()

    def _get_llm(self) -> ChatOllama:
        """Get or create LLM instance."""
        if self.llm is None:
            self.llm = get_llm()
        return self.llm

    def merge_files(
        self,
        base_file: str = "Fusion_Research.md",
        update_file: str = "Fusion_Research_UPDATE.md",
        output_file: Optional[str] = None,
    ) -> MergeResult:
        """
        Merge update file into base file.

        Args:
            base_file: Name of the base markdown file
            update_file: Name of the update markdown file
            output_file: Name of the output file (default: overwrite base)

        Returns:
            MergeResult with operation details
        """
        result = MergeResult()
        base_path = self.research_dir / base_file
        update_path = self.research_dir / update_file
        output_path = self.research_dir / (output_file or base_file)

        result.original_path = base_path

        # Validate files exist
        if not base_path.exists():
            result.add_error(f"Base file not found: {base_path}")
            return result

        if not update_path.exists():
            result.add_error(f"Update file not found: {update_path}")
            return result

        try:
            # Create backup
            result.backup_path = self.create_backup(base_path)

            # Read files
            base_content = base_path.read_text(encoding="utf-8")
            update_content = update_path.read_text(encoding="utf-8")

            # Extract sections from both files
            base_sections = self.extract_sections(base_content)
            update_sections = self.extract_sections(update_content)

            # Compare and identify differences
            diffs = self.compare_sections(base_sections, update_sections)

            # Merge sections
            merged_sections = {}
            for diff in diffs:
                if diff.diff_type == DiffType.UNCHANGED:
                    merged_sections[diff.section_name] = diff.original_content
                elif diff.diff_type == DiffType.NEW:
                    # New section from update
                    merged_sections[diff.section_name] = diff.update_content
                    result.sections_merged += 1
                elif diff.diff_type == DiffType.MODIFIED:
                    # Merge modified section
                    merged = self.merge_section(
                        diff.original_content,
                        diff.update_content,
                        diff.section_name,
                    )
                    merged_sections[diff.section_name] = merged
                    result.sections_merged += 1

                    # Count company changes
                    company_stats = self._count_company_changes(
                        diff.original_content, diff.update_content
                    )
                    result.companies_added += company_stats["added"]
                    result.companies_updated += company_stats["updated"]

            # Reassemble document
            merged_content = self._reassemble_document(
                base_content, merged_sections, base_sections
            )

            # Validate structure
            validation_errors = self.validate_structure(merged_content)
            if validation_errors:
                for error in validation_errors:
                    result.add_error(f"Structure validation: {error}")

            # Write output
            output_path.write_text(merged_content, encoding="utf-8")
            result.merged_path = output_path
            result.success = True

        except Exception as e:
            result.add_error(f"Merge failed: {str(e)}")
            # Restore from backup if available
            if result.backup_path and result.backup_path.exists():
                try:
                    shutil.copy2(result.backup_path, base_path)
                except Exception:
                    pass

        return result

    def extract_sections(self, content: str) -> dict[str, str]:
        """
        Extract ## sections from markdown content.

        Returns:
            Dictionary mapping section names to their content
        """
        sections = {}
        lines = content.split("\n")
        current_section = None
        current_content = []
        header_line = None

        for line in lines:
            if line.startswith("## "):
                # Save previous section
                if current_section:
                    sections[current_section] = (header_line, "\n".join(current_content))

                current_section = line[3:].strip()
                header_line = line
                current_content = []
            elif current_section:
                current_content.append(line)

        # Save last section
        if current_section:
            sections[current_section] = (header_line, "\n".join(current_content))

        # Flatten to just content for comparison
        return {name: content for name, (header, content) in sections.items()}

    def extract_sections_with_headers(self, content: str) -> dict[str, tuple[str, str]]:
        """Extract sections with their original header lines."""
        sections = {}
        lines = content.split("\n")
        current_section = None
        current_content = []
        header_line = None

        for line in lines:
            if line.startswith("## "):
                if current_section:
                    sections[current_section] = (header_line, "\n".join(current_content))
                current_section = line[3:].strip()
                header_line = line
                current_content = []
            elif current_section:
                current_content.append(line)

        if current_section:
            sections[current_section] = (header_line, "\n".join(current_content))

        return sections

    def extract_company_blocks(self, section_content: str) -> dict[str, CompanyDiff]:
        """
        Extract #### company entries from a section.

        Returns:
            Dictionary mapping company names to their content
        """
        companies = {}

        for match in self.COMPANY_PATTERN.finditer(section_content):
            company_name = match.group(1).strip()
            location = match.group(2).strip()

            # Get content after header until next #### or end
            start_pos = match.end()
            next_header = re.search(r"\n(?:####|###)\s+", section_content[start_pos:])
            if next_header:
                end_pos = start_pos + next_header.start()
            else:
                end_pos = len(section_content)

            company_content = section_content[match.start():end_pos]
            companies[company_name] = CompanyDiff(
                company_name=company_name,
                location=location,
                original_content=company_content,
            )

        return companies

    def compare_sections(
        self,
        base_sections: dict[str, str],
        update_sections: dict[str, str],
    ) -> list[SectionDiff]:
        """Compare sections and identify differences."""
        diffs = []
        all_section_names = set(base_sections.keys()) | set(update_sections.keys())

        for section_name in all_section_names:
            base_content = base_sections.get(section_name)
            update_content = update_sections.get(section_name)

            if base_content is None:
                # New section in update
                diffs.append(SectionDiff(
                    section_name=section_name,
                    update_content=update_content,
                    diff_type=DiffType.NEW,
                ))
            elif update_content is None:
                # Section only in base (keep as-is)
                diffs.append(SectionDiff(
                    section_name=section_name,
                    original_content=base_content,
                    diff_type=DiffType.UNCHANGED,
                ))
            elif self._content_hash(base_content) == self._content_hash(update_content):
                # No change
                diffs.append(SectionDiff(
                    section_name=section_name,
                    original_content=base_content,
                    diff_type=DiffType.UNCHANGED,
                ))
            else:
                # Modified
                diffs.append(SectionDiff(
                    section_name=section_name,
                    original_content=base_content,
                    update_content=update_content,
                    diff_type=DiffType.MODIFIED,
                ))

        return diffs

    def merge_section(
        self,
        base_section: str,
        update_section: str,
        section_name: str,
    ) -> str:
        """
        Use LLM to intelligently merge a single section.

        For large sections, processes company-by-company.
        """
        # Check if section is small enough to merge directly
        total_size = len(base_section) + len(update_section)

        if total_size < self.config.chunk_size:
            return self._llm_merge_section(base_section, update_section, section_name)

        # For large sections, merge company-by-company
        base_companies = self.extract_company_blocks(base_section)
        update_companies = self.extract_company_blocks(update_section)

        if not base_companies and not update_companies:
            # No company structure, use direct merge with chunking
            return self._llm_merge_section(base_section, update_section, section_name)

        # Merge companies
        merged_content = base_section  # Start with base

        for company_name, update_company in update_companies.items():
            if company_name in base_companies:
                # Update existing company
                base_company = base_companies[company_name]
                merged_company = self._llm_merge_company(
                    base_company.original_content,
                    update_company.original_content,
                    company_name,
                )
                # Replace in merged content
                merged_content = merged_content.replace(
                    base_company.original_content, merged_company
                )
            else:
                # New company - append at end of section
                merged_content = self._add_new_company(
                    merged_content, update_company.original_content
                )

        return merged_content

    def _llm_merge_section(
        self,
        base_section: str,
        update_section: str,
        section_name: str,
    ) -> str:
        """Use LLM to merge two section versions."""
        try:
            llm = self._get_llm()
            chain = SECTION_MERGE_PROMPT | llm | StrOutputParser()

            result = chain.invoke({
                "section_name": section_name,
                "original_content": base_section,
                "update_content": update_section,
            })

            return result.strip()

        except Exception as e:
            print(f"LLM merge failed for section {section_name}: {e}")
            # Fallback: return update content (prefer newer)
            return update_section

    def _llm_merge_company(
        self,
        base_company: str,
        update_company: str,
        company_name: str,
    ) -> str:
        """Use LLM to merge two company profile versions."""
        try:
            llm = self._get_llm()
            chain = COMPANY_MERGE_PROMPT | llm | StrOutputParser()

            result = chain.invoke({
                "company_name": company_name,
                "original_company": base_company,
                "update_company": update_company,
            })

            return result.strip()

        except Exception as e:
            print(f"LLM merge failed for company {company_name}: {e}")
            # Fallback: return update content (prefer newer)
            return update_company

    def _add_new_company(self, section_content: str, new_company: str) -> str:
        """Add a new company entry to a section."""
        # Find a good insertion point (before next ## or at end)
        next_section = re.search(r"\n##\s+", section_content)
        if next_section:
            insert_pos = next_section.start()
            return (
                section_content[:insert_pos] +
                "\n\n" + new_company.strip() + "\n" +
                section_content[insert_pos:]
            )
        else:
            return section_content.rstrip() + "\n\n" + new_company.strip() + "\n"

    def _reassemble_document(
        self,
        original_content: str,
        merged_sections: dict[str, str],
        original_sections: dict[str, str],
    ) -> str:
        """Reassemble document from merged sections, preserving order."""
        # Get content before first section (title, intro)
        first_section_match = re.search(r"^##\s+", original_content, re.MULTILINE)
        if first_section_match:
            preamble = original_content[:first_section_match.start()]
        else:
            preamble = ""

        # Build document maintaining original section order
        sections_with_headers = self.extract_sections_with_headers(original_content)

        parts = [preamble.rstrip()]

        for section_name in sections_with_headers:
            if section_name in merged_sections:
                header, _ = sections_with_headers[section_name]
                parts.append(f"\n\n{header}")
                parts.append(merged_sections[section_name])

        # Add any new sections not in original
        for section_name, content in merged_sections.items():
            if section_name not in sections_with_headers:
                parts.append(f"\n\n## {section_name}")
                parts.append(content)

        return "\n".join(parts)

    def _count_company_changes(
        self,
        base_content: str,
        update_content: str,
    ) -> dict[str, int]:
        """Count added and updated companies between two section versions."""
        base_companies = set(self.extract_company_blocks(base_content).keys())
        update_companies = set(self.extract_company_blocks(update_content).keys())

        added = len(update_companies - base_companies)
        updated = len(update_companies & base_companies)

        return {"added": added, "updated": updated}

    def _content_hash(self, content: str) -> str:
        """Generate hash for content comparison."""
        # Normalize whitespace for comparison
        normalized = " ".join(content.split())
        return hashlib.md5(normalized.encode()).hexdigest()

    def create_backup(self, file_path: Path) -> Path:
        """Create timestamped backup of file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.stem}_{timestamp}{self.config.backup_suffix}{file_path.suffix}"
        backup_path = file_path.parent / backup_name

        shutil.copy2(file_path, backup_path)
        return backup_path

    def restore_from_backup(self, backup_path: Path, original_path: Path) -> bool:
        """Restore file from backup."""
        if not backup_path.exists():
            return False
        shutil.copy2(backup_path, original_path)
        return True

    def validate_structure(self, content: str) -> list[str]:
        """Validate merged document structure."""
        errors = []

        # Check for ## sections
        sections = self.SECTION_PATTERN.findall(content)
        if not sections:
            errors.append("No ## sections found")

        # Check for duplicate section headers
        seen_sections = set()
        for section in sections:
            if section in seen_sections:
                errors.append(f"Duplicate section: {section}")
            seen_sections.add(section)

        # Check for unclosed markdown elements (basic check)
        code_blocks = content.count("```")
        if code_blocks % 2 != 0:
            errors.append("Unclosed code block (``` count is odd)")

        return errors


def get_markdown_merger(
    llm: Optional[ChatOllama] = None,
    config: Optional[MergeConfig] = None,
    research_dir: str = "research",
) -> MarkdownMergerService:
    """Factory function to get a markdown merger instance."""
    return MarkdownMergerService(
        llm=llm,
        config=config,
        research_dir=research_dir,
    )
