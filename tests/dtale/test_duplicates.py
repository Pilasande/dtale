import mock
import numpy as np
import pandas as pd
import pytest
import sklearn as skl
from pkg_resources import parse_version
from six import PY3

from dtale.app import build_app
from dtale.duplicate_checks import (
    DuplicateCheck,
    NoDuplicatesException,
    NoDuplicatesToShowException,
    RemoveAllDataException,
)
from tests.dtale.test_views import app

if PY3:
    from contextlib import ExitStack
else:
    from contextlib2 import ExitStack


def duplicates_data():
    return pd.DataFrame(
        dict(
            Foo=[1, 2, 3, 4, 5],
            foo=[1, 2, 3, 4, 5],
            fOo=[4, 5, 6, 7, 8],
            foO=[4, 4, 4, 4, 4],
            bar=[5, 5, 5, 6, 6],
        )
    )


def non_duplicate_data():
    return pd.DataFrame(dict(foo=[1, 2, 3], bar=[4, 5, 6]))


@pytest.mark.unit
def test_columns(unittest):
    data_id, duplicates_type = "1", "columns"
    with ExitStack() as stack:
        data = {data_id: duplicates_data()}
        stack.enter_context(mock.patch("dtale.global_state.DATA", data))

        builder = DuplicateCheck(data_id, duplicates_type, {"keep": "first"})
        unittest.assertEquals(builder.test(), {"Foo": ["foo"]})
        new_data_id = builder.execute()
        unittest.assertEquals(
            list(data[new_data_id].columns), ["Foo", "fOo", "foO", "bar"]
        )

    with ExitStack() as stack:
        data = {data_id: duplicates_data()}
        stack.enter_context(mock.patch("dtale.global_state.DATA", data))

        builder = DuplicateCheck(data_id, duplicates_type, {"keep": "last"})
        unittest.assertEquals(builder.test(), {"foo": ["Foo"]})
        new_data_id = builder.execute()
        unittest.assertEquals(
            list(data[new_data_id].columns), ["foo", "fOo", "foO", "bar"]
        )

    with ExitStack() as stack:
        data = {data_id: duplicates_data()}
        stack.enter_context(mock.patch("dtale.global_state.DATA", data))

        builder = DuplicateCheck(data_id, duplicates_type, {"keep": "none"})
        unittest.assertEquals(builder.test(), {"Foo": ["foo"]})
        new_data_id = builder.execute()
        unittest.assertEquals(list(data[new_data_id].columns), ["fOo", "foO", "bar"])

    with ExitStack() as stack:
        data = {data_id: non_duplicate_data()}
        stack.enter_context(mock.patch("dtale.global_state.DATA", data))

        builder = DuplicateCheck(data_id, duplicates_type, {"keep": "none"})
        with pytest.raises(NoDuplicatesException):
            builder.checker.remove(data[data_id])


@pytest.mark.unit
def test_column_names(unittest):
    data_id, duplicates_type = "1", "column_names"
    with ExitStack() as stack:
        data = {data_id: duplicates_data()}
        stack.enter_context(mock.patch("dtale.global_state.DATA", data))

        builder = DuplicateCheck(data_id, duplicates_type, {"keep": "first"})
        unittest.assertEquals(builder.test(), {"foo": ["Foo", "foo", "fOo", "foO"]})
        new_data_id = builder.execute()
        unittest.assertEquals(list(data[new_data_id].columns), ["Foo", "bar"])

    with ExitStack() as stack:
        data = {data_id: duplicates_data()}
        stack.enter_context(mock.patch("dtale.global_state.DATA", data))

        builder = DuplicateCheck(data_id, duplicates_type, {"keep": "last"})
        unittest.assertEquals(builder.test(), {"foo": ["Foo", "foo", "fOo", "foO"]})
        new_data_id = builder.execute()
        unittest.assertEquals(list(data[new_data_id].columns), ["foO", "bar"])

    with ExitStack() as stack:
        data = {data_id: duplicates_data()}
        stack.enter_context(mock.patch("dtale.global_state.DATA", data))

        builder = DuplicateCheck(data_id, duplicates_type, {"keep": "none"})
        unittest.assertEquals(builder.test(), {"foo": ["Foo", "foo", "fOo", "foO"]})
        new_data_id = builder.execute()
        unittest.assertEquals(list(data[new_data_id].columns), ["bar"])

    with ExitStack() as stack:
        data = {data_id: non_duplicate_data()}
        stack.enter_context(mock.patch("dtale.global_state.DATA", data))

        builder = DuplicateCheck(data_id, duplicates_type, {"keep": "none"})
        with pytest.raises(NoDuplicatesException):
            builder.checker.remove(data[data_id])


