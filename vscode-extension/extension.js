const path = require("path");
const os = require("os");
const { spawn } = require("child_process");
const vscode = require("vscode");

const COMMANDS = {
  run: "algolang.run",
  check: "algolang.check",
  ast: "algolang.ast",
  dryrun: "algolang.dryrun",
};

/** @type {vscode.OutputChannel} */
let outputChannel;
/** @type {vscode.DiagnosticCollection} */
let diagnostics;

function activate(context) {
  outputChannel = vscode.window.createOutputChannel("AlgoLang", "algolang");
  diagnostics = vscode.languages.createDiagnosticCollection("algolang");

  context.subscriptions.push(
    outputChannel,
    diagnostics,
    vscode.commands.registerCommand(COMMANDS.run, (resource) => execute("run", resource)),
    vscode.commands.registerCommand(COMMANDS.check, (resource) => execute("check", resource)),
    vscode.commands.registerCommand(COMMANDS.ast, (resource) => execute("ast", resource)),
    vscode.commands.registerCommand(COMMANDS.dryrun, (resource) => executeDryRun(resource)),
    vscode.workspace.onDidCloseTextDocument((document) => diagnostics.delete(document.uri)),
  );
}

function deactivate() {}

async function executeDryRun(resource) {
  const watches = await vscode.window.showInputBox({
    title: "AlgoLang Dry Run",
    prompt: "Variables to watch (comma-separated)",
    placeHolder: "left, right, mid — leave empty to discover variables",
  });
  if (watches === undefined) return;
  const extraArguments = watches.trim() ? ["--watch", watches.trim()] : [];
  return execute("dryrun", resource, extraArguments);
}

async function execute(command, resource, extraArguments = []) {
  const document = await resolveDocument(resource);
  if (!document) return;

  if (document.isUntitled) {
    vscode.window.showErrorMessage("Save the AlgoLang file before running it.");
    return;
  }
  if (document.isDirty && !(await document.save())) {
    vscode.window.showErrorMessage("AlgoLang could not save the active file.");
    return;
  }

  const configuration = vscode.workspace.getConfiguration("algolang", document.uri);
  if (configuration.get("clearOutputBeforeRun", true)) outputChannel.clear();
  diagnostics.delete(document.uri);

  const pythonPath = configuration.get("pythonPath", "python3");
  const runtimeDirectory = resolveRuntimeDirectory(document.uri, configuration);
  const arguments = ["-m", "algolang", command, document.uri.fsPath, ...extraArguments];
  outputChannel.appendLine(`> ${formatCommand(pythonPath, arguments)}`);
  outputChannel.appendLine("");
  revealOutput(configuration, false);

  const result = await vscode.window.withProgress(
    {
      location: vscode.ProgressLocation.Window,
      title: `AlgoLang: ${command} ${path.basename(document.uri.fsPath)}`,
    },
    () => launch(pythonPath, arguments, runtimeDirectory),
  );

  const foundDiagnostics = parseDiagnostics(result.stderr, document);
  diagnostics.set(document.uri, foundDiagnostics);
  revealOutput(configuration, result.code !== 0);

  if (result.code === 0) {
    if (command === "check") {
      vscode.window.setStatusBarMessage(`$(check) AlgoLang: ${path.basename(document.uri.fsPath)} is valid`, 4000);
    }
  } else {
    const noun = foundDiagnostics.length === 1 ? "problem" : "problems";
    const detail = foundDiagnostics.length ? `${foundDiagnostics.length} ${noun}` : "execution failed";
    const selection = await vscode.window.showErrorMessage(`AlgoLang: ${detail}.`, "Show Output");
    if (selection === "Show Output") outputChannel.show(true);
  }
}

async function resolveDocument(resource) {
  let document;
  if (resource instanceof vscode.Uri) {
    document = await vscode.workspace.openTextDocument(resource);
  } else {
    document = vscode.window.activeTextEditor?.document;
  }
  if (!document) {
    vscode.window.showErrorMessage("Open an AlgoLang (.algo) file first.");
    return undefined;
  }
  if (document.languageId !== "algolang" && path.extname(document.uri.fsPath) !== ".algo") {
    vscode.window.showErrorMessage("The active editor is not an AlgoLang file.");
    return undefined;
  }
  return document;
}

function resolveRuntimeDirectory(uri, configuration) {
  const workspaceFolder = vscode.workspace.getWorkspaceFolder(uri);
  const workspacePath = workspaceFolder?.uri.fsPath || path.dirname(uri.fsPath);
  let configured = configuration.get("runtimeDirectory", "").trim();
  if (!configured) return workspacePath;
  configured = configured
    .replace(/^~(?=$|[\\/])/, os.homedir())
    .replaceAll("${workspaceFolder}", workspacePath);
  return path.isAbsolute(configured) ? configured : path.resolve(workspacePath, configured);
}

function launch(pythonPath, arguments, cwd) {
  return new Promise((resolve) => {
    let stdout = "";
    let stderr = "";
    let settled = false;
    const child = spawn(pythonPath, arguments, {
      cwd,
      env: process.env,
      windowsHide: true,
    });

    child.stdout.on("data", (chunk) => {
      const text = chunk.toString();
      stdout += text;
      outputChannel.append(text);
    });
    child.stderr.on("data", (chunk) => {
      const text = chunk.toString();
      stderr += text;
      outputChannel.append(text);
    });
    child.on("error", (error) => {
      if (settled) return;
      settled = true;
      const message = `Unable to start '${pythonPath}': ${error.message}`;
      stderr += message;
      outputChannel.appendLine(message);
      resolve({ code: -1, stdout, stderr });
    });
    child.on("close", (code) => {
      if (settled) return;
      settled = true;
      resolve({ code: code ?? -1, stdout, stderr });
    });
  });
}

function parseDiagnostics(stderr, document) {
  const pattern = /^(.+):(\d+):(\d+): (Lexical|Parse|Semantic|Type|Runtime) error: (.+)$/gm;
  const result = [];
  for (const match of stderr.matchAll(pattern)) {
    const line = Math.max(0, Number(match[2]) - 1);
    const column = Math.max(0, Number(match[3]) - 1);
    const lineLength = line < document.lineCount ? document.lineAt(line).text.length : column + 1;
    const endColumn = Math.min(Math.max(column + 1, column), lineLength);
    const range = new vscode.Range(line, column, line, endColumn);
    const diagnostic = new vscode.Diagnostic(
      range,
      match[5],
      vscode.DiagnosticSeverity.Error,
    );
    diagnostic.source = `AlgoLang ${match[4]}`;
    result.push(diagnostic);
  }
  return result;
}

function revealOutput(configuration, failed) {
  const policy = configuration.get("revealOutput", "always");
  if (policy === "always" || (policy === "onError" && failed)) outputChannel.show(true);
}

function formatCommand(program, arguments) {
  return [program, ...arguments].map((part) => {
    if (!/[\s"']/u.test(part)) return part;
    return JSON.stringify(part);
  }).join(" ");
}

module.exports = { activate, deactivate };

