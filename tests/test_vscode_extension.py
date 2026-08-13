import json
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).parent.parent
EXTENSION = ROOT / "vscode-extension"


class VsCodeExtensionTests(unittest.TestCase):
    def load_json(self, relative: str):
        return json.loads((EXTENSION / relative).read_text(encoding="utf-8"))

    def test_all_extension_json_is_valid(self):
        files = [
            "package.json",
            "language-configuration.json",
            "syntaxes/algolang.tmLanguage.json",
            "snippets/algolang.json",
        ]
        for filename in files:
            with self.subTest(filename=filename):
                self.assertIsInstance(self.load_json(filename), dict)

    def test_manifest_registers_language_and_commands(self):
        manifest = self.load_json("package.json")
        contributes = manifest["contributes"]
        language = contributes["languages"][0]
        self.assertEqual(language["id"], "algolang")
        self.assertIn(".algo", language["extensions"])
        command_ids = {command["command"] for command in contributes["commands"]}
        self.assertEqual(
            command_ids,
            {"algolang.run", "algolang.check", "algolang.ast", "algolang.dryrun"},
        )
        activation_commands = {
            event.removeprefix("onCommand:")
            for event in manifest["activationEvents"]
            if event.startswith("onCommand:")
        }
        self.assertTrue(command_ids.issubset(activation_commands))

    def test_contributed_files_exist(self):
        manifest = self.load_json("package.json")
        paths = [manifest["main"]]
        paths.extend(language["configuration"] for language in manifest["contributes"]["languages"])
        paths.extend(grammar["path"] for grammar in manifest["contributes"]["grammars"])
        paths.extend(snippet["path"] for snippet in manifest["contributes"]["snippets"])
        for relative in paths:
            with self.subTest(path=relative):
                self.assertTrue((EXTENSION / relative).is_file())

    def test_grammar_targets_algolang_scope(self):
        grammar = self.load_json("syntaxes/algolang.tmLanguage.json")
        manifest = self.load_json("package.json")
        contribution = manifest["contributes"]["grammars"][0]
        self.assertEqual(grammar["scopeName"], "source.algolang")
        self.assertEqual(contribution["scopeName"], grammar["scopeName"])
        self.assertEqual(contribution["language"], "algolang")

    @unittest.skipUnless(shutil.which("node"), "Node.js is not installed")
    def test_extension_javascript_syntax(self):
        result = subprocess.run(
            ["node", "--check", str(EXTENSION / "extension.js")],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__": unittest.main()
