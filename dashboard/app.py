"""Interactive review dashboard for the delivered cyclone analysis."""
from pathlib import Path
import json
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
TASK = ROOT / 'Task1'

st.set_page_config(page_title='Cyclone Operations Lab', page_icon='🌀', layout='wide')
st.markdown('''<style>
.block-container{padding-top:2rem;max-width:1500px}
h1,h2,h3{font-family:Arial,sans-serif;color:#173f59}
div[data-testid="stMetric"]{background:#eef5f8;border:1px solid #d6e5ec;border-radius:14px;padding:18px}
</style>''', unsafe_allow_html=True)

@st.cache_data
def load_outputs():
    result=json.loads((TASK/'results.json').read_text())
    shutdown=pd.read_csv(TASK/'shutdown_periods.csv',parse_dates=['start','end'])
    anomalies=pd.read_csv(TASK/'anomalous_periods.csv',parse_dates=['start','end'])
    clusters=pd.read_csv(TASK/'clusters_summary.csv')
    metrics=pd.read_csv(TASK/'forecast_metrics.csv')
    forecasts=pd.read_csv(TASK/'forecasts.csv',parse_dates=['origin','target_time'])
    labels=pd.read_csv(TASK/'sample_labels.csv.gz',index_col=0,parse_dates=True)
    return result,shutdown,anomalies,clusters,metrics,forecasts,labels

def main():
    st.title('Cyclone Operations Lab')
    st.caption('Explore the measured sensor analysis and inspect cited answers from technical manuals. The shutdown and anomaly labels are retrospective hypotheses.')
    result,shutdown,anomalies,clusters,metrics,forecasts,labels=load_outputs()
    pages=st.tabs(['Overview','Shutdowns','Operating states','Anomalies','Forecasts','Document Q&A','Methods'])
    with pages[0]:
        a,b,c,d=st.columns(4)
        a.metric('Sensor observations','377,719');b.metric('Shutdown proxy events',f"{result['shutdown_events']:,}")
        c.metric('Detected downtime',f"{result['downtime_hours']:,.0f} h");d.metric('Anomaly candidates',f"{result['anomaly_events']:,}")
        st.image(str(TASK/'plots/full_year.png'),caption='2018 sensor traces. Red areas satisfy the shutdown proxy.',use_container_width=True)
        st.info('Coverage: January 2017 to August 2020. Missing telemetry is tracked separately from shutdowns.')
    with pages[1]:
        st.subheader('Shutdown event explorer')
        year=st.selectbox('Year',[2017,2018,2019,2020],index=1)
        filtered=shutdown[shutdown.start.dt.year==year]
        st.write(f'{len(filtered)} events, {filtered.duration_minutes.sum()/60:,.1f} hours in {year}')
        st.dataframe(filtered.sort_values('duration_minutes',ascending=False),use_container_width=True,hide_index=True)
        st.caption('Event end is exclusive. Both gas temperatures must be below 150 and absolute inlet draft below 30 for at least 30 minutes.')
    with pages[2]:
        st.subheader('Measured state profiles')
        cols=['state','state_name','samples','frequency_fraction','episodes','median_duration_minutes','Cyclone_Inlet_Gas_Temp_median','Cyclone_Inlet_Draft_median']
        st.dataframe(clusters[cols],use_container_width=True,hide_index=True)
        fig=go.Figure(go.Bar(x=clusters['state_name'],y=clusters['frequency_fraction']*100,marker_color='#197da1'))
        fig.update_layout(yaxis_title='Share of complete active samples (%)',xaxis_title='',height=440)
        st.plotly_chart(fig,use_container_width=True)
        st.caption('Names summarize observed profiles. They are not validated fault or efficiency classifications.')
    with pages[3]:
        st.subheader('Contextual anomaly events')
        available=sorted(anomalies.state.dropna().astype(int).unique())
        chosen=st.multiselect('States',available,default=available)
        filtered=anomalies[anomalies.state.isin(chosen)].sort_values('peak_score',ascending=False)
        st.dataframe(filtered.head(100),use_container_width=True,hide_index=True)
        pictures=list(sorted((TASK/'plots').glob('anomaly_*.png')))
        if pictures:
            pick=st.selectbox('Annotated case',[p.name for p in pictures])
            st.image(str(TASK/'plots'/pick),use_container_width=True)
        with st.expander('Measured case notes'):
            st.markdown((TASK/'anomaly_cases.md').read_text(encoding='utf-8'))
    with pages[4]:
        st.subheader('Held-out forecast comparison')
        chart=metrics[metrics.horizon_steps!='overall'].copy();chart['horizon_steps']=chart.horizon_steps.astype(int)
        fig=go.Figure()
        for method,group in chart.groupby('method'):
            fig.add_trace(go.Scatter(x=group.horizon_steps*5,y=group.RMSE,mode='lines+markers',name=method))
        fig.update_layout(xaxis_title='Forecast horizon (minutes)',yaxis_title='RMSE (native temperature units)',height=440)
        st.plotly_chart(fig,use_container_width=True)
        overall=metrics[metrics.horizon_steps=='overall'];st.dataframe(overall,use_container_width=True,hide_index=True)
        horizon=st.slider('Inspect horizon (minutes)',5,60,60,5)
        view=forecasts[forecasts.horizon_steps==horizon//5].head(200)
        st.line_chart(view.set_index('target_time')[['actual','persistence','gradient_boosting']])
        st.caption('The line chart shows the first 200 held-out predictions at the selected horizon. Forecast origins overlap.')
    with pages[5]:
        st.subheader('Ask the supplied manuals')
        st.caption('First run the indexing command in the README. The local FLAN-T5 model may take time on CPU.')
        question=st.text_input('Question',value='How often does Linatex recommend internal cyclone inspections?')
        if st.button('Search and answer',type='primary'):
            from Task2.prototype.rag_prototype import RAG
            index=ROOT/'Task2/prototype/index'
            if not (index/'vectors.faiss').exists():st.error('Index missing. Run: python Task2/prototype/rag_prototype.py --rebuild')
            else:
                with st.spinner('Retrieving evidence and generating a cited answer...'):
                    response=RAG(index).answer(question)
                st.write(response['answer']);st.caption(f"Status: {response['status']}")
                for source in response['sources']:
                    with st.expander(f"{source['document']}, page {source['page']}"):
                        st.write(source['text'])
    with pages[6]:
        st.markdown((TASK/'README.md').read_text(encoding='utf-8'))
        st.markdown('### RAG design')
        st.markdown((ROOT/'Task2/notes.md').read_text(encoding='utf-8'))

if __name__=='__main__':main()
