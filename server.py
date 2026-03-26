from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import logging
import re
import sys

from mcp.server.fastmcp import FastMCP

logging.basicConfig(stream=sys.stderr, level=logging.INFO)

mcp = FastMCP("compiler-study")

DEFAULT_VAULT = Path("/home/dhruv/Documents/compiler engineering")
DEFAULT_NOTES_FOLDER: str | None = None
DEFAULT_PROJECT_PATH = Path("/home/dhruv/Documents/Programming/accelerator-sim")

TOP_CONCEPT_LIMIT = 12
GAP_LIMIT = 8
RECENT_NOTES_LIMIT = 5
PROJECT_TEXT_SUFFIXES = {".cpp", ".cc", ".c", ".h", ".hpp", ".py", ".md", ".txt"}
NOTE_PREVIEW_CHARS = 180

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


@dataclass
class NoteDocument:
    path: Path
    relative_path: Path
    content: str
    modified_at: float


@dataclass
class VaultSnapshot:
    vault_path: Path
    folder: str | None
    notes_root: Path
    notes: list[NoteDocument]
    topic_total_hits: Counter[str]
    topic_file_hits: Counter[str]


def get_notes_root(vault_path: Path, folder: str | None = None) -> Path:
    root = vault_path
    if folder:
        root = root / folder

    if not root.exists():
        raise FileNotFoundError(f"Path does not exist: {root}")

    return root


def read_markdown_files(vault_path: Path, folder: str | None = None) -> list[NoteDocument]:
    root = get_notes_root(vault_path, folder)
    files: list[NoteDocument] = []

    for path in sorted(root.rglob("*.md")):
        try:
            stat = path.stat()
            files.append(
                NoteDocument(
                    path=path,
                    relative_path=path.relative_to(vault_path),
                    content=path.read_text(encoding="utf-8"),
                    modified_at=stat.st_mtime,
                )
            )
        except Exception as exc:
            logging.warning("Failed reading %s: %s", path, exc)

    return files


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())


def strip_frontmatter(text: str) -> str:
    return re.sub(r"\A---\s*\n.*?\n---\s*\n?", "", text, count=1, flags=re.DOTALL)


