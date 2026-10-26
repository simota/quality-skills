#!/usr/bin/env python3
"""Each test breaks one page in a temp copy and asserts figures_check fails.

A green figures_check proves only that it raises no false alarm on today's
pages. Whether it still catches a wrong figure is what this file shows: every
case below passed unnoticed before the checks it names were added.
"""
import contextlib, io, os, pathlib, re, shutil, subprocess, sys, tempfile, unittest
from unittest import mock
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True
try:
    import figures_check as fc  # noqa: E402
except SystemExit:                  # it ran main() on import: no test below would run
    sys.exit("importing figures_check ran its main()")

PAGES = ("SEVERITY", "INTEREST", "BISECTION", "EXTRACTION")

class FakeRepo:
    """Stands in for Repo: `outputs` maps a predicate on argv to (stdout, rc)."""
    def __init__(self, bisect_text="", subject="c1", rc=0, out=None):
        self.calls, self.bisect_text, self.subject, self.rc, self._out = [], bisect_text, subject, rc, out or {}
    def git(self, *a):
        self.calls.append(a)
        text = self.bisect_text if a[:2] == ("bisect", "run") else ""
        return subprocess.CompletedProcess(a, self.rc, text, "")
    def commit(self, *a):
        pass
    def out(self, *a):
        for key, val in self._out.items():
            if key in a:
                return val
        return self.subject


