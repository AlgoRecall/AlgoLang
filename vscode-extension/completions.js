/** Static and document-aware completion suggestions for AlgoLang source files. */

const KEYWORD_COMPLETIONS = [
  { label: "and", kind: "Keyword", detail: "Boolean conjunction" },
  { label: "break", kind: "Keyword", detail: "Exit the nearest loop" },
  { label: "continue", kind: "Keyword", detail: "Continue the nearest loop" },
  { label: "else", kind: "Keyword", detail: "Alternative branch" },
  { label: "false", kind: "Keyword", detail: "Boolean false literal" },
  { label: "fn", kind: "Snippet", detail: "Declare a typed function", insertText: "fn ${1:name}(${2:value}: ${3:int}) -> ${4:int} {\n    ${5:return value}\n}" },
  { label: "for", kind: "Snippet", detail: "Iterate over a collection", insertText: "for ${1:value} in ${2:values} {\n    ${3}\n}" },
  { label: "if", kind: "Snippet", detail: "Conditional block", insertText: "if ${1:condition} {\n    ${2}\n}" },
  { label: "in", kind: "Keyword", detail: "Membership or iteration operator" },
  { label: "not", kind: "Keyword", detail: "Boolean negation" },
  { label: "null", kind: "Keyword", detail: "Null literal" },
  { label: "or", kind: "Keyword", detail: "Boolean disjunction" },
  { label: "print", kind: "Function", detail: "Print a value", insertText: "print(${1:value})" },
  { label: "return", kind: "Keyword", detail: "Return from a function" },
  { label: "true", kind: "Keyword", detail: "Boolean true literal" },
  { label: "while", kind: "Snippet", detail: "Conditional loop", insertText: "while ${1:condition} {\n    ${2}\n}" },
];

const TYPE_COMPLETIONS = [
  { label: "bool", kind: "TypeParameter", detail: "Boolean type" },
  { label: "float", kind: "TypeParameter", detail: "Floating-point number type" },
  { label: "int", kind: "TypeParameter", detail: "Integer type" },
  { label: "string", kind: "TypeParameter", detail: "String type" },
  { label: "[T]", kind: "TypeParameter", detail: "Array type", insertText: "[${1:int}]" },
  { label: "map<K, V>", kind: "Class", detail: "Map collection", insertText: "map<${1:string}, ${2:int}>()" },
  { label: "set<T>", kind: "Class", detail: "Set collection", insertText: "set<${1:int}>()" },
  { label: "stack<T>", kind: "Class", detail: "Stack collection", insertText: "stack<${1:int}>()" },
  { label: "queue<T>", kind: "Class", detail: "Queue collection", insertText: "queue<${1:int}>()" },
  { label: "deque<T>", kind: "Class", detail: "Double-ended queue", insertText: "deque<${1:int}>()" },
  { label: "minheap<T>", kind: "Class", detail: "Minimum heap", insertText: "minheap<${1:int}>()" },
  { label: "maxheap<T>", kind: "Class", detail: "Maximum heap", insertText: "maxheap<${1:int}>()" },
];

const BUILTIN_COMPLETIONS = [
  { label: "len", kind: "Function", detail: "Return the size of a string or collection", insertText: "len(${1:value})" },
  { label: "range", kind: "Function", detail: "Create an integer range", insertText: "range(${1:stop})" },
];

const STATIC_COMPLETIONS = [
  ...KEYWORD_COMPLETIONS,
  ...TYPE_COMPLETIONS,
  ...BUILTIN_COMPLETIONS,
];

/** Collect functions and variables declared in an AlgoLang document. */
function collectDocumentIdentifiers(source) {
  const identifiers = new Map();
  /** Add one unique identifier suggestion to the document-local result. */
  const add = (label, kind, detail) => {
    if (label && !identifiers.has(label)) identifiers.set(label, { label, kind, detail });
  };

  for (const match of source.matchAll(/\bfn\s+([A-Za-z_]\w*)\s*\(([^)]*)\)/gu)) {
    add(match[1], "Function", "Function declared in this file");
    for (const parameter of match[2].matchAll(/\b([A-Za-z_]\w*)\s*:/gu)) {
      add(parameter[1], "Variable", "Function parameter");
    }
  }

  for (const match of source.matchAll(/^\s*([A-Za-z_]\w*)\s*(?::[^=\n]+)?=/gmu)) {
    add(match[1], "Variable", "Variable declared in this file");
  }

  for (const match of source.matchAll(/\bfor\s+([^\n{]+?)\s+in\b/gu)) {
    for (const name of match[1].split(",")) {
      const identifier = name.trim();
      if (/^[A-Za-z_]\w*$/u.test(identifier)) {
        add(identifier, "Variable", "Loop variable");
      }
    }
  }

  return [...identifiers.values()];
}

/** Return static language completions plus identifiers from the document. */
function getCompletions(source) {
  return [...STATIC_COMPLETIONS, ...collectDocumentIdentifiers(source)];
}

module.exports = {
  BUILTIN_COMPLETIONS,
  KEYWORD_COMPLETIONS,
  STATIC_COMPLETIONS,
  TYPE_COMPLETIONS,
  collectDocumentIdentifiers,
  getCompletions,
};
