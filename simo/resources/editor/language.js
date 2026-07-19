'use strict';

const BUILTINS = [
  ['say', 'say(value)', 'Print a value to the console.'],
  ['ask', 'ask(prompt)', 'Ask the user for text. Desktop pages open a native prompt.'],
  ['number', 'number(value)', 'Convert a value to a number.'],
  ['text', 'text(value)', 'Convert a value to text.'],
  ['boolean', 'boolean(value)', 'Convert a value to a boolean.'],
  ['length', 'length(value)', 'Return the size of text, a list, or an object.'],
  ['range', 'range(start, end)', 'Create a list of numbers.'],
  ['append', 'append(list, value)', 'Add a value to a list.'],
  ['remove', 'remove(list, value)', 'Remove a value from a list.'],
  ['contains', 'contains(collection, value)', 'Check whether a collection contains a value.'],
  ['keys', 'keys(object)', 'Return an object’s keys.'],
  ['values', 'values(object)', 'Return an object’s values.'],
  ['save', 'save(key, value)', 'Persist a value for this application.'],
  ['load', 'load(key, fallback)', 'Load a persisted value.'],
  ['read_file', 'read_file(path)', 'Read a text file.'],
  ['write_file', 'write_file(path, text)', 'Write a text file.'],
  ['assert', 'assert(condition, message)', 'Stop when a condition is false.'],
  ['random', 'random()', 'Return a random number.'],
  ['round', 'round(number)', 'Round a number.'],
  ['floor', 'floor(number)', 'Round a number down.'],
  ['ceil', 'ceil(number)', 'Round a number up.'],
  ['open_file_dialog', 'open_file_dialog()', 'Open a native file picker in desktop apps.'],
  ['save_file_dialog', 'save_file_dialog()', 'Open a native save dialog in desktop apps.'],
  ['select_folder', 'select_folder()', 'Open a native folder picker in desktop apps.'],
  ['desktop_notification', 'desktop_notification(title, message)', 'Show a native desktop notification.'],
  ['clipboard_get', 'clipboard_get()', 'Read text from the clipboard.'],
  ['clipboard_set', 'clipboard_set(value)', 'Copy text to the clipboard.'],
  ['open_url', 'open_url(url)', 'Open a URL in the default browser.'],
  ['app_data_path', 'app_data_path()', 'Return this app’s persistent data folder.'],
  ['quit_app', 'quit_app()', 'Close the current desktop app.'],
];

const SNIPPETS = [
  ['set', 'set ${1:name} = ${2:value}', 'Create a mutable variable.'],
  ['fix', 'fix ${1:name} = ${2:value}', 'Create an immutable constant.'],
  ['action', 'action ${1:name}(${2})\n    ${0}\nend', 'Create an action.'],
  ['if', 'if ${1:condition}\n    ${0}\nend', 'Create a condition.'],
  ['ifelse', 'if ${1:condition}\n    ${2}\nelse\n    ${0}\nend', 'Create an if/else condition.'],
  ['loopfor', 'loop for ${1:item} in ${2:items}\n    ${0}\nend', 'Loop over a collection.'],
  ['looptimes', 'loop ${1:5} times\n    ${0}\nend', 'Repeat code a fixed number of times.'],
  ['page', 'page "${1:My App}" size ${2:800x600} {\n    ${0}\n}', 'Create a page.'],
  ['heading', 'show heading "${1:Heading}" named ${2:heading}', 'Show a heading.'],
  ['textui', 'show text "${1:Text}" named ${2:text_label}', 'Show text.'],
  ['input', 'show input box named ${1:input_name} placeholder "${2:Enter text}"', 'Show an input box.'],
  ['button', 'show button "${1:Click me}" named ${2:button} {\n    when clicked:\n        ${0}\n    end\n}', 'Show a button with a click event.'],
  ['object', '{ ${1:key}: ${2:value} }', 'Create an object.'],
  ['list', '[${1:value}]', 'Create a list.'],
  ['attempt', 'attempt\n    ${1}\nif it fails\n    ${0}\nend', 'Handle a runtime failure.'],
];

