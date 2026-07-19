# Simo Language Guide

## Files and comments

Simo files use the `.simo` extension.

```simo
// Standard comment
note: Beginner-readable comment
```

## Variables and values

```simo
set score = 10
fix maximum = 100

set name = "Alex"
set ready = true
set alternate = yes
set missing = null
set values = [1, 2, 3]
set player = { name: "Alex", score: 10 }
```

`set` creates a mutable binding. `fix` creates an immutable binding.

```simo
score = score + 1
player.score = 50
values[0] = 9
```

## Operators

```simo
set arithmetic = 2 + 3 * 4
set equal = score == 10
set readable_equal = score is 10
set different = score is not 0
set logic = ready and score > 0
set inverted = not ready
```

Boolean values are not numbers: `true == 1` is false.

## Actions

```simo
action multiply(a, b)
    return a * b
end

set result = multiply(4, 5)
```

Actions capture surrounding variables and can update mutable outer bindings.

## Conditions

```simo
if score >= 100
    say("Complete")
else if score > 0
    say("In progress")
else
    say("Not started")
end
```

## Loops

```simo
loop 3 times
    say("Hello")
end

loop while score < 100
    score = score + 10
end

loop for item in ["a", "b", "c"]
    if item == "b"
        continue
    end
    say(item)
end
```

Use `break` to leave a loop and `continue` to start its next iteration.

## Imports

```simo
import "helpers/math.simo"
```

Imports are resolved relative to the importing file. A module is loaded once. Imported declarations share the project environment.

## Error handling

```simo
attempt
    set value = 10 / 0
if it fails
    say("Failed: " + error)
end
```

The catch block receives an immutable `error` text value.

## Built-ins

| Built-in | Purpose |
|---|---|
| `say(value)` | Print to the console; maps to browser console for web builds |
| `ask(prompt)` | Read console input |
| `len(value)` | Collection or text length |
| `text(value)` | Convert to text |
| `number(value)` | Convert to a number |
| `bool(value)` | Convert to a boolean |
| `range(stop)` | Create a numeric list |
| `add(list, value)` | Append to a list |
| `remove(collection, value)` | Remove a list value or object key |
| `contains(collection, value)` | Membership test |
| `keys(object)` / `values(object)` | Object contents |
| `save(key, value)` / `load(key, fallback)` | Persistent storage |
| `read_file(path)` / `write_file(path, text)` | Console file access |
| `assert(condition, message)` | Fail a Simo test or program |
| `random()`, `round()`, `floor()`, `ceil()`, `pi` | Basic math helpers |

`save` and `load` use `.simo-storage.json` for console programs and browser local storage for web/app builds.

## Source tests

Create `tests/test_example.simo`:

```simo
set result = 2 + 2
assert(result == 4, "math should work")
```

Run:

```bash
simo test
```
