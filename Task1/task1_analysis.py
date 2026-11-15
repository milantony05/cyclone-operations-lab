"""Reproducible cyclone analysis. Run from the repository root."""
from pathlib import Path
import argparse
import json
import numpy as np
import pandas as pd


def periods(mask):
    """Return half-open events; each five-minute observation contributes duration."""
    mask = mask.fillna(False).astype(bool)
    rows = []
    for _, group in mask.groupby(mask.ne(mask.shift()).cumsum()):
        if group.iloc[0]:
            rows.append(dict(start=group.index[0], end=group.index[-1] + pd.Timedelta(minutes=5),
                             duration_minutes=len(group)*5))
    return pd.DataFrame(rows, columns=['start', 'end', 'duration_minutes'])


def lag_features(values):
    """At origin t, only observed values at t and earlier are available."""
    result = pd.DataFrame({f'lag_{lag}': values.shift(lag) for lag in [0,1,2,3,6,12,24,36]})
    for window in [6,12,36]:
        result[f'mean_{window}'] = values.rolling(window).mean()
        result[f'std_{window}'] = values.rolling(window).std()
    return result


def prepare(raw):
    time = pd.to_datetime(raw.iloc[:,0], errors='coerce').dt.round('s')
    values = raw.iloc[:,1:].apply(pd.to_numeric, errors='coerce')
    values.index = time
    values = values.loc[values.index.notna()].sort_index()
    duplicates = int(values.index.duplicated().sum())
    values = values.groupby(level=0).median()
    if ((values.index.minute % 5 != 0) | (values.index.second != 0)).any():
        raise ValueError('Off-grid timestamps require explicit review')
    index = pd.date_range(values.index.min(), values.index.max(), freq='5min', name='time')
    quality = dict(raw_rows=len(raw), duplicate_timestamps=duplicates, missing_timestamps=len(index)-len(values),
                   markers={c:raw[c][pd.to_numeric(raw[c],errors='coerce').isna()].astype(str).value_counts().to_dict() for c in raw.columns[1:]})
    values = values.reindex(index)
    quality['missing_by_sensor'] = values.isna().sum().to_dict()
    quality['start'] = str(index[0]); quality['end'] = str(index[-1])
    return values, quality


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--data',default='docs/source-data/data.xlsx'); parser.add_argument('--output',default='Task1')
    args=parser.parse_args(); out=Path(args.output); out.mkdir(exist_ok=True,parents=True)
    data, quality=prepare(pd.read_excel(args.data))
    (out/'data_quality.json').write_text(json.dumps(quality,indent=2),encoding='utf-8')
    data.describe(percentiles=[.01,.05,.5,.95,.99]).to_csv(out/'summary_statistics.csv')
    data.corr().to_csv(out/'correlation_matrix.csv')
    print(json.dumps(quality,indent=2),flush=True)
    analyze(data, out)


