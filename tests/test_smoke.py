import ibis
import pytest
from process_tree_widget import ProcessTreeWidget


@pytest.fixture(scope="module")
def mde_table():
    return ibis.read_parquet("public/demo.parquet")


@pytest.fixture(scope="module")
def vol_table():
    return ibis.read_parquet("public/pstree.parquet")


def test_mde_widget_builds(mde_table):
    w = ProcessTreeWidget(events=mde_table, source="mde")
    assert len(w.events) > 0


def test_vol_widget_builds(vol_table):
    w = ProcessTreeWidget(events=vol_table, source="volatility")
    assert len(w.events) > 0


def test_mde_widget_has_start_date(mde_table):
    w = ProcessTreeWidget(events=mde_table, source="mde")
    assert w._start_date is not None


def test_vol_widget_has_start_date(vol_table):
    w = ProcessTreeWidget(events=vol_table, source="volatility")
    assert w._start_date is not None
