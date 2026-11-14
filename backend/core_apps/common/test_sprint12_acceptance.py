"""Release evidence must retain omissions and recognize import/contract gaps."""

from tools.qa.sprint12_acceptance import (
    TRANSPORT_FIELDS, junit_result, project_view_imports, transport_differences,
)


def test_junit_omissions_are_not_acceptance_passes(tmp_path):
    path = tmp_path / "results.xml"
    path.write_text('''<testsuites><testsuite>
      <testcase classname="flow" name="good"/>
      <testcase classname="flow" name="device"><skipped message="device missing"/></testcase>
      <testcase classname="flow" name="authority"><skipped type="pytest.xfail" message="known gap"/></testcase>
    </testsuite></testsuites>''')
    result = junit_result(path)
    assert result["regression_passed"]
    assert not result["all_cases_passed"]
    assert result["counts"] == {"passed": 1, "skipped": 1, "expected_failure": 1}
    assert result["omissions"][1]["reason"] == "known gap"


def test_junit_errors_and_unexpected_pass_failures_block_regression(tmp_path):
    path = tmp_path / "results.xml"
    path.write_text('''<testsuite>
      <testcase name="setup"><error message="fixture failed"/></testcase>
      <testcase name="xpass"><failure message="XPASS(strict)"/></testcase>
    </testsuite>''')
    result = junit_result(path)
    assert not result["regression_passed"]
    assert result["counts"] == {"error": 1, "failure": 1}


def test_empty_junit_cannot_pass(tmp_path):
    path = tmp_path / "empty.xml"
    path.write_text("<testsuites/>")
    result = junit_result(path)
    assert not result["all_cases_passed"]
    assert not result["regression_passed"]


def test_service_scan_resolves_relative_and_parent_imports():
    result = project_view_imports(
        "from ..planning_views import helper\nfrom .. import views\n"
        "from ..planning_group_views_parts.process_payload import invalidate_process\n"
        "import core_apps.other.account_views\nfrom rest_framework.views import APIView\n",
        "core_apps.features.services.access",
    )
    assert {row["import"] for row in result} == {
        "core_apps.features.planning_views", "core_apps.features.planning_views.helper",
        "core_apps.features.views", "core_apps.other.account_views",
        "core_apps.features.planning_group_views_parts.process_payload",
        "core_apps.features.planning_group_views_parts.process_payload.invalidate_process",
    }


def test_service_package_relative_imports():
    assert project_view_imports(
        "from ...views import helper", "core_apps.features.services.nested", True,
    )[0]["import"] == "core_apps.features.views"


def test_transport_report_retains_removed_added_and_changed_aliases():
    original = {key: [] for key in TRANSPORT_FIELDS} | {"route": "one/", "name": "one"}
    changed = original | {"aliases": ["new-alias/"]}
    diff = transport_differences([original, original | {"route": "removed/"}],
                                 [changed, original | {"route": "added/"}])
    assert diff["added"] == ["added/"]
    assert diff["removed"] == ["removed/"]
    assert diff["changed"] == [{"route": "one/", "field": "aliases",
                               "before": [], "after": ["new-alias/"]}]
