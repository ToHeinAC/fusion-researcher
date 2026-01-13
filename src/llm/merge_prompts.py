"""LLM prompts for markdown merging and database sync operations.

All prompts are in German to match the source document language.
"""

from langchain_core.prompts import ChatPromptTemplate

# =============================================================================
# Section Merge Prompts
# =============================================================================

SECTION_MERGE_SYSTEM = """Du bist ein Experte für Fusionsenergie-Dokumentation.
Deine Aufgabe ist es, zwei Versionen eines Dokumentabschnitts intelligent zusammenzuführen.

REGELN:
1. Behalte die ursprüngliche Markdown-Struktur (## und #### Header) exakt bei
2. Behalte die deutsche Sprache bei
3. Wenn UPDATE neue Informationen enthält, integriere sie sinnvoll
4. Wenn UPDATE aktuellere Zahlen enthält (Finanzierung, Team-Größe, TRL), verwende diese
5. Behalte alle Quellenverweise [n] bei und nummeriere sie korrekt
6. Entferne keine bestehenden Informationen, es sei denn UPDATE widerspricht explizit
7. Bei Widersprüchen bevorzuge die neueren/spezifischeren Daten aus UPDATE
8. Formatierung: Behalte Fettdruck (**text**), Aufzählungen (-) und Tabellen (|) bei"""

SECTION_MERGE_HUMAN = """Führe diese beiden Versionen des Abschnitts "{section_name}" zusammen.

=== ORIGINAL ===
{original_content}

=== UPDATE ===
{update_content}

=== ZUSAMMENGEFÜHRTER ABSCHNITT ==="""

SECTION_MERGE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SECTION_MERGE_SYSTEM),
    ("human", SECTION_MERGE_HUMAN),
])

# =============================================================================
# Company Entry Merge Prompts
# =============================================================================

COMPANY_MERGE_SYSTEM = """Du bist ein Experte für Fusionsenergie-Unternehmensdaten.
Deine Aufgabe ist es, zwei Unternehmensprofile intelligent zusammenzuführen.

REGELN:
1. Behalte alle Standard-Felder bei:
   - **Profil:** (Unternehmensbeschreibung)
   - **Technologie:** (Technologischer Ansatz)
   - **Finanzierung:** (Finanzierungsrunden und Gesamtbetrag)
   - **Investoren:** (Liste der Investoren)
   - **Standorte:** (Geografische Standorte)
   - **Team:** (Teamgröße und Zusammensetzung)
   - **Meilensteine:** (Wichtige Meilensteine und Zeitpläne)
   - **USP/Besonderheit:** (Alleinstellungsmerkmale)
   - **Partnerschaften/Netzwerk:** (Strategische Partnerschaften)

2. Verwende neuere Zahlen aus UPDATE für:
   - Finanzierung (EUR/USD Beträge)
   - Team-Größe (Mitarbeiterzahlen)
   - TRL-Level (Technology Readiness Level)

3. Füge neue Partnerschaften oder Meilensteine aus UPDATE hinzu
4. Behalte bestehende Informationen, wenn UPDATE sie nicht explizit korrigiert
5. Behalte alle Quellenverweise [n] bei
6. Behalte die #### Header-Struktur: #### Unternehmensname (Standort)"""

COMPANY_MERGE_HUMAN = """Führe diese beiden Profile für "{company_name}" zusammen.

=== ORIGINAL ===
{original_company}

=== UPDATE ===
{update_company}

=== ZUSAMMENGEFÜHRTES PROFIL ==="""

COMPANY_MERGE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", COMPANY_MERGE_SYSTEM),
    ("human", COMPANY_MERGE_HUMAN),
])

# =============================================================================
# New Company Integration Prompt
# =============================================================================

NEW_COMPANY_SYSTEM = """Du bist ein Experte für Fusionsenergie-Dokumentation.
Ein neues Unternehmen soll in einen bestehenden Abschnitt integriert werden.

REGELN:
1. Füge das neue Unternehmen an der passenden Stelle ein (alphabetisch oder nach Relevanz)
2. Behalte die bestehende Struktur des Abschnitts bei
3. Stelle sicher, dass das neue Profil dem Standard-Format entspricht:
   #### Unternehmensname (Standort)
   **Profil:** ...
   - **Technologie:** ...
   - **Finanzierung:** ...
   etc."""

NEW_COMPANY_HUMAN = """Integriere dieses neue Unternehmen in den bestehenden Abschnitt.

=== BESTEHENDER ABSCHNITT ===
{existing_section}

=== NEUES UNTERNEHMEN ===
{new_company}

=== AKTUALISIERTER ABSCHNITT ==="""

NEW_COMPANY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", NEW_COMPANY_SYSTEM),
    ("human", NEW_COMPANY_HUMAN),
])

