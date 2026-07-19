from __future__ import annotations

import io
import tempfile
import unittest
from pathlib import Path

from simo.errors import RuntimeError as SimoRuntimeError
from simo.interpreter import Interpreter
from simo.source import parse_file, parse_source


def execute(source: str, filename: str = "test.simo") -> str:
    output = io.StringIO()
    program = parse_source(source, filename)
    Interpreter(filename=filename, output_stream=output).interpret(program)
    return output.getvalue()


class InterpreterTests(unittest.TestCase):
    def test_section16_program(self) -> None:
        output = execute(
            '''
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
'''
        )
        self.assertEqual(
            output,
            "Loading Simo Engine...\nHello, Alex\nMax score reached!\nFinal score: 120\n",
        )

    def test_lists_objects_for_loop_and_member_assignment(self) -> None:
        output = execute(
            '''
set player = { name: "Alex", score: 0 }
set values = [10, 20, 30]
loop for value in values
    player.score = player.score + value
end
say(player.name + ": " + player.score)
'''
        )
        self.assertEqual(output.strip(), "Alex: 60")

    def test_index_assignment(self) -> None:
        output = execute(
            '''
set values = [1, 2]
values[0] = 9
say(values[0])
'''
        )
        self.assertEqual(output.strip(), "9")

    def test_builtin_collection_functions(self) -> None:
        output = execute(
            '''
set values = [1]
add(values, 2)
add(values, 3)
remove(values, 2)
say(len(values))
say(contains(values, 3))
'''
        )
        self.assertEqual(output, "2\ntrue\n")

    def test_attempt_catches_runtime_failure(self) -> None:
        output = execute(
            '''
attempt
    set result = 10 / 0
if it fails
    say("caught: " + error)
end
'''
        )
        self.assertIn("caught:", output)
        self.assertIn("Division by zero", output)

    def test_boolean_number_equality_is_type_safe(self) -> None:
        output = execute(
            '''
say(true == 1)
say(false == 0)
say(1 == 1.0)
say(yes == true)
'''
        )
        self.assertEqual(output, "false\nfalse\ntrue\ntrue\n")

    def test_constant_reassignment_fails(self) -> None:
        program = parse_source("fix limit = 2\nlimit = 3\n")
        with self.assertRaises(SimoRuntimeError):
            Interpreter().interpret(program)

    def test_break_and_continue(self) -> None:
        output = execute(
            '''
set result = 0
loop for value in [1, 2, 3, 4]
    if value == 2
        continue
    end
    if value == 4
        break
    end
    result = result + value
end
say(result)
'''
        )
        self.assertEqual(output.strip(), "4")

    def test_note_comment(self) -> None:
        output = execute("note: this is ignored\nsay(\"ok\")\n")
        self.assertEqual(output.strip(), "ok")

    def test_imports_share_global_environment(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "math.simo").write_text(
                "action double(value)\n    return value * 2\nend\n", encoding="utf-8"
            )
            main = root / "main.simo"
            main.write_text('import "math.simo"\nsay(double(6))\n', encoding="utf-8")
            output = io.StringIO()
            Interpreter(filename=str(main), output_stream=output).interpret(parse_file(main))
            self.assertEqual(output.getvalue().strip(), "12")


if __name__ == "__main__":
    unittest.main()
