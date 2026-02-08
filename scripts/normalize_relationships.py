#!/usr/bin/env python3
"""Migrate text-based relationship fields into normalized tables.

Parses companies.key_investors and companies.key_partnerships text fields
and populates: investors, funding_investors, partnerships, collaborations.

Idempotent -- safe to re-run. Uses INSERT OR IGNORE for investors and
checks for existing partnerships/collaborations before inserting.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.database import get_database
from src.data.parsers.relationship_parser import classify_partner, parse_text_list


def normalize_relationships(db_path: str = "research/fusion_research.db") -> dict:
    """Parse text fields and populate normalized relationship tables.

    Returns summary stats dict.
    """
    db = get_database(db_path)
    stats = {
        "companies_processed": 0,
        "investors_created": 0,
        "funding_links_created": 0,
        "partnerships_created": 0,
        "collaborations_created": 0,
        "skipped_existing": 0,
    }

    # Load all companies with their text fields
    cursor = db.execute(
        "SELECT id, name, key_investors, key_partnerships FROM companies"
    )
    companies = cursor.fetchall()

    for company in companies:
        company_id = company["id"]
        company_name = company["name"]
        stats["companies_processed"] += 1

        # --- Process investors ---
        investor_names = parse_text_list(company["key_investors"])
        for inv_name in investor_names:
            # Get or create investor
            inv_cursor = db.execute(
                "SELECT id FROM investors WHERE name = ?", (inv_name,)
            )
            inv_row = inv_cursor.fetchone()
            if inv_row:
                investor_id = inv_row["id"]
            else:
                ins_cursor = db.execute(
                    "INSERT INTO investors (name, investor_type) VALUES (?, ?)",
                    (inv_name, "Unknown"),
                )
                investor_id = ins_cursor.lastrowid
                stats["investors_created"] += 1

            # Find or create a synthetic funding round to link through
            fr_cursor = db.execute(
                "SELECT id FROM funding_rounds WHERE company_id = ? LIMIT 1",
                (company_id,),
            )
            fr_row = fr_cursor.fetchone()
            if fr_row:
                funding_id = fr_row["id"]
            else:
                # Create a synthetic funding round
                fr_ins = db.execute(
                    """INSERT INTO funding_rounds
                       (company_id, stage, notes)
                       VALUES (?, ?, ?)""",
                    (company_id, "Unknown", f"Synthetic round for {company_name} investor linkage"),
                )
                funding_id = fr_ins.lastrowid

            # Link investor to funding round (idempotent)
            existing_link = db.execute(
                "SELECT 1 FROM funding_investors WHERE funding_id = ? AND investor_id = ?",
                (funding_id, investor_id),
            ).fetchone()
            if not existing_link:
                db.execute(
                    "INSERT INTO funding_investors (funding_id, investor_id, is_lead) VALUES (?, ?, 0)",
                    (funding_id, investor_id),
                )
                stats["funding_links_created"] += 1
            else:
                stats["skipped_existing"] += 1

        # --- Process partnerships ---
        partner_names = parse_text_list(company["key_partnerships"])
        for partner_name in partner_names:
            partner_type = classify_partner(partner_name)

            if partner_type == "research_partner":
                # Insert as collaboration
                existing = db.execute(
                    """SELECT 1 FROM collaborations
                       WHERE company_id = ? AND institution_name = ?""",
                    (company_id, partner_name),
                ).fetchone()
                if not existing:
                    db.execute(
                        """INSERT INTO collaborations
                           (company_id, institution_name, institution_type,
                            collaboration_type)
                           VALUES (?, ?, ?, ?)""",
                        (company_id, partner_name, "Research Institute", "Research"),
                    )
                    stats["collaborations_created"] += 1
                else:
                    stats["skipped_existing"] += 1
            else:
                # Insert as partnership (industrial or government)
                ptype = "Government" if partner_type == "government" else "Strategic"
                existing = db.execute(
                    """SELECT 1 FROM partnerships
                       WHERE company_id_a = ? AND partner_name = ?""",
                    (company_id, partner_name),
                ).fetchone()
                if not existing:
                    db.execute(
                        """INSERT INTO partnerships
                           (company_id_a, partner_name, partner_type, status)
                           VALUES (?, ?, ?, ?)""",
                        (company_id, partner_name, ptype, "Active"),
                    )
                    stats["partnerships_created"] += 1
                else:
                    stats["skipped_existing"] += 1

    db.commit()
    return stats


def main():
    print("Normalizing relationship data from text fields...")
    stats = normalize_relationships()
    print(f"\nDone! Summary:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
