"""Offline regressions for markup changes and safe export behavior."""
import runpy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
from scipy.integrate import quad
from scipy.stats import gaussian_kde

SCRIPT = Path(__file__).resolve().parents[1] / 'DataImport Script.py'
scraper = runpy.run_path(str(SCRIPT))
parse = scraper['parse_matchups']


def page(name='Spider-man', slug='spider-man', rate='54.32%', count='1,234'):
    return f'''<table><thead><tr><th>Hero</th><th>Matchup</th>
    <th>Win Rate</th><th>Difference</th><th>Matches</th></tr></thead><tbody>
    <tr><td><a href="/characters/{slug}"><img class="mu-face" alt="{name}">
    <span>{name}</span></a></td><td>670W/564L</td><td>{rate}</td>
    <td>+8.64%</td><td>{count}</td></tr></tbody></table>'''


class ScraperTests(unittest.TestCase):
    def test_new_markup_and_name_variants(self):
        for name, slug, label in [('Spider-man', 'spider-man', 'Spider Man'),
                                   ('Star-lord', 'star-lord', 'Star Lord'),
                                   ('Deadpool (Vanguard)', 'deadpool-vanguard', 'Deadpool Vanguard'),
                                   ('Deadpool (Duelist)', 'deadpool-duelist', 'Deadpool Duelist'),
                                   ('Deadpool (Strategist)', 'deadpool-strategist', 'Deadpool Strategist'),
                                   ('Cloak &amp; Dagger', 'cloak-dagger', 'Cloak & Dagger')]:
            with self.subTest(name=name):
                result = parse(page(name, slug), 'Luna Snow', ['Luna Snow', label])
                self.assertEqual(result[label], (54.32, 1234))
                self.assertEqual(result['Luna Snow'], (50.0, 1234))

    def test_reordered_columns_and_no_image(self):
        html = '''<table><thead><tr><th>Matches</th><th>Hero</th><th>Win Rate</th>
        </tr></thead><tbody><tr><td>2,000</td><td>Spider-man</td><td>45.6%</td>
        </tr></tbody></table>'''
        self.assertEqual(parse(html, 'Luna Snow', ['Luna Snow', 'Spider Man'])['Spider Man'],
                         (45.6, 2000))

    def test_bad_or_missing_data_is_rejected(self):
        for html in ['<html>Blocked</html>', page(rate='--'), page(rate='101%'),
                     page(count='0'), page(count='--'), page(slug='new-hero'), page()+page()]:
            with self.subTest(html=html):
                with self.assertRaises(ValueError):
                    parse(html, 'Luna Snow', ['Luna Snow', 'Spider Man'])
        with self.assertRaisesRegex(ValueError, 'missing matchup'):
            parse(page(), 'Luna Snow', ['Luna Snow', 'Spider Man', 'Hulk'])

    def test_failed_scrape_leaves_existing_files_untouched(self):
        main = scraper['main']
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'MarvelRivals_WinRate_Matrix.csv'
            path.write_text('existing data')
            with patch.dict(main.__globals__, scrape_matrices=lambda: parse('<html/>', 'Luna Snow')):
                with self.assertRaises(ValueError):
                    main(folder)
            self.assertEqual(path.read_text(), 'existing data')
            self.assertEqual(len(list(Path(folder).iterdir())), 1)

    def test_payoff_matches_original_formula(self):
        rates = pd.DataFrame([[50., 45.], [55., 50.]], index=['A', 'B'], columns=['A', 'B'])
        counts = pd.DataFrame([[100, 200], [200, 100]], index=rates.index, columns=rates.columns)
        actual = scraper['build_payoff_matrix'](rates, counts)
        kde = gaussian_kde(rates.to_numpy().ravel(), weights=counts.to_numpy().ravel())
        total = quad(lambda x: kde(x).item(), 45, 55)[0]
        expected = rates.map(lambda rate: round(2 * quad(lambda x: kde(x).item(), 45, rate)[0] / total - 1, 2))
        np.testing.assert_allclose(actual, expected)


if __name__ == '__main__':
    unittest.main()