@pytest.mark.unit
def test_rows(unittest):
    data_id, duplicates_type = "1", "rows"
    with ExitStack() as stack:
        data = {data_id: duplicates_data()}
        stack.enter_context(mock.patch("dtale.global_state.DATA", data))

        builder = DuplicateCheck(
            data_id, duplicates_type, {"keep": "first", "subset": "foo"}
        )
        unittest.assertEquals(builder.test(), 0)
        pre_length = len(data[data_id])
        new_data_id = builder.execute()
        assert pre_length == len(data[new_data_id])

    with ExitStack() as stack:
        data = {data_id: duplicates_data()}
        stack.enter_context(mock.patch("dtale.global_state.DATA", data))

        builder = DuplicateCheck(
            data_id, duplicates_type, {"keep": "first", "subset": ["foO", "bar"]}
        )
        unittest.assertEquals(builder.test(), 3)
        new_data_id = builder.execute()
        assert len(data[new_data_id]) == 2
        unittest.assertEquals(data[new_data_id]["Foo"].tolist(), [1, 4])

    with ExitStack() as stack:
        data = {data_id: duplicates_data()}
        stack.enter_context(mock.patch("dtale.global_state.DATA", data))

        builder = DuplicateCheck(
            data_id, duplicates_type, {"keep": "last", "subset": ["foO", "bar"]}
        )
        unittest.assertEquals(builder.test(), 3)
        new_data_id = builder.execute()
        assert len(data[new_data_id]) == 2
        unittest.assertEquals(data[new_data_id]["Foo"].tolist(), [3, 5])

    with ExitStack() as stack:
        data = {data_id: duplicates_data()}
        stack.enter_context(mock.patch("dtale.global_state.DATA", data))

        builder = DuplicateCheck(
            data_id, duplicates_type, {"keep": "none", "subset": ["foO", "bar"]}
        )
        unittest.assertEquals(builder.test(), 5)
        with pytest.raises(RemoveAllDataException):
            builder.execute()


@pytest.mark.unit
def test_show_duplicates(unittest):
    data_id, duplicates_type = "1", "show"
    with ExitStack() as stack:
        data = {data_id: duplicates_data()}
        stack.enter_context(mock.patch("dtale.global_state.DATA", data))

        builder = DuplicateCheck(data_id, duplicates_type, {"group": ["foo"]})
        unittest.assertEquals(builder.test(), {})
        with pytest.raises(NoDuplicatesToShowException):
            builder.execute()

    with ExitStack() as stack:
        data = {data_id: duplicates_data()}
        stack.enter_context(mock.patch("dtale.global_state.DATA", data))

        builder = DuplicateCheck(data_id, duplicates_type, {"group": ["foO", "bar"]})
        unittest.assertEquals(
            builder.test(),
            {
                "4, 5": dict(count=3, filter=["4", "5"]),
                "4, 6": dict(count=2, filter=["4", "6"]),
            },
        )
        new_data_id = builder.execute()
        assert new_data_id == "2"
        unittest.assertEquals(data[new_data_id]["Foo"].tolist(), [1, 2, 3, 4, 5])

    with ExitStack() as stack:
        data = {data_id: duplicates_data()}
        stack.enter_context(mock.patch("dtale.global_state.DATA", data))

        builder = DuplicateCheck(
            data_id, duplicates_type, {"group": ["foO", "bar"], "filter": ["4", "5"]}
        )
        new_data_id = builder.execute()
        assert new_data_id == "2"
        unittest.assertEquals(data[new_data_id]["Foo"].tolist(), [1, 2, 3])