class Broken(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, self.tmp)
        self.orig = {k: getattr(fc, k) for k in PAGES}
        for k in PAGES:
            dst = self.tmp / k; shutil.copy(self.orig[k], dst); setattr(fc, k, dst)
        self.addCleanup(lambda: [setattr(fc, k, v) for k, v in self.orig.items()])
        fc.failures.clear(); self.addCleanup(fc.failures.clear)

    def edit(self, page, old, new):
        p = getattr(fc, page); t = p.read_text(encoding="utf-8")
        self.assertEqual(t.count(old), 1, old); p.write_text(t.replace(old, new), encoding="utf-8")

    def run_main(self):
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                return fc.main()
        except Exception as e:             # a traceback is not a report
            self.fail(f"checker crashed: {type(e).__name__}: {e}")

    def test_pickaxe_recipe_reading_the_newest_match(self):
        self.edit("EXTRACTION", "-- <test file> | head -n 1", "-- <test file> | tail -n 1")
        self.assertNotEqual(self.run_main(), 0)

    def test_pickaxe_recipe_limited_before_it_is_reversed(self):
        # git applies -1 before --reverse, so this reads the newest match.
        self.edit("EXTRACTION", "git log --reverse --format=%cI", "git log --reverse -1 --format=%cI")
        self.assertNotEqual(self.run_main(), 0)

    def test_pickaxe_limit_after_a_quoted_pipe(self):
        # The pipe inside the format is not the pipeline; the limit after it still counts.
        self.edit("EXTRACTION", "git log --reverse --format=%cI", "git log --reverse --format='%H|%cI' -1")
        self.assertNotEqual(self.run_main(), 0)

    def test_example_ending_a_sentence_is_reported_not_raised(self):
        self.edit("INTEREST", "/ 0.3 ≈ 0.3", "/ 0.3 ≈ 0.3.")
        self.assertEqual(self.run_main(), 0, fc.failures)
        self.edit("INTEREST", "/ 0.3 ≈ 0.3.", "/ 0.3 ≈ 0.4.")
        self.assertNotEqual(self.run_main(), 0)

    def test_zero_divisor_is_reported_not_raised(self):
        self.edit("INTEREST", "/ 0.3 ≈ 0.3", "/ 0 ≈ 0.3")
        self.assertNotEqual(self.run_main(), 0)

    def test_zero_divisor_fails_even_when_canonical(self):
        # 0.0 in both SEVERITY tables makes it canonical; dividing by it is still wrong.
        self.edit("SEVERITY", "| 1.0 · 0.6 · 0.3 · 0.2 |", "| 1.0 · 0.6 · 0.0 · 0.2 |")
        self.edit("SEVERITY", "| no tests; stateful, I/O, or concurrent | 0.3 |",
                  "| no tests; stateful, I/O, or concurrent | 0.0 |")
        p = fc.INTEREST
        p.write_text(p.read_text(encoding="utf-8").replace("/ 0.3 ≈", "/ 0.0 ≈")
                     .replace("→ 0.3\n", "→ 0.0\n"), encoding="utf-8")
        self.assertNotEqual(self.run_main(), 0)
        self.assertTrue(any("divisor 0.0" in f for f in fc.failures), fc.failures)

    def test_a_second_formula_that_disagrees(self):
        self.edit("INTEREST", "## Reporting the ranking",
                  "```\ninterest = (touch_score × blast_score × comprehension_score) × confidence_of_fix\n```\n\n"
                  "## Reporting the ranking")
        self.assertNotEqual(self.run_main(), 0)

    def test_a_second_formula_with_a_constant_in_severity(self):
        # SEVERITY has no worked examples, so a digit there exempts nothing.
        self.edit("SEVERITY", "## 5. Regression",
                  "interest = (touch_score × blast_score × comprehension_score) / confidence_of_fix + 1\n\n"
                  "## 5. Regression")
        self.assertNotEqual(self.run_main(), 0)

    def test_a_second_formula_without_parentheses(self):
        self.edit("INTEREST", "## Reporting the ranking",
                  "```\ninterest = touch_score × blast_score\n```\n\n## Reporting the ranking")
        self.assertNotEqual(self.run_main(), 0)

    def test_a_second_formula_indented_or_inline(self):
        # Not at the start of a line is still a statement of the model.
        self.edit("SEVERITY", "## 5. Regression",
                  "- In short: `interest = touch_score × blast_score / confidence_of_fix`\n\n"
                  "## 5. Regression")
        self.assertNotEqual(self.run_main(), 0)
        self.assertTrue(any("formula" in f for f in fc.failures), fc.failures)

    def test_the_formula_restated_inline_and_indented_passes(self):
        formula = "interest = (touch_score × blast_score × comprehension_score) / confidence_of_fix"
        self.edit("INTEREST", "## Reporting the ranking",
                  f"- In short: `{formula}`\n\n    {formula}\n\n## Reporting the ranking")
        self.assertEqual(self.run_main(), 0, fc.failures)

    def test_a_capitalised_or_bold_formula_is_still_a_formula(self):
        for name in ("Interest", "**interest**"):
            with self.subTest(name=name):
                fc.failures.clear()
                self.edit("INTEREST", "## Reporting the ranking",
                          f"{name} = touch_score × blast_score\n\n## Reporting the ranking")
                self.assertNotEqual(self.run_main(), 0)
                self.assertTrue(any("formula" in f for f in fc.failures), fc.failures)
                self.edit("INTEREST", f"{name} = touch_score × blast_score\n\n", "")

    def test_a_capitalised_restatement_of_the_same_formula_passes(self):
        self.edit("INTEREST", "## Reporting the ranking",
                  "Interest = (touch_score × blast_score × comprehension_score) / confidence_of_fix"
                  "\n\n## Reporting the ranking")
        self.assertEqual(self.run_main(), 0, fc.failures)

    def test_a_capitalised_example_is_recomputed(self):
        self.edit("INTEREST", "## Reporting the ranking",
                  "`Interest = (2.0 × 2.0 × 2.0) / 0.3 ≈ 999`\n\n## Reporting the ranking")
        self.assertNotEqual(self.run_main(), 0)
        self.assertTrue(any("999" in f for f in fc.failures), fc.failures)

    def test_an_extra_band_row_with_a_note_is_compared(self):
        self.edit("INTEREST", "| 26+ | 3.0 — this file is where the team lives |",
                  "| 26–60 | 3.0 — this file is where the team lives |\n| 61+ | 5.0 (the whole team) |")
        self.assertNotEqual(self.run_main(), 0)
        self.assertTrue(any("5.0" in f for f in fc.failures), fc.failures)

    def test_a_band_row_with_no_readable_value(self):
        self.edit("INTEREST", "| 26+ | 3.0 — this file is where the team lives |",
                  "| 26–60 | 3.0 — this file is where the team lives |\n| 61+ | about five |")
        self.assertNotEqual(self.run_main(), 0)
        self.assertTrue(any("about five" in f for f in fc.failures), fc.failures)

    def test_a_signal_table_opening_with_a_number_is_not_a_band_scale(self):
        self.edit("INTEREST", "| the invariant is enforced in more than one file | the hour-plus bands |",
                  "| the invariant is enforced in more than one file | 2.0 or 3.0 (the hour-plus bands) |")
        self.assertEqual(self.run_main(), 0, fc.failures)

    def test_a_lower_case_value_header_still_guards_its_rows(self):
        self.edit("INTEREST", "| Commits / 90d | Value |", "| Commits / 90d | value |")
        self.edit("INTEREST", "| 26+ | 3.0 — this file is where the team lives |",
                  "| 26–60 | 3.0 |\n| 61+ | about five |")
        self.assertNotEqual(self.run_main(), 0)
        self.assertTrue(any("about five" in f for f in fc.failures), fc.failures)

    def test_a_malformed_number_is_reported_not_raised(self):
        for old, new in (("0.8%", "0..8%"), ("0.8%", "10.0.8%"),
                         ("At `p = 0.10`", "At `p = 0.10.`")):
            with self.subTest(new=new):
                fc.failures.clear()
                self.edit("BISECTION", old, new)
                self.assertNotEqual(self.run_main(), 0)
                self.edit("BISECTION", new, old)

    def test_log2_of_zero_is_reported_not_raised(self):
        self.edit("BISECTION", "⌈log2 100⌉", "⌈log2 0⌉")
        self.assertNotEqual(self.run_main(), 0)
        self.assertTrue(any("log2 0" in f for f in fc.failures), fc.failures)

    def test_an_inline_example_mid_sentence_is_recomputed(self):
        self.edit("INTEREST", "## Reporting the ranking",
                  "With tests the first entry drops to interest = (2.0 × 2.0 × 2.0) / 1.0 ≈ 8.\n\n"
                  "## Reporting the ranking")
        self.assertEqual(self.run_main(), 0, fc.failures)
        self.edit("INTEREST", "/ 1.0 ≈ 8.", "/ 1.0 ≈ 9.")
        self.assertNotEqual(self.run_main(), 0)

    def test_a_second_example_on_the_same_line_is_recomputed(self):
        # One mention ran to the end of the line and only its prefix was parsed.
        self.edit("INTEREST", "## Reporting the ranking",
                  "Compare interest = (2.0 × 2.0 × 2.0) / 1.0 ≈ 8 with "
                  "interest = (2.0 × 2.0 × 2.0) / 0.3 ≈ 27.\n\n## Reporting the ranking")
        self.assertEqual(self.run_main(), 0, fc.failures)
        self.edit("INTEREST", "/ 0.3 ≈ 27.\n", "/ 0.3 ≈ 999.\n")
        self.assertNotEqual(self.run_main(), 0)
        self.assertTrue(any("999" in f for f in fc.failures), fc.failures)

    def test_a_formula_after_an_example_on_the_same_line(self):
        self.edit("INTEREST", "## Reporting the ranking",
                  "So interest = (2.0 × 2.0 × 2.0) / 1.0 ≈ 8, since "
                  "interest = touch_score × blast_score.\n\n## Reporting the ranking")
        self.assertNotEqual(self.run_main(), 0)
        self.assertTrue(any("formula" in f for f in fc.failures), fc.failures)

    def test_an_extra_example_does_not_excuse_a_formula_with_a_digit(self):
        # Counting lines against parses let the one cancel the other.
        self.edit("INTEREST", "## Reporting the ranking",
                  "With tests the first entry drops to interest = (2.0 × 2.0 × 2.0) / 1.0 ≈ 8.\n\n"
                  "```\ninterest = touch_score × blast_score / confidence_of_fix   (v1, retired 2026)\n```\n\n"
                  "## Reporting the ranking")
        self.assertNotEqual(self.run_main(), 0)
        self.assertTrue(any("formula" in f for f in fc.failures), fc.failures)

    def test_a_formula_carrying_a_constant_in_both_files_passes(self):
        for page in ("SEVERITY", "INTEREST"):
            self.edit(page, "comprehension_score) / confidence_of_fix\n",
                      "comprehension_score) / max(confidence_of_fix, 0.2)\n")
        self.assertEqual(self.run_main(), 0, fc.failures)

    def test_a_later_table_is_not_the_canonical_divisor_table(self):
        p = fc.SEVERITY
        p.write_text(p.read_text(encoding="utf-8")
                     + "\n| Threshold | Value |\n|---|---|\n| quarantine above | 0.05 |\n"
                     + "\n**Flake classes — canonical values.**\n\n| a | b |\n|---|---|\n| x | y |\n",
                     encoding="utf-8")
        self.assertEqual(self.run_main(), 0, fc.failures)

    def test_divisor_values_restated_in_interest(self):
        self.edit("INTEREST", "## Worked example",
                  "| State | Value |\n|---|---|\n| tested | 1.0 |\n| untested | 0.4 |\n\n## Worked example")
        self.assertNotEqual(self.run_main(), 0)

    def test_divisor_values_restated_in_a_wider_table(self):
        self.edit("INTEREST", "## Worked example",
                  "| State | Value | Why |\n|---|---|---|\n| tested | 1.0 | proven |\n"
                  "| untested | 0.4 | a gamble |\n\n## Worked example")
        self.assertNotEqual(self.run_main(), 0)
        self.assertTrue(any("restates confidence_of_fix" in f for f in fc.failures), fc.failures)

    def test_a_canonical_divisor_with_a_note_is_compared(self):
        self.edit("SEVERITY", "| no tests; behaviour is pure, with no state or I/O | 0.6 |",
                  "| no tests; behaviour is pure, with no state or I/O | 0.5 (pure code is cheap to pin) |")
        self.assertNotEqual(self.run_main(), 0)
        self.assertTrue(any("0.5" in f for f in fc.failures), fc.failures)

    def test_a_wider_canonical_divisor_table_is_read(self):
        self.edit("SEVERITY", "| State | Value |\n|-------|-------|", "| State | Value | Why |\n|---|---|---|")
        p = fc.SEVERITY; t = p.read_text(encoding="utf-8")
        head, table = t.split("| State | Value | Why |", 1)
        body, rest = table.split("\n\n", 1)
        body = "\n".join(l + " because |" if l.startswith("| ") else l for l in body.split("\n"))
        p.write_text(head + "| State | Value | Why |" + body + "\n\n" + rest, encoding="utf-8")
        self.assertEqual(self.run_main(), 0, fc.failures)
        self.edit("SEVERITY", "| no tests; behaviour is pure, with no state or I/O | 0.6 | because |",
                  "| no tests; behaviour is pure, with no state or I/O | 0.5 | because |")
        self.assertNotEqual(self.run_main(), 0)
        self.assertTrue(any("0.5" in f for f in fc.failures), fc.failures)

    def test_a_canonical_divisor_row_with_no_readable_value(self):
        self.edit("SEVERITY", "| no tests; behaviour is pure, with no state or I/O | 0.6 |",
                  "| no tests; behaviour is pure, with no state or I/O | about half |")
        self.assertNotEqual(self.run_main(), 0)
        self.assertTrue(any("about half" in f for f in fc.failures), fc.failures)

    def test_clean_pages_pass(self):
        self.assertEqual(self.run_main(), 0, fc.failures)

    def test_F1_wrong_example_with_equals_sign(self):
        self.edit("INTEREST", "/ 0.3 ≈ 27", "/ 0.3 = 99")
        fc.check_examples(fc.confidence_values()); self.assertTrue(fc.failures)

    def test_F1_wrong_flake_row_without_backticks(self):
        self.edit("BISECTION", "| `K=3` | 99% | 68% |", "| K=3 | 99% | 99% |")
        fc.check_flake_table(); self.assertTrue(fc.failures)

    def test_F1_wrong_compounding_with_equals_sign(self):
        self.edit("BISECTION", "(1 − 0.12)^7 ≈ 59%", "(1 − 0.12)^7 = 99%")
        fc.check_compounding(); self.assertTrue(fc.failures)

    def test_F2_compounding_q_not_the_table_cell(self):
        self.edit("BISECTION", "(1 − 0.12)^7 ≈ 59%", "(1 − 0.15)^7 ≈ 68%")
        fc.check_compounding(); self.assertTrue(fc.failures)

    def test_F3_exit_zero_row_wrong(self):
        self.edit("BISECTION", "| `0` | good |", "| `0` | skip |")
        self.assertEqual(self.run_main(), 1)

    def test_F4_guard_row_narrowed(self):
        self.edit("BISECTION", "| `126`, `127` on the first step and again on the good revision |",
                  "| `126` on the first step and again on the good revision |")
        self.assertEqual(self.run_main(), 1)

    def test_F5_empty_range_is_reported_not_raised(self):
        self.edit("BISECTION", "| `128`+ | **abort the bisect** |", "| `129`+ | **abort the bisect** |")
        self.assertEqual(self.run_main(), 1)

    def test_F6_band_rows_swapped(self):
        self.edit("INTEREST", "| 1–3 | 0.5 |\n| 4–10 | 1.0 |", "| 1–3 | 1.0 |\n| 4–10 | 0.5 |")
        fc.check_bands(fc.confidence_values()); self.assertTrue(fc.failures)

    def test_F7_example_operand_not_a_band(self):
        self.edit("INTEREST", "interest = (2.0 × 2.0 × 2.0) / 0.3 ≈ 27", "interest = (2.5 × 2.0 × 2.0) / 0.3 ≈ 33")
        fc.check_examples(fc.confidence_values()); self.assertTrue(fc.failures)

    def test_F7_arrow_disagrees_with_formula(self):
        self.edit("INTEREST", "blast:  9 importers                      → 2.0",
                  "blast:  9 importers                      → 3.0")
        fc.check_examples(fc.confidence_values()); self.assertTrue(fc.failures)

    def fails_main(self):
        self.assertEqual(self.run_main(), 1, "checker stayed green")

    # ---- summary counts: every return value reaches the green line
    def test_green_line_counts(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(fc.main(), 0)
        self.assertRegex(out.getvalue(), r"^figures green - formula agrees across 2 files, 3 band scales "
                         r"matched, 2 worked examples recomputed, 11 false-good figures recomputed, "
                         r"14 git behaviours re-run against git version \d")

    def test_failure_report_is_printed(self):
        self.edit("INTEREST", "/ 0.3 ≈ 27", "/ 0.3 ≈ 28")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(fc.main(), 1)
        self.assertIn("1 problem(s):", out.getvalue())
        self.assertIn("worked example", out.getvalue())

    # ---- formula
    def test_formula_missing_from_severity(self):
        self.edit("SEVERITY", "interest = (touch", "interst = (touch")
        self.fails_main()

    def test_formula_missing_from_interest(self):
        p = fc.INTEREST; p.write_text(p.read_text(encoding="utf-8").replace("interest =", "cost ="), encoding="utf-8")
        fc.check_formula(); self.assertTrue(fc.failures)

    def test_formula_differs(self):
        self.edit("SEVERITY", "comprehension_score) / confidence_of_fix", "comprehension_score) / confidence")
        self.fails_main()

    # ---- bands
    def test_severity_operand_count(self):
        self.edit("SEVERITY", "| `confidence_of_fix` | the divisor", "| confidence_of_fix | the divisor")
        self.fails_main()

    def test_confidence_scale_disagrees_with_canonical_table(self):
        self.edit("SEVERITY", "| 1.0 · 0.6 · 0.3 · 0.2 |", "| 1.0 · 0.6 · 0.3 · 0.1 |")
        self.fails_main()

    def test_no_canonical_table(self):
        p = fc.SEVERITY; t = p.read_text(encoding="utf-8")
        p.write_text(t.split("canonical values.")[0] + "canonical values.\n", encoding="utf-8")
        fc.confidence_values(); self.assertTrue(fc.failures)

    def test_operand_band_table_missing(self):
        self.edit("INTEREST", "## Input 2 — blast_score", "## Input 2 — blast")
        self.fails_main()

    def test_table_outside_an_input_section_is_ignored(self):
        p = fc.INTEREST; p.write_text(p.read_text(encoding="utf-8") + "\n## Notes\n\n| a | 1.0 |\n", encoding="utf-8")
        self.assertEqual(self.run_main(), 0, fc.failures)

    # ---- worked examples
    def test_example_arithmetic_wrong(self):
        self.edit("INTEREST", "/ 0.3 ≈ 27", "/ 0.3 ≈ 28")
        self.fails_main()

    def test_example_divisor_not_canonical(self):
        self.edit("INTEREST", "interest = (2.0 × 2.0 × 2.0) / 0.3 ≈ 27", "interest = (2.0 × 2.0 × 2.0) / 0.4 ≈ 20")
        self.edit("INTEREST", "no tests, money, stateful        → 0.3", "no tests, money, stateful        → 0.4")
        self.fails_main()

    def test_example_operand_not_a_band_even_when_arrows_agree(self):
        self.edit("INTEREST", "interest = (2.0 × 2.0 × 2.0) / 0.3 ≈ 27", "interest = (2.5 × 2.0 × 2.0) / 0.3 ≈ 33")
        self.edit("INTEREST", "18 commits / 90d                 → 2.0", "18 commits / 90d                 → 2.5")
        self.fails_main()

    def test_no_worked_example(self):
        p = fc.INTEREST; t = p.read_text(encoding="utf-8")
        t = "\n".join(l for l in t.splitlines() if not re.match(r"interest = \(\d", l))
        p.write_text(t, encoding="utf-8")
        fc.check_examples(fc.confidence_values()); self.assertTrue(fc.failures)

    # ---- exit table
    def test_gap_in_exit_table(self):
        self.edit("BISECTION", "| `1`–`124` |", "| `1`–`123` |")
        self.fails_main()

    def test_open_ended_row_missing(self):
        self.edit("BISECTION", "| `128`+ | **abort the bisect** | the predicate itself is broken |\n", "")
        self.fails_main()

    def test_code_claimed_twice(self):
        self.edit("BISECTION", "| `125` | skip |", "| `124` | **bad** | again |\n| `125` | skip |")
        self.fails_main()

    def test_empty_range_beyond_ceiling(self):
        self.edit("BISECTION", "| `125` | skip |", "| `130`–`129` | **bad** | x |\n| `125` | skip |")
        self.fails_main()

    def test_low_end_of_range_wrong(self):
        self.edit("BISECTION", "| `0` | good | the test passed |\n", "")
        self.edit("BISECTION", "| `1`–`124` |", "| `0`–`124` |")
        self.fails_main()

    def test_high_end_of_range_wrong(self):
        self.edit("BISECTION", "| `125` | skip |", "| `126`–`125` | skip |")    # placeholder, replaced below
        p = fc.BISECTION; t = p.read_text(encoding="utf-8")
        t = re.sub(r"^\| `126`–`125` \| skip \|[^\n]*\n", "", t, flags=re.M)
        p.write_text(t.replace("| `1`–`124` |", "| `1`–`125` |"), encoding="utf-8")
        self.fails_main()

    def test_guard_row_wrong_verdict(self):
        self.edit("BISECTION", "| **abort** — `error: bogus", "| **skip** — `error: bogus")
        self.fails_main()

    # ---- execute bit
    def test_execute_bit_claim_missing(self):
        self.edit("BISECTION", "the shell returns 126", "the shell returns code 126")
        self.fails_main()

    def test_execute_bit_claim_wrong(self):
        self.edit("BISECTION", "the shell returns 126", "the shell returns 127")
        self.fails_main()

    # ---- false-good table
    def test_rate_missing(self):
        self.edit("BISECTION", "At `p = 0.10`", "At `q = 0.10`")
        self.fails_main()

    def test_header_missing(self):
        self.edit("BISECTION", "| K (threshold) |", "| threshold |")
        self.fails_main()

    def test_no_k_rows(self):
        p = fc.BISECTION; t = p.read_text(encoding="utf-8")
        p.write_text(re.sub(r"^\| `K=\d+` \|[^\n]*\n", "", t, flags=re.M), encoding="utf-8")
        fc.check_flake_table(); self.assertTrue(fc.failures)

    def test_k_row_short_a_cell(self):
        self.edit("BISECTION", "| `K=3` | 99% | 68% | 15% | 5% |", "| `K=3` | 99% | 68% | 15% |")
        fc.check_flake_table(); self.assertTrue(fc.failures)

    def test_flake_cell_wrong(self):
        self.edit("BISECTION", "| `K=3` | 99% | 68% |", "| `K=3` | 99% | 67% |")
        self.fails_main()

    # ---- compounding
    def test_no_step_count(self):
        self.edit("BISECTION", "⌈log2 100⌉ = 7", "log2(100) rounded up, 7")
        fc.check_compounding(); self.assertTrue(fc.failures)

    def test_step_count_wrong(self):
        self.edit("BISECTION", "⌈log2 100⌉ = 7", "⌈log2 200⌉ = 7")
        self.fails_main()

    def test_compound_arithmetic_wrong(self):
        self.edit("BISECTION", "(1 − 0.12)^7 ≈ 59%", "(1 − 0.12)^7 ≈ 60%")
        self.fails_main()

    def test_compound_over_other_step_count(self):
        self.edit("BISECTION", "(1 − 0.12)^7 ≈ 59%", "(1 − 0.12)^8 ≈ 64%")
        self.fails_main()

    def test_unparsed_uncited_compounding(self):
        p = fc.BISECTION; p.write_text(p.read_text(encoding="utf-8") + "\nAlso 1 − (1 − 0.12)^7 = 59% here.\n", encoding="utf-8")
        fc.check_compounding(); self.assertTrue(fc.failures)

    def test_parsed_but_uncited_compounding(self):
        p = fc.BISECTION; p.write_text(p.read_text(encoding="utf-8") + "\nAlso 1 − (1 − 0.50)^7 ≈ 99%.\n", encoding="utf-8")
        fc.check_compounding(); self.assertTrue(fc.failures)

    # ---- what git did, with a stand-in repo
    def test_observed_blames_the_wrong_commit(self):
        r = FakeRepo("abc123 is the first bad commit", subject="c3")
        self.assertEqual(fc.observed(r, "g", "b", 1, everywhere=False), "bad, but blamed c3 rather than c1")
        r = FakeRepo("abc123 is the first bad commit", subject="c0")
        self.assertEqual(fc.observed(r, "g", "b", 126, everywhere=True), "bad")
        self.assertEqual(r.calls[-1], ("bisect", "reset"))

    def test_observed_unrecognised(self):
        r = FakeRepo("something new", rc=4)
        self.assertEqual(fc.observed(r, "g", "b", 1, everywhere=False), "unrecognised (rc=4)")

    def test_observed_good(self):
        self.assertEqual(fc.observed_good(FakeRepo("abc is the first bad commit", subject="c5"), "g", "b"), "good")
        self.assertEqual(fc.observed_good(FakeRepo("abc is the first bad commit", subject="c4"), "g", "b"),
                         "not good (rc=0)")
        r = FakeRepo("nothing", rc=2)
        self.assertEqual(fc.observed_good(r, "g", "b"), "not good (rc=2)")
        self.assertEqual(r.calls[-1], ("bisect", "reset"))

    def pick(self, **out):
        with mock.patch.object(fc, "Repo", lambda d: FakeRepo(out=out)):
            fc.check_pickaxe(self.tmp)
        return fc.failures

    def test_pickaxe_guards(self):
        good = {"--reverse": "first\nsecond\ndrop", "-1": "drop", "-S": "drop\nsecond\nfirst"}
        self.assertEqual(self.pick(**good), [])
        shutil.rmtree(self.tmp / "pickaxe")
        self.assertTrue(self.pick(**{**good, "--reverse": "second\nfirst"})); fc.failures.clear()
        shutil.rmtree(self.tmp / "pickaxe")
        self.assertTrue(self.pick(**{**good, "-1": "second"})); fc.failures.clear()
        shutil.rmtree(self.tmp / "pickaxe")
        self.assertTrue(self.pick(**{**good, "-S": "second\nfirst"}))

    def stat(self, line):
        d = self.tmp / "shortstat"
        if d.exists():
            shutil.rmtree(d)
        fc.failures.clear()
        with mock.patch.object(fc, "Repo", lambda d: FakeRepo(out={"--shortstat": line})):
            n = fc.check_shortstat(self.tmp)
        return n, list(fc.failures)

    def test_shortstat_guards(self):
        self.assertEqual(self.stat(" 1 file changed, 2 deletions(-)"), (1, []))
        for line in ("1 file changed", "1 file changed, 2", "1 file changed, x deletions(-)",
                     "1 file changed, 2 removals(-)", "1 file changed, 2 deletions(-), 1 insertion(+)"):
            with self.subTest(line=line):
                self.assertTrue(self.stat(line)[1])

    # ---- environment and entry point
    def test_git_env_is_isolated(self):
        r = subprocess.run([sys.executable, "-c", "import figures_check as fc; "
                            "print('GIT_DIR' in fc.GIT_ENV, 'PATH' in fc.GIT_ENV, fc.GIT_ENV.get('LC_ALL'))"],
                           cwd=HERE, env={**os.environ, "GIT_DIR": "/nowhere"}, capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), "False True C")

    def test_import_does_not_run_and_script_exits_nonzero_on_failure(self):
        r = subprocess.run([sys.executable, "-c", "import figures_check; print('imported')"],
                           cwd=HERE, capture_output=True, text=True)
        self.assertIn("imported", r.stdout)
        with tempfile.TemporaryDirectory() as t:
            root = pathlib.Path(t) / "repo"
            shutil.copytree(HERE.parent, root, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            b = root / "skills/quality-regression/reference/bisection.md"
            b.write_text(b.read_text(encoding="utf-8").replace("the shell returns 126", "the shell returns 127"),
                         encoding="utf-8")
            r = subprocess.run([sys.executable, str(root / "quality-tools/figures_check.py")],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 1, r.stdout)

    def test_temp_dir_is_removed(self):
        made = []
        real = tempfile.mkdtemp
        def spy(*a, **k):
            made.append(real(*a, **k)); return made[-1]
        with mock.patch.object(fc.tempfile, "mkdtemp", spy):
            self.run_main()
        self.assertTrue(made)
        self.assertFalse(any(os.path.exists(m) for m in made))


if __name__ == "__main__":
    unittest.main(verbosity=1)
