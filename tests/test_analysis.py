import numpy as np
import pandas as pd
from sensor_analysis.task1_analysis import periods, lag_features


def test_event_duration_includes_last_sample():
    index = pd.date_range('2020-01-01', periods=5, freq='5min')
    result = periods(pd.Series([False, True, True, False, True], index=index))
    assert result.duration_minutes.tolist() == [10, 5]
    assert result.start.iloc[0] == index[1]


def test_lag_features_never_read_future():
    values = pd.Series(np.arange(30.0))
    original = lag_features(values)
    values.iloc[20:] = 999
    changed = lag_features(values)
    pd.testing.assert_frame_equal(original.iloc[:20], changed.iloc[:20])