def preview_text(text: str, limit: int = NOTE_PREVIEW_CHARS) -> str:
    normalized = normalize_text(strip_frontmatter(text)).strip()
    if not normalized:
        return "(empty note)"
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def format_timestamp(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def analyze_topics(notes: list[NoteDocument]) -> tuple[Counter[str], Counter[str]]:
    topic_total_hits: Counter[str] = Counter()
    topic_file_hits: Counter[str] = Counter()

    for note in notes:
        text = normalize_text(note.content)
        for topic in KEY_TOPICS:
            hits = text.count(topic)
            topic_total_hits[topic] += hits
            if hits > 0:
                topic_file_hits[topic] += 1

    return topic_total_hits, topic_file_hits


def load_vault_snapshot(vault_path: Path | None = None, folder: str | None = None) -> VaultSnapshot:
    actual_vault = DEFAULT_VAULT if vault_path is None else vault_path
    actual_folder = DEFAULT_NOTES_FOLDER if folder is None else folder
    notes_root = get_notes_root(actual_vault, actual_folder)
    notes = read_markdown_files(actual_vault, actual_folder)
    topic_total_hits, topic_file_hits = analyze_topics(notes)
    return VaultSnapshot(
        vault_path=actual_vault,
        folder=actual_folder,
        notes_root=notes_root,
        notes=notes,
        topic_total_hits=topic_total_hits,
        topic_file_hits=topic_file_hits,
    )


def describe_snapshot_scope(snapshot: VaultSnapshot) -> str:
    if snapshot.folder:
        return f"`{snapshot.folder}`"
    return "the vault root"


def get_top_concepts(snapshot: VaultSnapshot, limit: int = TOP_CONCEPT_LIMIT) -> list[tuple[str, int]]:
    return [
        (topic, count)
        for topic, count in snapshot.topic_total_hits.most_common(limit)
        if count > 0
    ]


def get_gap_candidates(snapshot: VaultSnapshot, limit: int = GAP_LIMIT) -> list[tuple[str, int, int]]:
    candidates = []
    for topic in KEY_TOPICS:
        file_hits = snapshot.topic_file_hits[topic]
        total_hits = snapshot.topic_total_hits[topic]
        if file_hits >= 2 and total_hits <= file_hits * 2:
            candidates.append((topic, file_hits, total_hits))

    return sorted(candidates, key=lambda item: (-item[1], item[2], item[0]))[:limit]


def format_concepts_summary(snapshot: VaultSnapshot) -> str:
    top = get_top_concepts(snapshot)
    if not top:
        return "Recurring concepts:\nNo tracked concepts found."

    lines = [f"- {topic}: {count} mention(s)" for topic, count in top]
    return "Recurring concepts:\n" + "\n".join(lines)


def format_learning_gaps_summary(snapshot: VaultSnapshot) -> str:
    candidates = get_gap_candidates(snapshot)
    if not candidates:
        return "No obvious shallow recurring gaps found from the tracked concept list."

    lines = [
        f"- {topic}: appears in {file_hits} note(s), but only {total_hits} total mention(s)"
        for topic, file_hits, total_hits in candidates
    ]
    return (
        "Potential weak spots (recurring but shallow):\n"
        + "\n".join(lines)
        + "\n\nInterpretation: these topics show up repeatedly, but your notes may not go deep yet."
    )


def get_recent_notes(snapshot: VaultSnapshot, limit: int = RECENT_NOTES_LIMIT) -> list[NoteDocument]:
    return sorted(
        snapshot.notes,
        key=lambda note: (-note.modified_at, note.relative_path.as_posix()),
    )[:limit]


def format_recent_notes_digest(snapshot: VaultSnapshot, limit: int = RECENT_NOTES_LIMIT) -> str:
    recent_notes = get_recent_notes(snapshot, limit=limit)
    if not recent_notes:
        return "Recent notes:\nNo notes found."

    lines = ["Recent notes:"]
    for index, note in enumerate(recent_notes, start=1):
        lines.append(
            f"{index}. `{note.relative_path.as_posix()}` (updated {format_timestamp(note.modified_at)})"
        )
        lines.append(f"   Preview: {preview_text(note.content)}")
    return "\n".join(lines)


def load_project_text(project_path: Path | None = None) -> str:
    actual_project_path = DEFAULT_PROJECT_PATH if project_path is None else project_path
    if not actual_project_path.exists():
        raise FileNotFoundError(f"Configured project path does not exist: {actual_project_path}")

    project_chunks = []
    for path in sorted(actual_project_path.rglob("*")):
        if not path.is_file() or path.suffix not in PROJECT_TEXT_SUFFIXES:
            continue
        try:
            project_chunks.append(path.read_text(encoding="utf-8"))
        except Exception as exc:
            logging.warning("Failed reading %s: %s", path, exc)

    return normalize_text("\n".join(project_chunks))


def build_alignment_lists(
    snapshot: VaultSnapshot,
    project_path: Path | None = None,
) -> tuple[list[str], list[str]]:
    project_text = load_project_text(project_path)

    represented = []
    missing = []
    for topic in KEY_TOPICS:
        if snapshot.topic_total_hits[topic] <= 0:
            continue

        if topic in project_text:
            represented.append(topic)
        else:
            missing.append(topic)

    return represented[:10], missing[:10]


def format_project_alignment_summary(
    snapshot: VaultSnapshot,
    project_path: Path | None = None,
) -> str:
    actual_project_path = DEFAULT_PROJECT_PATH if project_path is None else project_path
    try:
        represented, missing = build_alignment_lists(snapshot, actual_project_path)
    except FileNotFoundError:
        return (
            "Project alignment unavailable.\n"
            f"Configured project path does not exist: `{actual_project_path}`"
        )

    return (
        "Concepts present in notes and likely represented in project:\n- "
        + ("\n- ".join(represented) if represented else "None detected")
        + "\n\nConcepts present in notes but not obviously represented in project:\n- "
        + ("\n- ".join(missing) if missing else "None detected")
    )


def format_weekly_review(snapshot: VaultSnapshot, project_path: Path | None = None) -> str:
    return "\n\n".join(
        [
            "# Weekly Learning Review",
            f"Snapshot: {len(snapshot.notes)} note(s) from {describe_snapshot_scope(snapshot)}.",
            "## Recurring Concepts",
            format_concepts_summary(snapshot),
            "## Likely Gaps",
            format_learning_gaps_summary(snapshot),
            "## Recent Notes",
            format_recent_notes_digest(snapshot),
            "## Project Alignment",
            format_project_alignment_summary(snapshot, project_path),
        ]
    )


def format_resource_document(title: str, body: str, snapshot: VaultSnapshot) -> str:
    return "\n\n".join(
        [
            f"# {title}",
            f"Snapshot: {len(snapshot.notes)} note(s) from {describe_snapshot_scope(snapshot)}.",
            body,
        ]
    )


@mcp.tool()
def extract_concepts(
    vault_path: str = str(DEFAULT_VAULT),
    folder: str | None = DEFAULT_NOTES_FOLDER,
) -> str:
    """Extract recurring compiler concepts from notes in a vault folder.

    Args:
        vault_path: Absolute path to the Obsidian vault.
        folder: Folder inside the vault to scan.
    """
    snapshot = load_vault_snapshot(Path(vault_path), folder)
    return format_concepts_summary(snapshot)


@mcp.tool()
def get_learning_gaps(
    vault_path: str = str(DEFAULT_VAULT),
    folder: str | None = DEFAULT_NOTES_FOLDER,
) -> str:
    """Identify likely weak spots based on repeated but shallow concept coverage.

    Args:
        vault_path: Absolute path to the Obsidian vault.
        folder: Folder inside the vault to scan.
    """
    snapshot = load_vault_snapshot(Path(vault_path), folder)
    return format_learning_gaps_summary(snapshot)


@mcp.tool()
def generate_study_session(
    vault_path: str = str(DEFAULT_VAULT),
    folder: str | None = DEFAULT_NOTES_FOLDER,
    duration_minutes: int = 90,
) -> str:
    """Generate a focused study session using recurring concepts and likely gaps.

    Args:
        vault_path: Absolute path to the Obsidian vault.
        folder: Folder inside the vault to scan.
        duration_minutes: Target study session length.
    """
    snapshot = load_vault_snapshot(Path(vault_path), folder)
    concepts = format_concepts_summary(snapshot)
    gaps = format_learning_gaps_summary(snapshot)

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
    notes_folder: str | None = DEFAULT_NOTES_FOLDER,
    project_path: str = str(DEFAULT_PROJECT_PATH),
) -> str:
    """Compare note concepts against a local project repo by checking keyword coverage.

    Args:
        vault_path: Absolute path to the Obsidian vault.
        notes_folder: Folder inside the vault to scan.
        project_path: Absolute path to the code project to compare against.
    """
    snapshot = load_vault_snapshot(Path(vault_path), notes_folder)
    return format_project_alignment_summary(snapshot, Path(project_path))