const ELEMENT_MEMBERS = {
  common: {
    visible: ['boolean', 'Whether the element is visible.'],
    enabled: ['boolean', 'Whether the element can be used.'],
    color: ['text', 'Foreground/text color.'],
    background: ['text', 'Background color.'],
  },
  heading: { text: ['text', 'Displayed heading text.'] },
  text: { text: ['text', 'Displayed text.'] },
  button: { text: ['text', 'Displayed button text.'] },
  input: {
    value: ['text', 'Current text entered by the user.'],
    placeholder: ['text', 'Placeholder shown while empty.'],
  },
  image: { source: ['text', 'Image source path.'] },
};

function unknownShape() {
  return { kind: 'unknown', members: Object.create(null) };
}

function primitiveShape(kind) {
  const shape = { kind, members: Object.create(null) };
  if (kind === 'text') shape.members.length = member('number', 'Number of characters.');
  if (kind === 'list') shape.members.length = member('number', 'Number of items.');
  return shape;
}

function member(kind, documentation, shape = null) {
  return { kind, documentation, shape: shape || primitiveShape(kind) };
}

function objectShape() {
  return { kind: 'object', members: Object.create(null) };
}

function elementShape(type) {
  const shape = { kind: `${type} element`, members: Object.create(null), elementType: type };
  for (const [name, data] of Object.entries(ELEMENT_MEMBERS.common)) {
    shape.members[name] = member(data[0], data[1]);
  }
  for (const [name, data] of Object.entries(ELEMENT_MEMBERS[type] || {})) {
    shape.members[name] = member(data[0], data[1]);
  }
  return shape;
}

function stripComments(source) {
  let output = '';
  let quote = null;
  let escaped = false;
  for (let i = 0; i < source.length; i += 1) {
    const ch = source[i];
    const next = source[i + 1];
    if (quote) {
      output += ch;
      if (escaped) escaped = false;
      else if (ch === '\\') escaped = true;
      else if (ch === quote) quote = null;
      continue;
    }
    if (ch === '"' || ch === "'") {
      quote = ch;
      output += ch;
      continue;
    }
    if (ch === '/' && next === '/') {
      while (i < source.length && source[i] !== '\n') {
        output += ' ';
        i += 1;
      }
      if (i < source.length) output += '\n';
      continue;
    }
    output += ch;
  }
  return output
    .split(/\r?\n/)
    .map((line) => (/^\s*note:/.test(line) ? ' '.repeat(line.length) : line))
    .join('\n');
}

function tokenize(source) {
  const clean = stripComments(source);
  const tokens = [];
  let i = 0;
  while (i < clean.length) {
    const ch = clean[i];
    if (/\s/.test(ch)) {
      i += 1;
      continue;
    }
    if (ch === '"' || ch === "'") {
      const start = i;
      const quote = ch;
      i += 1;
      let escaped = false;
      while (i < clean.length) {
        const current = clean[i];
        i += 1;
        if (escaped) escaped = false;
        else if (current === '\\') escaped = true;
        else if (current === quote) break;
      }
      tokens.push({ type: 'string', value: clean.slice(start, i), offset: start });
      continue;
    }
    if (/[A-Za-z_]/.test(ch)) {
      const start = i;
      i += 1;
      while (i < clean.length && /[A-Za-z0-9_]/.test(clean[i])) i += 1;
      tokens.push({ type: 'identifier', value: clean.slice(start, i), offset: start });
      continue;
    }
    if (/\d/.test(ch)) {
      const start = i;
      i += 1;
      while (i < clean.length && /[0-9.]/.test(clean[i])) i += 1;
      tokens.push({ type: 'number', value: clean.slice(start, i), offset: start });
      continue;
    }
    tokens.push({ type: 'symbol', value: ch, offset: i });
    i += 1;
  }
  return tokens;
}

