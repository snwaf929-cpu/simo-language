# Simo Programming Language — v0 Documentation

## Current Interpreter

The current Milestone 1 interpreter requires **Python 3.11+**.

```bash
pip install -e .
simo run examples/section16.simo
```

You can also run it without the installed command:

```bash
python -m simo examples/section16.simo
```

---

## 1. Core Philosophy

- **Name:** Simo — short for "Simple," reflecting the language's core goal: plain English instead of coding jargon.
- **Vision:** "Simplicity at the Speed of Light." Write code the way you'd explain it to a friend.
- **File extension:** `.simo`
- **Goal:** Write one file. Build it as a website, a desktop app, or a game — same syntax, different build target.

```
simo build main.simo --target web     → HTML/CSS/JS (runs in browser)
simo build main.simo --target app     → Desktop app (Electron-style)
```

---

## 2. Variables

| Keyword | Meaning | Example |
|---|---|---|
| `set` | Changeable variable | `set score = 100` |
| `fix` | Locked/constant variable | `fix pi = 3.14` |

```simo
set score = 100
fix max_players = 10
score = score + 1     // OK
max_players = 20      // ERROR: max_players is fixed
```

---

## 3. Data Types

Types are inferred automatically — no manual type declarations.

```simo
set name = "Alex"                          // text
set score = 100                            // number
set is_ready = true    // or: yes          // boolean (true/false and yes/no both work)
set fruits = ["apple", "pear", "mango"]    // list
set player = { name: "Alex", score: 100 }  // group (object)
```

---

## 4. Functions — `action`

```simo
action greet(name)
    say("Hello, " + name)
end

greet("Alex")

action add(a, b)
    return a + b
end

set total = add(5, 3)
```

---

## 5. Output — `say`

```simo
say("Hello World")
say("Score: " + score)
```

---

## 6. Conditionals

```simo
if score == 100 or score is 100     // == and "is" both work
    say("Perfect")
else if score is not 0
    say("Still playing")
else
    say("Game over")
end
```

Logic words: `and`, `or`, `not`.

---

## 7. Loops — `loop`

```simo
loop 5 times
    say("Hi")
end

loop while score < 100
    score = score + 10
end

loop for fruit in fruits
    say(fruit)
end
```

**Important:** `while` (blocking loop) is NOT used for real-time checks like key input — it freezes the program. Use `if` inside `every frame` instead (see Section 13).

---

## 8. Lists & Objects

```simo
set fruits = ["apple", "pear"]
add "grape" to fruits
remove "apple" from fruits

set player = { name: "Alex", score: 100 }
say(name of player)
change score of player to 50
```

---

## 9. Error Handling

```simo
attempt
    set result = 10 / 0
if it fails
    say("Something went wrong!")
end
```

---

## 10. Concurrency

| Keyword | Meaning |
|---|---|
| `start ___()` | Run a task in the background, don't wait |
| `wait(seconds)` | Pause for a fixed amount of time |
| `wait until ___ and ___` | Pause until specific background tasks finish |

```simo
start download_data()
start load_assets()
wait until download_data() and load_assets()
say("Both finished")
```

---

## 11. Comments

```simo
// quick comment
note: more beginner-readable comment (both work, functionally identical)
```

---

## 12. UI / Apps — `page`

One syntax, works for web AND desktop (and eventually mobile) via build target.

```simo
page "My App" size 400x600 {

    show heading "Welcome to Simo" size big color blue

    show button "Click Me" {
        when clicked:
            say("You clicked it!")
            change color of this to green
    }

    show input box named username placeholder "Enter your name"

    show text "Hello, " + username.value when username changes

}
```

### Attribute rule
Any `show` element takes a `{ }` block of `attribute_name value` pairs — no `=`, no quotes unless it's text.

```simo
show button "Play" {
    size 150x50
    color red
    position top right
    visible true
}
```

### Images

```simo
show image "cat.png"

show image "logo.png" {
    size 200x100
    position center
    alt "Company Logo"
    rounded
}
```

| Attribute | Meaning |
|---|---|
| `size WxH` | Width x height |
| `position` | `center`, `top left`, `bottom right`, etc. |
| `alt "___"` | Screen-reader text |
| `rounded` | Rounded corners |

### Platform-specific code

```simo
if platform is "app"
    save tasks to file "tasks.txt"
else
    save tasks to browser storage
end
```

---

