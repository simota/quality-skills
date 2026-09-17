#!/usr/bin/env python3
"""Check five previously conflicting gate-to-producer ownership edges.

This is a registry regression test, NOT a model router. The natural-language
request is retained for context; `missing` is an intake observation provided by
the fixture. Agent selection, truthful observations and execution need traces.
"""
from pathlib import Path
import unittest
import yaml

ROOT = Path(__file__).resolve().parent.parent


class AcquisitionOwnership(unittest.TestCase):
    def test_discovered_missing_inputs_have_their_own_producer(self):
        registry = ROOT / 'quality-registry'
        cap = yaml.safe_load((registry / 'capabilities.yaml').read_text(encoding='utf-8'))
        cases = yaml.safe_load((registry / 'acquisition-fixtures.yaml').read_text(encoding='utf-8'))
        self.assertIsInstance(cases, list)
        self.assertTrue(cases, 'An empty fixture file checks no ownership edge')
        boundaries = cap['quality-gate']['not']
        for case in cases:
            with self.subTest(case=case['case'], request=case['ask'], missing=case['missing']):
                owners = [b['go'] for b in boundaries if b['what'] == case['missing']]
                self.assertEqual(owners, [case['expect']])
                self.assertNotEqual(case['expect'], 'quality-gate')


if __name__ == '__main__':
    unittest.main(verbosity=2)
