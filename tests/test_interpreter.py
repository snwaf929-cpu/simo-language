"""Tests for the Simo interpreter."""

from __future__ import annotations

import io
import unittest
from pathlib import Path

from simo.cli import run_source
from simo.errors import ParseError, RuntimeError as SimoRuntimeError
from simo.lexer import Lexer
from simo.parser import Parser


EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"


def run_program(source: str, filename: str = "test.simo") -> tuple[int, str]:
    buffer = io.StringIO()
    from simo.interpreter import Interpreter
    from simo.lexer import Lexer
    from simo.parser import Parser

    try:
        tokens = Lexer(source, filename).tokenize()
        program = Parser(tokens, filename).parse()
        Interpreter(filename=filename, output_stream=buffer).interpret(program)
        return 0, buffer.getvalue()
    except Exception as exc:
        return 1, str(exc)


class InterpreterTests(unittest.TestCase):
    def test_mutable_variable_declaration_and_reassignment(self) -> None:
        exit_code, output = run_program(
            """
set score = 0
score = score + 5
say(score)
"""
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(output.strip(), "5")

    def test_constant_reassignment_rejected(self) -> None:
        code = """
fix max_score = 100
max_score = 200
"""
        exit_code, message = run_program(code)
        self.assertEqual(exit_code, 1)
        self.assertIn("max_score", message)
        self.assertIn("constant", message.lower())

    def test_arithmetic_precedence(self) -> None:
        exit_code, output = run_program(
            """
set result = 2 + 3 * 4
say(result)
"""
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(output.strip(), "14")

    def test_string_and_number_concatenation(self) -> None:
        exit_code, output = run_program(
            """
set message = "Score: " + 42
say(message)
set mixed = "ok " + true
say(mixed)
"""
        )
        self.assertEqual(exit_code, 0)
        lines = output.strip().splitlines()
        self.assertEqual(lines[0], "Score: 42")
        self.assertEqual(lines[1], "ok true")

    def test_boolean_aliases(self) -> None:
        exit_code, output = run_program(
            """
set a = yes
set b = no
say(a)
say(b)
"""
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(output.strip().splitlines(), ["true", "false"])

    def test_is_and_is_not(self) -> None:
        exit_code, output = run_program(
            """
set score = 10
if score is 10
    say("equal")
end
if score is not 0
    say("not zero")
end
"""
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(output.strip().splitlines(), ["equal", "not zero"])

    def test_equality_across_strings_numbers_and_booleans(self) -> None:
        exit_code, output = run_program(
            """
if "Alex" is "Alex"
    say("same name")
end
if "Alex" is not "Bob"
    say("different name")
end
if true == yes
    say("boolean aliases equal")
end
if false != true
    say("boolean aliases differ")
end
"""
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(
            output.strip().splitlines(),
            [
                "same name",
                "different name",
                "boolean aliases equal",
                "boolean aliases differ",
            ],
        )

    def test_ordering_comparisons_are_numeric_only(self) -> None:
        exit_code, message = run_program(
            """
if "a" < "b"
    say("unreachable")
end
"""
        )
        self.assertEqual(exit_code, 1)
        self.assertIn("number", message.lower())

    def test_functions_with_parameters_and_return(self) -> None:
        exit_code, output = run_program(
            """
action add(a, b)
    return a + b
end
set total = add(5, 3)
say(total)
"""
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(output.strip(), "8")

    def test_global_mutation_from_function(self) -> None:
        exit_code, output = run_program(
            """
set score = 0
action bump()
    score = score + 10
end
bump()
say(score)
"""
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(output.strip(), "10")

    def test_local_function_variables(self) -> None:
        exit_code, output = run_program(
            """
action demo()
    set local_value = 7
    say(local_value)
end
demo()
"""
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(output.strip(), "7")

    def test_if_else_if_else(self) -> None:
        exit_code, output = run_program(
            """
set score = 50
if score == 100
    say("perfect")
else if score > 40
    say("good")
else
    say("low")
end
"""
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(output.strip(), "good")

    def test_fixed_count_loop(self) -> None:
        exit_code, output = run_program(
            """
set count = 0
loop 3 times
    count = count + 1
end
say(count)
"""
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(output.strip(), "3")

    def test_conditional_loop(self) -> None:
        exit_code, output = run_program(
            """
set score = 0
loop while score < 30
    score = score + 10
end
say(score)
"""
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(output.strip(), "30")

    def test_inline_comments(self) -> None:
        exit_code, output = run_program(
            """
set score = 100 // starting score
say(score)
"""
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(output.strip(), "100")

    def test_undefined_variable(self) -> None:
        exit_code, message = run_program("say(missing)")
        self.assertEqual(exit_code, 1)
        self.assertIn("missing", message)

    def test_undefined_function(self) -> None:
        exit_code, message = run_program("missing()")
        self.assertEqual(exit_code, 1)
        self.assertIn("missing", message)

    def test_incorrect_function_argument_count(self) -> None:
        exit_code, message = run_program(
            """
action add(a, b)
    return a + b
end
add(1)
"""
        )
        self.assertEqual(exit_code, 1)
        self.assertIn("expects 2", message)

    def test_parse_error_with_line_information(self) -> None:
        with self.assertRaises(ParseError) as ctx:
            Parser(Lexer("set = 1", "bad.simo").tokenize(), "bad.simo").parse()
        self.assertEqual(ctx.exception.line, 1)
        self.assertIn("bad.simo", str(ctx.exception))

    def test_section16_example_output(self) -> None:
        source = (EXAMPLES_DIR / "section16.simo").read_text(encoding="utf-8")
        exit_code, output = run_program(source, "section16.simo")
        self.assertEqual(exit_code, 0)
        self.assertEqual(
            output.splitlines(),
            [
                "Loading Simo Engine...",
                "Hello, Alex",
                "Max score reached!",
                "Final score: 120",
            ],
        )

    def test_return_outside_function(self) -> None:
        exit_code, message = run_program("return 1")
        self.assertEqual(exit_code, 1)
        self.assertIn("outside", message.lower())

    def test_cli_run_source_failure_exit_code(self) -> None:
        self.assertEqual(run_source("say(missing)", "bad.simo"), 1)


if __name__ == "__main__":
    unittest.main()