function resolveChain(roots, chain) {
  if (!chain) return null;
  const parts = Array.isArray(chain) ? chain : chain.split('.').filter(Boolean);
  if (!parts.length) return null;
  let shape = roots[parts[0]] ? roots[parts[0]].shape : null;
  for (let index = 1; shape && index < parts.length; index += 1) {
    const entry = shape.members && shape.members[parts[index]];
    shape = entry ? entry.shape : null;
  }
  return shape || null;
}

function parseChain(tokens, index) {
  const parts = [];
  let cursor = index;
  if (!tokens[cursor] || tokens[cursor].type !== 'identifier') return { parts, next: cursor };
  parts.push(tokens[cursor].value);
  cursor += 1;
  while (
    tokens[cursor] && tokens[cursor].value === '.' &&
    tokens[cursor + 1] && tokens[cursor + 1].type === 'identifier'
  ) {
    parts.push(tokens[cursor + 1].value);
    cursor += 2;
  }
  return { parts, next: cursor };
}

function parseValue(tokens, index, roots) {
  const token = tokens[index];
  if (!token) return { shape: unknownShape(), next: index };
  if (token.value === '{') {
    const shape = objectShape();
    let cursor = index + 1;
    while (cursor < tokens.length && tokens[cursor].value !== '}') {
      const key = tokens[cursor];
      if (key.type !== 'identifier' && key.type !== 'string') {
        cursor += 1;
        continue;
      }
      const name = key.value.replace(/^['"]|['"]$/g, '');
      cursor += 1;
      if (!tokens[cursor] || tokens[cursor].value !== ':') {
        while (cursor < tokens.length && ![',', '}'].includes(tokens[cursor].value)) cursor += 1;
        if (tokens[cursor] && tokens[cursor].value === ',') cursor += 1;
        continue;
      }
      cursor += 1;
      const parsed = parseValue(tokens, cursor, roots);
      shape.members[name] = {
        kind: parsed.shape.kind,
        documentation: `Property ${name}.`,
        shape: parsed.shape,
      };
      cursor = parsed.next;
      if (tokens[cursor] && tokens[cursor].value === ',') cursor += 1;
    }
    return { shape, next: tokens[cursor] && tokens[cursor].value === '}' ? cursor + 1 : cursor };
  }
  if (token.value === '[') {
    let cursor = index + 1;
    let itemShape = unknownShape();
    if (tokens[cursor] && tokens[cursor].value !== ']') {
      const parsed = parseValue(tokens, cursor, roots);
      itemShape = parsed.shape;
      cursor = parsed.next;
    }
    let depth = 1;
    while (cursor < tokens.length && depth > 0) {
      if (tokens[cursor].value === '[') depth += 1;
      if (tokens[cursor].value === ']') depth -= 1;
      cursor += 1;
    }
    const shape = primitiveShape('list');
    shape.itemShape = itemShape;
    return { shape, next: cursor };
  }
  if (token.type === 'string') return { shape: primitiveShape('text'), next: index + 1 };
  if (token.type === 'number') return { shape: primitiveShape('number'), next: index + 1 };
  if (['true', 'false', 'yes', 'no'].includes(token.value)) {
    return { shape: primitiveShape('boolean'), next: index + 1 };
  }
  if (token.value === 'null') return { shape: primitiveShape('null'), next: index + 1 };
  if (token.type === 'identifier') {
    const chain = parseChain(tokens, index);
    const referenced = resolveChain(roots, chain.parts);
    return { shape: referenced || unknownShape(), next: chain.next };
  }
  return { shape: unknownShape(), next: index + 1 };
}

function addRoot(analysis, name, data) {
  if (analysis.roots[name]) {
    analysis.diagnostics.push({
      offset: data.offset,
      length: name.length,
      severity: 'warning',
      message: `“${name}” is already declared in this file.`,
    });
  }
  analysis.roots[name] = data;
}

function analyzeText(source) {
  const tokens = tokenize(source);
  const analysis = {
    roots: Object.create(null), variables: [], actions: [], elements: [], pages: [], diagnostics: [],
  };

  for (let i = 0; i < tokens.length; i += 1) {
    const token = tokens[i];
    if ((token.value === 'set' || token.value === 'fix') && tokens[i + 1]?.type === 'identifier') {
      const nameToken = tokens[i + 1];
      let shape = unknownShape();
      const cursor = i + 2;
      if (tokens[cursor]?.value === '=') shape = parseValue(tokens, cursor + 1, analysis.roots).shape;
      const data = {
        name: nameToken.value,
        kind: token.value === 'fix' ? 'constant' : 'variable',
        shape,
        offset: nameToken.offset,
        detail: `${token.value} ${nameToken.value}: ${shape.kind}`,
      };
      analysis.variables.push(data);
      addRoot(analysis, nameToken.value, data);
      continue;
    }

    if (token.value === 'action' && tokens[i + 1]?.type === 'identifier') {
      const nameToken = tokens[i + 1];
      const params = [];
      let cursor = i + 2;
      if (tokens[cursor]?.value === '(') {
        cursor += 1;
        while (cursor < tokens.length && tokens[cursor].value !== ')') {
          if (tokens[cursor].type === 'identifier') params.push(tokens[cursor].value);
          cursor += 1;
        }
      }
      const action = {
        name: nameToken.value,
        params,
        offset: nameToken.offset,
        detail: `${nameToken.value}(${params.join(', ')})`,
      };
      analysis.actions.push(action);
      addRoot(analysis, nameToken.value, { ...action, kind: 'action', shape: unknownShape() });
      for (const param of params) {
        if (!analysis.roots[param]) {
          analysis.roots[param] = {
            name: param, kind: 'parameter', shape: unknownShape(), offset: nameToken.offset,
            detail: `parameter ${param}`,
          };
        }
      }
      continue;
    }

    if (token.value === 'page') {
      const title = tokens[i + 1]?.type === 'string' ? tokens[i + 1].value.slice(1, -1) : 'Page';
      analysis.pages.push({ name: title, offset: token.offset, detail: `page ${title}` });
      continue;
    }

    if (token.value === 'show') {
      let type = tokens[i + 1]?.value || 'element';
      if (type === 'input' && tokens[i + 2]?.value === 'box') type = 'input';
      let cursor = i + 1;
      while (cursor < tokens.length && cursor < i + 24 && tokens[cursor].value !== 'named') cursor += 1;
      if (tokens[cursor]?.value === 'named' && tokens[cursor + 1]?.type === 'identifier') {
        const nameToken = tokens[cursor + 1];
        const shape = elementShape(type);
        const data = {
          name: nameToken.value, kind: 'element', elementType: type, shape,
          offset: nameToken.offset, detail: `${type} element ${nameToken.value}`,
        };
        analysis.elements.push(data);
        addRoot(analysis, nameToken.value, data);
      }
      continue;
    }

    if (token.type === 'identifier') {
      const chain = parseChain(tokens, i);
      if (chain.parts.length > 1 && tokens[chain.next]?.value === '=') {
        const root = analysis.roots[chain.parts[0]];
        if (root) {
          let shape = root.shape;
          for (let part = 1; part < chain.parts.length; part += 1) {
            const name = chain.parts[part];
            if (!shape.members[name]) shape.members[name] = member('unknown', `Property ${name}.`, objectShape());
            if (part === chain.parts.length - 1) {
              const parsed = parseValue(tokens, chain.next + 1, analysis.roots);
              shape.members[name] = { kind: parsed.shape.kind, documentation: `Property ${name}.`, shape: parsed.shape };
            } else shape = shape.members[name].shape;
          }
        }
      }
    }
  }

  collectStructureDiagnostics(source, analysis.diagnostics);
  return analysis;
}

function collectStructureDiagnostics(source, diagnostics) {
  const clean = stripComments(source);
  const lines = clean.split(/\r?\n/);
  const blocks = [];
  let offset = 0;
  for (const line of lines) {
    const trimmed = line.trim();
    const leading = line.length - line.trimStart().length;
    const lineOffset = offset + leading;
    if (/^(action\b|if\b(?!\s+it\s+fails)|loop\b|attempt\b|when\b.*:)/.test(trimmed)) {
      blocks.push({ offset: lineOffset, text: trimmed.split(/\s+/)[0] });
    } else if (/^end\b/.test(trimmed)) {
      if (!blocks.length) {
        diagnostics.push({
          offset: lineOffset, length: 3, severity: 'error',
          message: 'This end does not match an open action, condition, loop, attempt, or event.',
        });
      } else blocks.pop();
    }
    offset += line.length + 1;
  }
  for (const block of blocks) {
    diagnostics.push({
      offset: block.offset, length: block.text.length, severity: 'warning',
      message: `This ${block.text} block is missing end.`,
    });
  }

  let depth = 0;
  let quote = null;
  let escaped = false;
  for (let i = 0; i < clean.length; i += 1) {
    const ch = clean[i];
    if (quote) {
      if (escaped) escaped = false;
      else if (ch === '\\') escaped = true;
      else if (ch === quote) quote = null;
      continue;
    }
    if (ch === '"' || ch === "'") quote = ch;
    else if (ch === '{') depth += 1;
    else if (ch === '}') {
      depth -= 1;
      if (depth < 0) {
        diagnostics.push({ offset: i, length: 1, severity: 'error', message: 'Unexpected closing brace.' });
        depth = 0;
      }
    }
  }
  if (depth > 0) {
    diagnostics.push({
      offset: Math.max(0, clean.lastIndexOf('{')), length: 1, severity: 'warning',
      message: 'This page or UI element is missing a closing brace.',
    });
  }
}

function memberCompletions(analysis, chain) {
  const shape = resolveChain(analysis.roots, chain);
  if (!shape || !shape.members) return [];
  return Object.entries(shape.members).map(([name, data]) => ({
    label: name, kind: 'property', detail: data.kind,
    documentation: data.documentation || `Property ${name}.`,
  }));
}

function rootCompletions(analysis) {
  const items = [];
  for (const variable of analysis.variables) {
    items.push({ label: variable.name, kind: variable.kind, detail: variable.detail, documentation: `Simo ${variable.kind}.` });
  }
  for (const action of analysis.actions) {
    items.push({
      label: action.name,
      kind: 'action',
      detail: action.detail,
      insertText: `${action.name}(${action.params.map((name, index) => `\${${index + 1}:${name}}`).join(', ')})`,
      documentation: 'Action declared in this file.',
    });
  }
  for (const element of analysis.elements) {
    items.push({
      label: element.name, kind: 'element', detail: element.detail,
      documentation: `Named ${element.elementType} UI element. Type “${element.name}.” to see its properties.`,
    });
  }
  for (const [name, signature, documentation] of BUILTINS) {
    items.push({ label: name, kind: 'builtin', detail: signature, documentation });
  }
  for (const [label, insertText, documentation] of SNIPPETS) {
    items.push({ label, kind: 'snippet', insertText, detail: 'Simo snippet', documentation });
  }
  return items;
}

function findCompletionContext(textBeforeCursor) {
  const match = textBeforeCursor.match(/([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)\.([A-Za-z_][A-Za-z0-9_]*)?$/);
  if (match) return { kind: 'member', chain: match[1], partial: match[2] || '' };
  return { kind: 'root', chain: null, partial: '' };
}

function findSymbol(analysis, name) {
  return analysis.roots[name] || null;
}

function callAt(textBeforeCursor) {
  const match = textBeforeCursor.match(/([A-Za-z_][A-Za-z0-9_]*)\s*\(([^()]*)$/);
  if (!match) return null;
  return { name: match[1], activeParameter: (match[2].match(/,/g) || []).length };
}

module.exports = {
  BUILTINS, SNIPPETS, analyzeText, memberCompletions, rootCompletions,
  findCompletionContext, findSymbol, callAt, resolveChain,
};
