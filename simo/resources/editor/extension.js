'use strict';

const vscode = require('vscode');
const language = require('./language');

const selector = [
  { language: 'simo', scheme: 'file' },
  { language: 'simo', scheme: 'untitled' },
];

const KIND = {
  variable: vscode.CompletionItemKind.Variable,
  constant: vscode.CompletionItemKind.Constant,
  parameter: vscode.CompletionItemKind.Variable,
  action: vscode.CompletionItemKind.Function,
  builtin: vscode.CompletionItemKind.Function,
  element: vscode.CompletionItemKind.Field,
  property: vscode.CompletionItemKind.Property,
  snippet: vscode.CompletionItemKind.Snippet,
};

function analysisFor(document) {
  return language.analyzeText(document.getText());
}

function completionItem(data) {
  const item = new vscode.CompletionItem(data.label, KIND[data.kind] || vscode.CompletionItemKind.Text);
  item.detail = data.detail;
  item.documentation = new vscode.MarkdownString(data.documentation || '');
  if (data.insertText) {
    item.insertText = new vscode.SnippetString(data.insertText);
  }
  item.sortText = data.kind === 'property' ? `0-${data.label}` : `1-${data.label}`;
  return item;
}

function textBefore(document, position) {
  return document.getText(new vscode.Range(new vscode.Position(0, 0), position));
}

function registerCompletionProvider(context) {
  const provider = vscode.languages.registerCompletionItemProvider(
    selector,
    {
      provideCompletionItems(document, position) {
        const analysis = analysisFor(document);
        const before = textBefore(document, position);
        const completionContext = language.findCompletionContext(before);
        const data = completionContext.kind === 'member'
          ? language.memberCompletions(analysis, completionContext.chain)
          : language.rootCompletions(analysis);
        return data
          .filter((entry) => !completionContext.partial || entry.label.startsWith(completionContext.partial))
          .map(completionItem);
      },
    },
    '.',
  );
  context.subscriptions.push(provider);
}

function hoverForBuiltin(name) {
  const builtin = language.BUILTINS.find((entry) => entry[0] === name);
  if (!builtin) return null;
  const markdown = new vscode.MarkdownString();
  markdown.appendCodeblock(builtin[1], 'simo');
  markdown.appendMarkdown(`\n${builtin[2]}`);
  return markdown;
}

function chainAt(document, position) {
  const line = document.lineAt(position.line).text;
  const left = line.slice(0, position.character);
  const right = line.slice(position.character);
  const leftMatch = left.match(/[A-Za-z_][A-Za-z0-9_.]*$/);
  const rightMatch = right.match(/^[A-Za-z0-9_.]*/);
  return `${leftMatch ? leftMatch[0] : ''}${rightMatch ? rightMatch[0] : ''}`;
}

function registerHoverProvider(context) {
  const provider = vscode.languages.registerHoverProvider(selector, {
    provideHover(document, position) {
      const wordRange = document.getWordRangeAtPosition(position, /[A-Za-z_][A-Za-z0-9_]*/);
      if (!wordRange) return null;
      const word = document.getText(wordRange);
      const builtin = hoverForBuiltin(word);
      if (builtin) return new vscode.Hover(builtin, wordRange);

      const analysis = analysisFor(document);
      const root = language.findSymbol(analysis, word);
      if (root) {
        const markdown = new vscode.MarkdownString();
        markdown.appendCodeblock(root.detail || `${root.kind} ${root.name}`, 'simo');
        if (root.kind === 'element') {
          markdown.appendMarkdown(`\nNamed **${root.elementType}** UI element. Type \`${root.name}.\` for available properties.`);
        } else {
          markdown.appendMarkdown(`\nSimo ${root.kind}.`);
        }
        return new vscode.Hover(markdown, wordRange);
      }

      const chain = chainAt(document, position);
      if (chain.includes('.')) {
        const parts = chain.split('.');
        const property = parts.pop();
        const shape = language.resolveChain(analysis.roots, parts);
        const entry = shape && shape.members ? shape.members[property] : null;
        if (entry) {
          const markdown = new vscode.MarkdownString();
          markdown.appendCodeblock(`${property}: ${entry.kind}`, 'simo');
          markdown.appendMarkdown(`\n${entry.documentation || 'Object property.'}`);
          return new vscode.Hover(markdown);
        }
      }
      return null;
    },
  });
  context.subscriptions.push(provider);
}

function offsetRange(document, offset, length) {
  const start = document.positionAt(Math.max(0, offset));
  const end = document.positionAt(Math.max(0, offset + Math.max(1, length)));
  return new vscode.Range(start, end);
}

function symbolKind(kind) {
  if (kind === 'action') return vscode.SymbolKind.Function;
  if (kind === 'constant') return vscode.SymbolKind.Constant;
  if (kind === 'element') return vscode.SymbolKind.Field;
  if (kind === 'page') return vscode.SymbolKind.Class;
  return vscode.SymbolKind.Variable;
}

