#!/usr/bin/env python3
"""Each test breaks one page in a temp copy and asserts figures_check fails.

A green figures_check proves only that it raises no false alarm on today's
pages. Whether it still catches a wrong figure is what this file shows: every
case below passed unnoticed before the checks it names were added.
"""
import contextlib, io, pathlib, shutil, sys, tempfile, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.dont_write_bytecode = True
import figures_check as fc                          # noqa: E402

PAGES = ("SEVERITY", "INTEREST", "BISECTION", "EXTRACTION")

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
        fc.check_bands(); self.assertTrue(fc.failures)

    def test_F7_example_operand_not_a_band(self):
        self.edit("INTEREST", "interest = (2.0 × 2.0 × 2.0) / 0.3 ≈ 27", "interest = (2.5 × 2.0 × 2.0) / 0.3 ≈ 33")
        fc.check_examples(fc.confidence_values()); self.assertTrue(fc.failures)

    def test_F7_arrow_disagrees_with_formula(self):
        self.edit("INTEREST", "blast:  9 importers                      → 2.0",
                  "blast:  9 importers                      → 3.0")
        fc.check_examples(fc.confidence_values()); self.assertTrue(fc.failures)

if __name__ == "__main__":
    unittest.main(verbosity=1)
