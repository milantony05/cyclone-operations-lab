import pandas as pd
from sensor_analysis.task1_analysis import prepare, periods


def test_missing_grid_and_duplicate_median():
    raw=pd.DataFrame({'time':pd.to_datetime(['2020-01-01 00:00','2020-01-01 00:00','2020-01-01 00:10']), 'sensor':[2,4,'Comm Fail']})
    data,audit=prepare(raw)
    assert len(data)==3 and data.iloc[0,0]==3
    assert data.iloc[1:,0].isna().all()
    assert audit['duplicate_timestamps']==1 and audit['missing_timestamps']==1


def test_missing_breaks_event():
    mask=pd.Series([True,None,True],index=pd.date_range('2020',periods=3,freq='5min'))
    assert periods(mask).duration_minutes.tolist()==[5,5]

