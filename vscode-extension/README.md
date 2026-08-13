# AlgoLang for VS Code

Lightweight editing and execution support for `.algo` files.

## Features

- AlgoLang syntax highlighting
- Comment toggling, bracket matching, auto-closing, indentation, and folding
- Snippets for functions, conditions, and loops
- Autocomplete for keywords, types, collections, built-ins, and identifiers or
  functions declared in the current file
- **Run** and **Dry Run** buttons in the editor title bar
- **Run**, **Check**, **Show AST**, and **Dry Run** commands in the Command Palette
- Compiler/type/runtime errors in VS Code's Problems collection
- Program results and dry-run tables in the AlgoLang Output channel

## Development installation

1. Open the AlgoLang repository root in VS Code.
2. Open **Run and Debug**.
3. Select **Run AlgoLang Extension**.
4. Press `F5`.
5. In the Extension Development Host window, open an example such as
   `examples/binary_search.algo`.
6. Click the play button in the editor title bar.

The development host uses this repository as the Python runtime directory.

## Usage

With an `.algo` file active:

- Click `$(play)` to run it.
- Click `$(debug-alt)` to dry-run it and optionally enter watched variables.
- Open the Command Palette and search for `AlgoLang` to check the file or show
  its AST.
- Right-click in the editor to access Run, Check, and Dry Run.

## Settings

- `algolang.pythonPath`: Python executable, default `python3`.
- `algolang.runtimeDirectory`: folder containing the `algolang` Python package;
  empty means the current workspace folder.
- `algolang.autocomplete.enabled`: enable autocomplete suggestions; defaults to
  `true`.
- `algolang.clearOutputBeforeRun`: clear output before commands.
- `algolang.revealOutput`: `always`, `onError`, or `never`.

When using the extension outside this repository, install AlgoLang into the
selected Python environment or set `algolang.runtimeDirectory` to a checkout of
this repository.

## Packaging

With Microsoft's VS Code Extension Manager installed:

```sh
cd vscode-extension
npx @vscode/vsce package
```

Then select **Extensions: Install from VSIX...** in VS Code.