@mcp.resource(
    "vault://compiler/concepts",
    name="compiler-concepts",
    title="Compiler Concepts",
    description="Stable view of recurring tracked concepts in the compiler notes.",
    mime_type="text/markdown",
)
def compiler_concepts_resource() -> str:
    snapshot = load_vault_snapshot()
    return format_resource_document("Compiler Concepts", format_concepts_summary(snapshot), snapshot)


@mcp.resource(
    "vault://compiler/gaps",
    name="compiler-gaps",
    title="Compiler Gaps",
    description="Stable view of recurring but shallow compiler topics in the notes.",
    mime_type="text/markdown",
)
def compiler_gaps_resource() -> str:
    snapshot = load_vault_snapshot()
    return format_resource_document("Compiler Gaps", format_learning_gaps_summary(snapshot), snapshot)


@mcp.resource(
    "vault://compiler/recent-notes",
    name="compiler-recent-notes",
    title="Recent Compiler Notes",
    description="Recent note digest for the compiler study folder.",
    mime_type="text/markdown",
)
def compiler_recent_notes_resource() -> str:
    snapshot = load_vault_snapshot()
    return format_resource_document("Recent Compiler Notes", format_recent_notes_digest(snapshot), snapshot)


@mcp.resource(
    "vault://project/alignment",
    name="project-alignment",
    title="Project Alignment",
    description="Stable notes-to-project alignment summary for the default study project.",
    mime_type="text/markdown",
)
def project_alignment_resource() -> str:
    snapshot = load_vault_snapshot()
    return format_resource_document(
        "Project Alignment",
        format_project_alignment_summary(snapshot),
        snapshot,
    )


@mcp.resource(
    "vault://weekly-review/latest",
    name="weekly-review-latest",
    title="Weekly Review",
    description="Latest weekly digest across concepts, gaps, recent notes, and project alignment.",
    mime_type="text/markdown",
)
def weekly_review_resource() -> str:
    snapshot = load_vault_snapshot()
    return format_weekly_review(snapshot)


if __name__ == "__main__":
    mcp.run()
