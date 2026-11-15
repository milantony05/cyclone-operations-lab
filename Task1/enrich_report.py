"""Add measured event comparisons and descriptive state names."""
from pathlib import Path
import pandas as pd
from Task1.task1_analysis import prepare

def main():
    out=Path('Task1'); data,_=prepare(pd.read_excel('data.xlsx'))
    labels=pd.read_csv(out/'sample_labels.csv.gz',index_col=0,parse_dates=True)
    events=pd.read_csv(out/'anomalous_periods.csv',parse_dates=['start','end']).sort_values('peak_score',ascending=False)
    chosen=[]; notes=['# Selected anomaly investigations\n\nComparisons use the 30 minutes before each event and the event median. These are hypotheses, not causal diagnoses.\n']
    for e in events.itertuples():
        if any(abs(e.start-t)<pd.Timedelta(days=1) for t in chosen):continue
        chosen.append(e.start)
        before=data.loc[(data.index>=e.start-pd.Timedelta(minutes=30))&(data.index<e.start)].median()
        during=data.loc[(data.index>=e.start)&(data.index<e.end)].median()
        delta=during-before
        notes.append(f'## Event {len(chosen)}: {e.start}\n\nDuration: {e.duration_minutes} minutes. State at onset: {e.state}. Peak state-relative robust score: {e.peak_score:.1f}.\n')
        for c in data:notes.append(f'- {c}: before {before[c]:.2f}, during {during[c]:.2f}, change {delta[c]:+.2f}.')
        temp=abs(delta['Cyclone_Inlet_Gas_Temp']); draft=abs(delta['Cyclone_Inlet_Draft'])
        hypothesis=('A coupled thermal and draft transient is consistent with a change in gas flow or operating regime.' if temp>30 and draft>20 else 'A localized instrument excursion or sensor calibration issue is plausible when the implicated signal changes more than the other sensors.')
        pre=labels.loc[labels.index<e.start,'state'].iloc[-1]; post=labels.loc[labels.index>=e.end,'state'].iloc[0] if (labels.index>=e.end).any() else -1
        notes.append(f'\nHypothesis: {hypothesis} State before/after: {pre}/{post}. Check the annotated plot for ordering within the five-minute sampling resolution. Maintenance records, fan status and calibration checks are needed to distinguish a process event from an instrument fault. No causal direction is established.\n')
        if len(chosen)==4:break
    (out/'anomaly_cases.md').write_text('\n'.join(notes),encoding='utf-8')
    summary=pd.read_csv(out/'clusters_summary.csv')
    def name(r):
        t=r.Cyclone_Inlet_Gas_Temp_median; d=r.Cyclone_Inlet_Draft_median
        return 'Cool transition / weak draft' if t<500 else ('Warm transition' if t<800 else ('Hot / strong suction' if d<-200 else 'Hot operation'))
    summary['state_name']=summary.apply(name,axis=1)+' (state '+summary.state.astype(str)+')'
    summary.to_csv(out/'clusters_summary.csv',index=False)

if __name__=='__main__':main()
