import json
from pathlib import Path
import tempfile
import unittest

from mobile_run_report import summarize
from rerun import mobile_test_path


class MobileRunReportTests(unittest.TestCase):
    def test_renamed_test_directory_is_resolved_without_losing_the_case(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory)
            nested = package / 'test' / 'screen_audit' / 'screen_audit_test.dart'
            nested.parent.mkdir(parents=True)
            nested.write_text('// migrated test')
            self.assertEqual(mobile_test_path(package, nested.name), 'test/screen_audit/screen_audit_test.dart')
            duplicate = package / 'test' / 'other' / nested.name
            duplicate.parent.mkdir()
            duplicate.write_text('// ambiguous')
            with self.assertRaises(ValueError):
                mobile_test_path(package, nested.name)

    def report(self, *events):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'events.jsonl'
            path.write_text('Flutter startup diagnostic\n' + '\n'.join(json.dumps(e) for e in events))
            return summarize(path)

    def test_passing_cases_without_terminal_event_do_not_close_the_gate(self):
        result = self.report(
            {'type': 'testStart', 'test': {'id': 1, 'name': 'price'}},
            {'type': 'testDone', 'testID': 1, 'result': 'success'},
        )
        self.assertEqual(result['test_cases'], {'success': 1})
        self.assertFalse(result['completed_successfully'])

    def test_active_tests_survive_a_misleading_success_terminal(self):
        result = self.report(
            {'type': 'testStart', 'test': {'id': 1, 'name': 'stalled payment'}},
            {'type': 'done', 'success': True},
        )
        self.assertEqual(result['active_at_end'], ['stalled payment'])
        self.assertFalse(result['completed_successfully'])

    def test_hidden_setup_failure_cannot_become_a_green_run(self):
        result = self.report(
            {'type': 'testStart', 'test': {'id': 1, 'name': 'setUpAll'}},
            {'type': 'error', 'testID': 1, 'error': 'fixture failed'},
            {'type': 'testDone', 'testID': 1, 'result': 'error', 'hidden': True},
            {'type': 'done', 'success': True},
        )
        self.assertEqual(result['failed_cases'], ['setUpAll'])
        self.assertFalse(result['completed_successfully'])

    def test_completed_run_distinguishes_skips_and_hidden_teardown(self):
        result = self.report(
            {'type': 'testStart', 'test': {'id': 1, 'name': 'full-release company'}},
            {'type': 'testDone', 'testID': 1, 'result': 'success', 'skipped': True},
            {'type': 'testStart', 'test': {'id': 2, 'name': 'owner recovery'}},
            {'type': 'testDone', 'testID': 2, 'result': 'success'},
            {'type': 'testStart', 'test': {'id': 3, 'name': 'tearDownAll'}},
            {'type': 'testDone', 'testID': 3, 'result': 'success', 'hidden': True},
            {'type': 'done', 'success': True},
        )
        self.assertEqual(result['test_cases'], {'skipped': 1, 'success': 1})
        self.assertTrue(result['completed_successfully'])

    def test_case_identity_keeps_same_named_tests_in_different_files_separate(self):
        result = self.report(
            {'type': 'suite', 'suite': {'id': 1, 'path': '/test/owner_test.dart'}},
            {'type': 'suite', 'suite': {'id': 2, 'path': '/test/tenant_test.dart'}},
            {'type': 'testStart', 'test': {'id': 3, 'suiteID': 1, 'name': 'retains draft'}},
            {'type': 'testDone', 'testID': 3, 'result': 'success'},
            {'type': 'testStart', 'test': {'id': 4, 'suiteID': 2, 'name': 'retains draft'}},
            {'type': 'testDone', 'testID': 4, 'result': 'success'},
            {'type': 'done', 'success': True},
        )
        self.assertEqual(result['case_results'], [
            {'file': 'owner_test.dart', 'name': 'retains draft', 'result': 'success'},
            {'file': 'tenant_test.dart', 'name': 'retains draft', 'result': 'success'},
        ])


if __name__ == '__main__':
    unittest.main()
