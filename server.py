from __future__ import annotations

from pathlib import Path
from collections import Counter
import re
import sys
import logging

from mcp.server.fastmcp import FastMCP

logging.basicConfig(stream=sys.stderr, level=logging.INFO)

mcp = FastMCP("compiler-study")

DEFAULT_VAULT = Path("/home/dhruv/Documents/compiler engineering")

KEY_TOPICS = [
    "llvm",
    "mlir",
    "ssa",
    "register allocation",
    "instruction selection",
    "dataflow",
    "lowering",
    "ir",
    "dialect",
    "systolic array",
    "tiling",
    "kernel fusion",
    "autotuning",
    "runtime",
    "scheduler",
    "memory hierarchy",
]

def read_markdown_files(vault_path: Path, folder: str | None = None) -> list[tuple[Path, str]]:
    root = vault_path
    if folder:
        root = root / folder

    if not root.exists():
        raise FileNotFoundError(f"Path does not exist: {root}")

    files: list[tuple[Path, str]] = []
    for path in root.rglob("*.md"):
        try:
            files.append((path, path.read_text(encoding="utf-8")))
        except Exception as e:
            logging.warning("Failed reading %s: %s", path, e)
    return files

def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())

@mcp.tool()
def extract_concepts(
    vault_path: str = str(DEFAULT_VAULT),
    folder: str = "Compiler Engineering"
) -> str:
    """Extract recurring compiler concepts from notes in a vault folder.

    Args:
        vault_path: Absolute path to the Obsidian vault.
        folder: Folder inside the vault to scan.
    """
    files = read_markdown_files(Path(vault_path), folder)
    counts = Counter()

    for _, content in files:
        text = normalize_text(content)
        for topic in KEY_TOPICS:
            counts[topic] += text.count(topic)

    if not counts:
        return "No concepts found."

    top = counts.most_common(12)
    lines = [f"- {topic}: {count} mention(s)" for topic, count in top if count > 0]
    return "Recurring concepts:\n" + ("\n".join(lines) if lines else "No tracked concepts found.")

@mcp.tool()
def get_learning_gaps(
    vault_path: str = str(DEFAULT_VAULT),
    folder: str = "Compiler Engineering"
) -> str:
    """Identify likely weak spots based on repeated but shallow concept coverage.

    Args:
        vault_path: Absolute path to the Obsidian vault.
        folder: Folder inside the vault to scan.
    """
    files = read_markdown_files(Path(vault_path), folder)
    topic_file_hits = Counter()
    topic_total_hits = Counter()

    for _, content in files:
        text = normalize_text(content)
        for topic in KEY_TOPICS:
            hits = text.count(topic)
            if hits > 0:
                topic_file_hits[topic] += 1
                topic_total_hits[topic] += hits

    candidates = []
    for topic in KEY_TOPICS:
        file_hits = topic_file_hits[topic]
        total_hits = topic_total_hits[topic]
        if file_hits >= 2 and total_hits <= file_hits * 2:
            candidates.append((topic, file_hits, total_hits))

    if not candidates:
        return "No obvious shallow recurring gaps found from the tracked concept list."

    lines = [
        f"- {topic}: appears in {file_hits} note(s), but only {total_hits} total mention(s)"
        for topic, file_hits, total_hits in sorted(candidates, key=lambda x: (-x[1], x[2]))
    ]
    return (
        "Potential weak spots (recurring but shallow):\n"
        + "\n".join(lines[:8])
        + "\n\nInterpretation: these topics show up repeatedly, but your notes may not go deep yet."
    )

@mcp.tool()
def generate_study_session(
    vault_path: str = str(DEFAULT_VAULT),
    folder: str = "Compiler Engineering",
    duration_minutes: int = 90
) -> str:
    """Generate a focused study session using recurring concepts and likely gaps.

    Args:
        vault_path: Absolute path to the Obsidian vault.
        folder: Folder inside the vault to scan.
        duration_minutes: Target study session length.
    """
    concepts = extract_concepts(vault_path, folder)
    gaps = get_learning_gaps(vault_path, folder)

    return f"""Study session ({duration_minutes} min)

1. Review block (20 min)
Read your strongest recurring notes from:
{folder}

2. Gap deepening block (35 min)
Use these likely weak spots:
{gaps}

3. Implementation block (25 min)
Code one tiny exercise tied to a weak topic:
- parse a toy IR
- implement a simple dataflow pass
- simulate a scheduler decision
- trace matrix tiling by hand

4. Reflection block (10 min)
Write:
- what became clearer
- what still feels fuzzy
- what to build next

Reference concept summary:
{concepts}
"""

@mcp.tool()
def compare_notes_to_project(
    vault_path: str = str(DEFAULT_VAULT),
    notes_folder: str = "Compiler Engineering",
    project_path: str = "/home/dhruv/Documents/Programming/accelerator-sim"
) -> str:
    """Compare note concepts against a local project repo by checking keyword coverage.

    Args:
        vault_path: Absolute path to the Obsidian vault.
        notes_folder: Folder inside the vault to scan.
        project_path: Absolute path to the code project to compare against.
    """
    files = read_markdown_files(Path(vault_path), notes_folder)
    note_counts = Counter()
    for _, content in files:
        text = normalize_text(content)
        for topic in KEY_TOPICS:
            note_counts[topic] += text.count(topic)

    project_root = Path(project_path)
    project_text = []
    for path in project_root.rglob("*"):
        if path.is_file() and path.suffix in {".cpp", ".cc", ".c", ".h", ".hpp", ".py", ".md", ".txt"}:
            try:
                project_text.append(path.read_text(encoding="utf-8"))
            except Exception:
                pass
    combined_project = normalize_text("\n".join(project_text))

    missing = []
    represented = []
    for topic in KEY_TOPICS:
        if note_counts[topic] > 0:
            if topic in combined_project:
                represented.append(topic)
            else:
                missing.append(topic)

    return (
        "Concepts present in notes and likely represented in project:\n- "
        + ("\n- ".join(represented[:10]) if represented else "None detected")
        + "\n\nConcepts present in notes but not obviously represented in project:\n- "
        + ("\n- ".join(missing[:10]) if missing else "None detected")
    )

if __name__ == "__main__":
    mcp.run()
