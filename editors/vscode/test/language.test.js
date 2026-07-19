'use strict';

const assert = require('node:assert/strict');
const language = require('../language');

const source = `
set player = {
    back: {
        images: {
            png1: "player.png",
            png2: "enemy.png"
        }
    }
}

page "Assets" size 640x480 {
    show input box named username placeholder "Player name"
    show button "Start" named start_button {
        when clicked:
            say(player.back.images.png1)
        end
    }
}

action greet(name)
    say("Hello " + name)
end
`;

const analysis = language.analyzeText(source);
assert.equal(analysis.variables[0].name, 'player');
assert.deepEqual(
  language.memberCompletions(analysis, 'player.back.images').map((item) => item.label),
  ['png1', 'png2'],
);
assert.ok(language.memberCompletions(analysis, 'username').some((item) => item.label === 'value'));
assert.ok(language.rootCompletions(analysis).some((item) => item.label === 'greet'));
assert.equal(language.findCompletionContext('set image = player.back.images.').chain, 'player.back.images');
assert.equal(language.callAt('greet(player, ').activeParameter, 1);
assert.deepEqual(analysis.diagnostics, []);

const broken = language.analyzeText('action test()\n    say("x")\n');
assert.ok(broken.diagnostics.some((item) => item.message.includes('missing end')));

console.log('Simo editor intelligence tests passed.');