function registerDocumentSymbols(context) {
  const provider = vscode.languages.registerDocumentSymbolProvider(selector, {
    provideDocumentSymbols(document) {
      const analysis = analysisFor(document);
      const result = [];
      const pageSymbols = analysis.pages.map((page) => {
        const range = offsetRange(document, page.offset, 4);
        return new vscode.DocumentSymbol(page.name, 'Simo page', vscode.SymbolKind.Class, range, range);
      });
      result.push(...pageSymbols);

      for (const action of analysis.actions) {
        const range = offsetRange(document, action.offset, action.name.length);
        result.push(new vscode.DocumentSymbol(action.name, action.detail, vscode.SymbolKind.Function, range, range));
      }
      for (const variable of analysis.variables) {
        const range = offsetRange(document, variable.offset, variable.name.length);
        result.push(new vscode.DocumentSymbol(variable.name, variable.detail, symbolKind(variable.kind), range, range));
      }
      for (const element of analysis.elements) {
        const range = offsetRange(document, element.offset, element.name.length);
        const symbol = new vscode.DocumentSymbol(
          element.name,
          `${element.elementType} element`,
          vscode.SymbolKind.Field,
          range,
          range,
        );
        if (pageSymbols.length === 1) pageSymbols[0].children.push(symbol);
        else result.push(symbol);
      }
      return result;
    },
  });
  context.subscriptions.push(provider);
}

function registerDefinitionProvider(context) {
  const provider = vscode.languages.registerDefinitionProvider(selector, {
    provideDefinition(document, position) {
      const range = document.getWordRangeAtPosition(position, /[A-Za-z_][A-Za-z0-9_]*/);
      if (!range) return null;
      const name = document.getText(range);
      const root = language.findSymbol(analysisFor(document), name);
      if (!root || root.offset === undefined) return null;
      return new vscode.Location(document.uri, document.positionAt(root.offset));
    },
  });
  context.subscriptions.push(provider);
}

function signatureFromData(analysis, call) {
  const builtin = language.BUILTINS.find((entry) => entry[0] === call.name);
  if (builtin) return { label: builtin[1], documentation: builtin[2] };
  const action = analysis.actions.find((entry) => entry.name === call.name);
  if (action) return { label: action.detail, documentation: 'Action declared in this file.' };
  return null;
}

function registerSignatureHelp(context) {
  const provider = vscode.languages.registerSignatureHelpProvider(
    selector,
    {
      provideSignatureHelp(document, position) {
        const call = language.callAt(textBefore(document, position));
        if (!call) return null;
        const signatureData = signatureFromData(analysisFor(document), call);
        if (!signatureData) return null;
        const help = new vscode.SignatureHelp();
        const signature = new vscode.SignatureInformation(signatureData.label, signatureData.documentation);
        const open = signatureData.label.indexOf('(');
        const close = signatureData.label.lastIndexOf(')');
        const parameters = open >= 0 && close > open
          ? signatureData.label.slice(open + 1, close).split(',').map((value) => value.trim()).filter(Boolean)
          : [];
        signature.parameters = parameters.map((name) => new vscode.ParameterInformation(name));
        help.signatures = [signature];
        help.activeSignature = 0;
        help.activeParameter = Math.min(call.activeParameter, Math.max(0, parameters.length - 1));
        return help;
      },
    },
    '(',
    ',',
  );
  context.subscriptions.push(provider);
}

function diagnosticSeverity(name) {
  if (name === 'error') return vscode.DiagnosticSeverity.Error;
  if (name === 'information') return vscode.DiagnosticSeverity.Information;
  return vscode.DiagnosticSeverity.Warning;
}

function registerDiagnostics(context) {
  const collection = vscode.languages.createDiagnosticCollection('simo');
  context.subscriptions.push(collection);
  const timers = new Map();

  const update = (document) => {
    if (document.languageId !== 'simo') return;
    const analysis = analysisFor(document);
    const diagnostics = analysis.diagnostics.map((entry) => {
      const diagnostic = new vscode.Diagnostic(
        offsetRange(document, entry.offset, entry.length),
        entry.message,
        diagnosticSeverity(entry.severity),
      );
      diagnostic.source = 'Simo';
      return diagnostic;
    });
    collection.set(document.uri, diagnostics);
  };

  const schedule = (document) => {
    const key = document.uri.toString();
    if (timers.has(key)) clearTimeout(timers.get(key));
    timers.set(key, setTimeout(() => {
      timers.delete(key);
      update(document);
    }, 180));
  };

  for (const document of vscode.workspace.textDocuments) update(document);
  context.subscriptions.push(vscode.workspace.onDidOpenTextDocument(update));
  context.subscriptions.push(vscode.workspace.onDidChangeTextDocument((event) => schedule(event.document)));
  context.subscriptions.push(vscode.workspace.onDidCloseTextDocument((document) => collection.delete(document.uri)));
}

function activate(context) {
  registerCompletionProvider(context);
  registerHoverProvider(context);
  registerDocumentSymbols(context);
  registerDefinitionProvider(context);
  registerSignatureHelp(context);
  registerDiagnostics(context);
}

function deactivate() {}

module.exports = { activate, deactivate };
