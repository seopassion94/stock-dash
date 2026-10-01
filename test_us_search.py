import os
import unittest
from unittest.mock import patch, Mock
import requests
from us_search import search_us, SearchError


class USSearchTests(unittest.TestCase):
    def test_blank_does_not_call_provider(self):
        with patch('us_search.requests.get') as get:
            self.assertEqual(search_us('  '), [])
            get.assert_not_called()

    @patch.dict(os.environ, {'ALPHAVANTAGE_API_KEY': 'test-key'})
    def test_filters_non_us_and_non_equity_and_deduplicates(self):
        us = {'1. symbol': 'AAPL', '2. name': 'Apple Inc.', '3. type': 'Equity', '4. region': 'United States'}
        response = Mock()
        response.json.return_value = {'bestMatches': [us, us, {**us, '4. region': 'United Kingdom'}, {**us, '3. type': 'ETF'}, None]}
        with patch('us_search.requests.get', return_value=response) as get:
            rows = search_us(' Apple ')
            self.assertEqual([r['티커'] for r in rows], ['AAPL'])
            self.assertEqual(get.call_args.kwargs['params']['keywords'], 'Apple')

    def test_missing_key(self):
        with patch.dict(os.environ, {'ALPHAVANTAGE_API_KEY': ''}):
            with self.assertRaises(SearchError):
                search_us('AAPL')

    @patch.dict(os.environ, {'ALPHAVANTAGE_API_KEY': 'private-key'})
    def test_errors_do_not_expose_provider_messages_or_keys(self):
        for payload in [{'Information': 'private-key'}, {}, [], {'bestMatches': None}]:
            response = Mock()
            response.json.return_value = payload
            with patch('us_search.requests.get', return_value=response):
                with self.assertRaises(SearchError) as error:
                    search_us('AAPL')
                self.assertNotIn('private-key', str(error.exception))
        with patch('us_search.requests.get', side_effect=requests.Timeout('private-key')):
            with self.assertRaises(SearchError) as error:
                search_us('AAPL')
            self.assertNotIn('private-key', str(error.exception))


if __name__ == '__main__':
    unittest.main()