# =============================================================================
# Conflict Resolution Prompts
# =============================================================================

CONFLICT_RESOLUTION_SYSTEM = """Du bist ein Datenvalidierungs-Experte für Fusionsenergie-Unternehmen.
Zwei Quellen haben widersprüchliche Informationen. Analysiere welcher Wert korrekt ist.

KRITERIEN:
1. Aktualität: Neuere Daten bevorzugen
2. Spezifität: Konkrete Zahlen > vage Angaben
3. Plausibilität: Konsistenz mit bekannten Fakten
4. Quellenqualität: Offizielle Quellen > Schätzungen

Antworte NUR mit einem JSON-Objekt, keine zusätzlichen Erklärungen."""

CONFLICT_RESOLUTION_HUMAN = """Widersprüchliche Information gefunden:

Unternehmen: {company_name}
Feld: {field_name}
Original-Wert: {original_value}
Update-Wert: {update_value}

Antworte mit JSON:
{{"selected_value": "...", "confidence": 0.0-1.0, "reasoning": "kurze Begründung"}}"""

CONFLICT_RESOLUTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", CONFLICT_RESOLUTION_SYSTEM),
    ("human", CONFLICT_RESOLUTION_HUMAN),
])

# =============================================================================
# Database Sync Validation Prompts
# =============================================================================

VALIDATE_CHANGE_SYSTEM = """Du bist ein Datenvalidierungs-Experte für Fusionsenergie-Unternehmen.
Validiere ob eine vorgeschlagene Datenänderung plausibel und korrekt ist.

PRÜFKRITERIEN:
1. Plausibilität: Ist der neue Wert realistisch für dieses Unternehmen?
2. Konsistenz: Passt er zu bekannten Fakten über Fusionsenergie-Startups?
3. Format: Ist das Datenformat korrekt (Zahlen, Währungen, Daten)?
4. Fehlerprüfung: Könnte es sich um einen Tippfehler handeln?

Antworte NUR mit einem JSON-Objekt."""

VALIDATE_CHANGE_HUMAN = """Validiere diese Datenänderung:

Unternehmen: {company_name}
Feld: {field_name}
Aktueller Wert: {old_value}
Neuer Wert: {new_value}
Quelle: Markdown-Dokument-Update

Antworte mit JSON:
{{"valid": true/false, "confidence": 0.0-1.0, "notes": "kurze Anmerkung"}}"""

VALIDATE_CHANGE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", VALIDATE_CHANGE_SYSTEM),
    ("human", VALIDATE_CHANGE_HUMAN),
])

# =============================================================================
# Fuzzy Company Name Matching
# =============================================================================

FUZZY_MATCH_SYSTEM = """Du bist ein Experte für Unternehmensdaten.
Bestimme ob zwei Unternehmensnamen sich auf dasselbe Unternehmen beziehen.

BERÜCKSICHTIGE:
- Abkürzungen: CFS = Commonwealth Fusion Systems
- Varianten: TAE Tech = TAE Technologies
- Schreibfehler und Tippfehler
- Zusätze: "GmbH", "Inc.", "Ltd." ignorieren
- Standort-Varianten: München = Munich

Antworte NUR mit einem JSON-Objekt."""

FUZZY_MATCH_HUMAN = """Sind diese beiden Namen dasselbe Unternehmen?

Name 1: {name1}
Name 2: {name2}

Antworte mit JSON:
{{"same_company": true/false, "confidence": 0.0-1.0, "reasoning": "kurze Begründung"}}"""

FUZZY_MATCH_PROMPT = ChatPromptTemplate.from_messages([
    ("system", FUZZY_MATCH_SYSTEM),
    ("human", FUZZY_MATCH_HUMAN),
])

# =============================================================================
# Structure Validation Prompt
# =============================================================================

STRUCTURE_VALIDATION_SYSTEM = """Du bist ein Markdown-Strukturvalidierungs-Experte.
Prüfe ob ein zusammengeführtes Dokument die korrekte Struktur hat.

PRÜFPUNKTE:
1. Alle ## Hauptabschnitte vorhanden
2. Alle #### Unternehmensprofile korrekt formatiert
3. Keine doppelten Header
4. Keine fehlenden Schließungen
5. Tabellen korrekt formatiert (|)
6. Listen korrekt formatiert (-)

Antworte mit einer Liste von Problemen oder "OK" wenn alles korrekt ist."""

STRUCTURE_VALIDATION_HUMAN = """Validiere die Struktur dieses Dokuments:

{document_content}

Liste alle strukturellen Probleme auf oder antworte mit "OK":"""

STRUCTURE_VALIDATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", STRUCTURE_VALIDATION_SYSTEM),
    ("human", STRUCTURE_VALIDATION_HUMAN),
])
