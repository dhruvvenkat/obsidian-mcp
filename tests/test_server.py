from __future__ import annotations

import asyncio
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import server


class ServerResourcesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.vault_path = self.root / "vault"
        self.notes_folder = self.vault_path / "Compiler Engineering"
        self.project_path = self.root / "project"
        self.notes_folder.mkdir(parents=True)
        self.project_path.mkdir(parents=True)

        alpha = self.notes_folder / "alpha.md"
        alpha.write_text(
            "---\n"
            "tags:\n"
            "  - compiler\n"
            "---\n\n"
            "LLVM and MLIR lower into a smaller IR.\n"
            "Lowering decisions affect scheduler behavior.\n",
            encoding="utf-8",
        )

        beta = self.notes_folder / "beta.md"
        beta.write_text(
            "MLIR enables dataflow experiments.\n"
            "Register allocation is still fuzzy.\n",
            encoding="utf-8",
        )

        gamma = self.notes_folder / "gamma.md"
        gamma.write_text(
            "Dataflow shows up again here.\n"
            "Register allocation is mentioned once more.\n",
            encoding="utf-8",
        )

        project_file = self.project_path / "main.py"
        project_file.write_text(
            "def build_pipeline():\n"
            "    # mlir lowering pass\n"
            "    return 'scheduler'\n",
            encoding="utf-8",
        )

        alpha_time = 1_700_000_000
        beta_time = 1_700_000_100
        gamma_time = 1_700_000_050
        os.utime(alpha, (alpha_time, alpha_time))
        os.utime(beta, (beta_time, beta_time))
        os.utime(gamma, (gamma_time, gamma_time))

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_tool_outputs_reuse_shared_analysis(self) -> None:
        concepts = server.extract_concepts(str(self.vault_path), "Compiler Engineering")
        gaps = server.get_learning_gaps(str(self.vault_path), "Compiler Engineering")
        alignment = server.compare_notes_to_project(
            str(self.vault_path),
            "Compiler Engineering",
            str(self.project_path),
        )

        self.assertIn("- mlir: 2 mention(s)", concepts)
        self.assertIn("- dataflow: 2 mention(s)", concepts)
        self.assertIn("dataflow: appears in 2 note(s), but only 2 total mention(s)", gaps)
        self.assertIn("register allocation: appears in 2 note(s), but only 2 total mention(s)", gaps)
        self.assertIn("- mlir", alignment)
        self.assertIn("- lowering", alignment)
        self.assertIn("- register allocation", alignment)

    def test_resource_registry_and_content(self) -> None:
        expected_uris = {
            "vault://compiler/concepts",
            "vault://compiler/gaps",
            "vault://compiler/recent-notes",
            "vault://project/alignment",
            "vault://weekly-review/latest",
        }
        resources = server.mcp._resource_manager.list_resources()
        resource_uris = {str(resource.uri) for resource in resources}
        self.assertTrue(expected_uris.issubset(resource_uris))

        with (
            patch.object(server, "DEFAULT_VAULT", self.vault_path),
            patch.object(server, "DEFAULT_NOTES_FOLDER", "Compiler Engineering"),
            patch.object(server, "DEFAULT_PROJECT_PATH", self.project_path),
        ):
            concepts = asyncio.run(self._read_resource("vault://compiler/concepts"))
            recent_notes = asyncio.run(self._read_resource("vault://compiler/recent-notes"))
            weekly = asyncio.run(self._read_resource("vault://weekly-review/latest"))

        self.assertIn("# Compiler Concepts", concepts)
        self.assertIn("Recurring concepts:", concepts)
        self.assertIn("`Compiler Engineering/beta.md`", recent_notes)
        self.assertLess(
            recent_notes.index("`Compiler Engineering/beta.md`"),
            recent_notes.index("`Compiler Engineering/gamma.md`"),
        )
        self.assertIn("## Recent Notes", weekly)
        self.assertIn("## Project Alignment", weekly)

    async def _read_resource(self, uri: str) -> str:
        resource = await server.mcp._resource_manager.get_resource(uri)
        self.assertIsNotNone(resource)
        return await resource.read()


if __name__ == "__main__":
    unittest.main()