def analyze(data, out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from sklearn.cluster import MiniBatchKMeans
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import silhouette_score, mean_absolute_error, mean_squared_error
    from sklearn.ensemble import HistGradientBoostingRegressor
    plots=out/'plots'; plots.mkdir(exist_ok=True)
    inlet='Cyclone_Inlet_Gas_Temp'; outlet='Cyclone_Gas_Outlet_Temp'
    # Conservative proxy: low gas temperatures and weak suction for >=30 minutes.
    candidate=(data[inlet]<150)&(data[outlet]<150)&(data['Cyclone_Inlet_Draft'].abs()<30)
    shutdown=pd.Series(False,index=data.index)
    for event in periods(candidate).itertuples():
        if event.duration_minutes>=30: shutdown.loc[(data.index>=event.start)&(data.index<event.end)]=True
    downtime=periods(shutdown); downtime.to_csv(out/'shutdown_periods.csv',index=False)
    complete=data.notna().all(axis=1)
    features=data.copy()
    features['temperature_difference']=data[inlet]-data[outlet]
    features['inlet_delta']=data[inlet].diff()
    features['inlet_rolling_std']=data[inlet].rolling(6).std()
    valid=(~shutdown)&complete&features.notna().all(axis=1)
    scaler=StandardScaler(); x=scaler.fit_transform(features.loc[valid])
    sample=np.random.default_rng(42).choice(len(x),min(5000,len(x)),replace=False)
    choices=[]; models={}
    for k in range(3,7):
        model=MiniBatchKMeans(n_clusters=k,random_state=42,n_init=5,batch_size=4096).fit(x)
        score=silhouette_score(x[sample],model.predict(x[sample]))
        choices.append(dict(k=k,silhouette=score)); models[k]=model
    pd.DataFrame(choices).to_csv(out/'cluster_selection.csv',index=False)
    model=models[max(choices,key=lambda a:a['silhouette'])['k']]
    states=pd.Series(-1,index=data.index,name='state'); states.loc[valid]=model.predict(x)
    summaries=[]; scores=pd.DataFrame(np.nan,index=data.index,columns=data.columns)
    for state in sorted(states[states>=0].unique()):
        subset=data.loc[states==state]; episodes=periods(states==state)
        row=dict(state=int(state),samples=len(subset),frequency_fraction=len(subset)/valid.sum(),episodes=len(episodes),median_duration_minutes=episodes.duration_minutes.median())
        row['description']=f"Inlet median {subset[inlet].median():.1f}; inlet draft median {subset['Cyclone_Inlet_Draft'].median():.1f}"
        for col in data:
            for statistic,value in subset[col].agg(['mean','std','median']).items(): row[f'{col}_{statistic}']=value
            row[f'{col}_p05']=subset[col].quantile(.05); row[f'{col}_p95']=subset[col].quantile(.95)
        summaries.append(row)
        median=subset.median(); scale=(subset-median).abs().median()*1.4826
        scale=scale.clip(lower=1)
        scores.loc[subset.index]=(subset-median).abs()/scale
    pd.DataFrame(summaries).to_csv(out/'clusters_summary.csv',index=False)
    flagged=scores.max(axis=1)>6
    events=periods(flagged); metadata=[]
    for event in events.itertuples():
        segment=scores.loc[(scores.index>=event.start)&(scores.index<event.end)]
        implicated=segment.max().sort_values(ascending=False)
        metadata.append(dict(start=event.start,end=event.end,duration_minutes=event.duration_minutes,
                             state=int(states.loc[event.start]),variables=';'.join(implicated.head(3).index),peak_score=float(implicated.max())))
    anomalies=pd.DataFrame(metadata); anomalies.to_csv(out/'anomalous_periods.csv',index=False)
    pd.DataFrame({'shutdown':shutdown,'state':states,'anomaly':flagged,'complete_telemetry':complete}).to_csv(out/'sample_labels.csv.gz')
    for label,subset in [('representative_week',data.loc['2018-06-01':'2018-06-07']),('full_year',data.loc['2018'])]:
        fig,axes=plt.subplots(2,1,figsize=(14,7),sharex=True)
        subset[[inlet,outlet,'Cyclone_Material_Temp']].plot(ax=axes[0],linewidth=.6)
        subset[[c for c in data if 'draft' in c.lower()]].plot(ax=axes[1],linewidth=.6)
        for event in downtime.itertuples():
            if event.end>=subset.index.min() and event.start<=subset.index.max():
                for ax in axes: ax.axvspan(event.start,event.end,color='red',alpha=.15)
        fig.suptitle(label.replace('_',' ').title()+' (red shading: shutdown proxy)'); fig.tight_layout(); fig.savefig(plots/f'{label}.png',dpi=150); plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,7)); im=ax.imshow(data.corr(),vmin=-1,vmax=1,cmap='coolwarm'); ax.set_xticks(range(6),data.columns,rotation=75,ha='right'); ax.set_yticks(range(6),data.columns); fig.colorbar(im); fig.tight_layout(); fig.savefig(plots/'correlation.png',dpi=150); plt.close(fig)
    case_notes=[]
    selected=anomalies.sort_values('peak_score',ascending=False)
    chosen=[]
    for event in selected.itertuples():
        if any(abs(event.start-t)<pd.Timedelta(days=1) for t in chosen): continue
        chosen.append(event.start)
        window=data.loc[event.start-pd.Timedelta(hours=2):event.end+pd.Timedelta(hours=2)]
        fig,axes=plt.subplots(3,1,figsize=(13,8),sharex=True)
        window[[inlet,outlet,'Cyclone_Material_Temp']].plot(ax=axes[0]); window[[c for c in data if 'draft' in c.lower()]].plot(ax=axes[1]); states.loc[window.index].plot(ax=axes[2],drawstyle='steps-post'); axes[2].set_ylabel('State (-1 unavailable)')
        for ax in axes: ax.axvspan(event.start,event.end,color='red',alpha=.2)
        fig.tight_layout(); fig.savefig(plots/f'anomaly_{len(chosen)}.png',dpi=150); plt.close(fig)
        case_notes.append(f"### Event {len(chosen)}: {event.start}\n\nDuration {event.duration_minutes} minutes, state {event.state}, implicated variables: {event.variables}. Peak robust deviation {event.peak_score:.1f}. Hypothesis: a process transition or instrument excursion. Compare simultaneous temperature and draft changes in the figure; sensor calibration and maintenance logs are required to distinguish these explanations. This is a statistical flag, not an established failure cause.\n")
        if len(chosen)==4: break
    (out/'anomaly_cases.md').write_text('\n'.join(case_notes),encoding='utf-8')
    y=data[inlet]; f=lag_features(y); n=len(y); train_end=int(n*.6); validation_end=int(n*.8)
    predictions=[]; metrics=[]
    for horizon in range(1,13):
        target=y.shift(-horizon); usable=f.notna().all(axis=1)&target.notna()
        positions=np.arange(n); train=usable&(positions+horizon<train_end); validation=usable&(positions>=train_end)&(positions+horizon<validation_end); test=usable&(positions>=validation_end)&(positions+horizon<n)
        best=None
        for leaves in [15,31]:
            reg=HistGradientBoostingRegressor(max_iter=100,max_leaf_nodes=leaves,learning_rate=.08,random_state=42).fit(f.loc[train].iloc[::3],target.loc[train].iloc[::3])
            error=mean_absolute_error(target.loc[validation],reg.predict(f.loc[validation]))
            if best is None or error<best[0]: best=(error,reg,leaves)
        reg=best[1]; actual=target.loc[test]; pred=reg.predict(f.loc[test]); base=y.loc[test]
        for method,p in [('persistence',base),('gradient_boosting',pred)]: metrics.append(dict(horizon_steps=horizon,method=method,MAE=mean_absolute_error(actual,p),RMSE=np.sqrt(mean_squared_error(actual,p)),n=len(actual),selected_leaves=best[2]))
        predictions.append(pd.DataFrame(dict(origin=actual.index,target_time=actual.index+pd.Timedelta(minutes=5*horizon),horizon_steps=horizon,actual=actual.values,persistence=base.values,gradient_boosting=pred)))
        print(f'Forecast horizon {horizon} complete',flush=True)
    forecasts=pd.concat(predictions,ignore_index=True); forecasts.to_csv(out/'forecasts.csv',index=False)
    for method in ['persistence','gradient_boosting']: metrics.append(dict(horizon_steps='overall',method=method,MAE=mean_absolute_error(forecasts.actual,forecasts[method]),RMSE=np.sqrt(mean_squared_error(forecasts.actual,forecasts[method])),n=len(forecasts)))
    pd.DataFrame(metrics).to_csv(out/'forecast_metrics.csv',index=False)
    result=dict(shutdown_events=len(downtime),downtime_hours=float(downtime.duration_minutes.sum()/60),unknown_hours=float((~complete).sum()/12),clusters=len(summaries),anomaly_events=len(anomalies),forecast_train_end=str(data.index[train_end]),forecast_test_start=str(data.index[validation_end]))
    (out/'results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')


if __name__ == '__main__':
    main()