## 13. Making a Game

### Scene
```simo
scene "Level 1" size 800x600 {
    background color skyblue
}
```

### Sprite
```simo
sprite player {
    image "player.png"
    x = 100
    y = 300
    speed = 5
}
```

### Game loop — `every frame`
Runs continuously (~60 times/second).

```simo
every frame
    if key "right" is down
        player.x = player.x + player.speed
    end
end
```

### Collision
```simo
if player touches coin
    remove coin
    score = score + 10
end
```

---

## 14. Input — Keyboard, Mouse, Touch

```simo
// Keyboard
if key "space" is pressed    // fires once
if key "right" is down        // true while held
if key "space" is released    // fires once, on release

// Mouse
if mouse is clicked
if mouse is down

// Touch
if touch is pressed
if touch is down
if touch is released
```

### Unified input — `control` (works across keyboard/touch/mouse automatically)

```simo
control "jump" {
    key "space"
    touch tap
}

control "move_right" {
    key "right"
    touch swipe_right
}

every frame
    if action "move_right" is down
        player.x = player.x + player.speed
    end
    if action "jump" is pressed
        player.jump()
    end
end
```

Write gameplay logic once — it works on keyboard, mouse, or touch without rewriting anything.

---

## 15. Time

| Keyword | Meaning |
|---|---|
| `frame` | Current frame number since start (increments every `every frame` tick) |
| `time()` | Real-world time in seconds, always increasing (like Lua's `tick()`) |
| `delta_time` | Seconds since the last frame — use for movement/timers so speed is consistent across devices |

### Cooldown example
```simo
set last_ability_time = 0
fix cooldown_length = 5

action use_ability()
    set now = time()
    if now - last_ability_time >= cooldown_length
        say("Ability used!")
        last_ability_time = now
    else
        set time_left = cooldown_length - (now - last_ability_time)
        say("On cooldown! " + time_left + "s left")
    end
end
```

### Optional built-in shortcut
```simo
cooldown ability_cd length 5

action use_ability()
    if ability_cd is ready
        say("Ability used!")
        start ability_cd
    else
        say("On cooldown! " + ability_cd.time_left + "s left")
    end
end
```

---

## 16. Full Example Program

```simo
set player_name = "Alex"
fix max_score = 100
set score = 0

action welcome_sequence()
    say("Loading Simo Engine...")
    say("Hello, " + player_name)
end

action add_points(amount)
    score = score + amount
    if score >= max_score
        say("Max score reached!")
    end
end

welcome_sequence()

loop 3 times
    add_points(40)
end

say("Final score: " + score)
```

---

## 17. OPEN QUESTIONS — Not Yet Decided

1. **Nested `of`** — how to access deep fields, e.g. an item inside a list inside an object?
2. **Sound** — no keyword yet. Proposal: `play sound "jump.mp3"`
3. **Animation** — proposal: `animate player using ["walk1.png", "walk2.png"] speed 0.2`
4. **Scene switching** — proposal: `go to scene "Level 2"`
5. **Gravity/physics** — built-in (`sprite player { gravity true }`) or fully manual via `every frame`?
6. **Touch gestures** — default gesture list: `tap`, `swipe_right/left/up/down`, `hold`, `pinch`?
7. **Multi-touch** — support two simultaneous touches (e.g. joystick + button)?
8. **On-screen buttons for mobile** — should `show button` auto-wire into `control` blocks for touch devices?
9. **`ping`** — not yet defined; could mean network latency, a custom event signal, or a visual/audio map ping. Needs a decision on meaning before syntax.
10. **`clock()`** — human-readable time (e.g. `"3:42 PM"`) separate from raw `time()`?
11. **Standard library** — math functions, random numbers, string tools not yet speced.
12. **Roblox/Luau target** — theoretically possible via a transpiler (Simo → Luau), same idea as `--target web`/`--target app`, but not yet designed.

---

## 18. What This Document Is For

This file is the **language specification** — not a working interpreter yet. To turn Simo into a real, runnable language, the next step is to build:

1. A **parser** (reads `.simo` files and understands the syntax)
2. A **compiler/transpiler** (turns parsed Simo into HTML/CSS/JS for `--target web`, or another target later)
3. A **standard library** (built-in functions like `time()`, `say()`, list operations)

This doc can be handed directly to a coding tool (like Claude Code) as the spec to build that interpreter/transpiler from.
