# Machine data analysis

From the repository root, run `python Task1/task1_analysis.py --data data.xlsx`.
Install the root requirements first. The run produces all CSVs and plots locally.
Run `python -m Task1.enrich_report` afterward to reproduce the detailed before/during anomaly comparisons and readable state names in the submitted report.

## Methods and interpretation

The actual data covers 2017-01-01 through 2020-08-07. Timestamps are sorted and checked against a strict five-minute grid. Duplicate timestamps, if present, are consolidated by median. Error strings become missing observations and are counted in `data_quality.json`. No interpolation is used: this avoids inventing downtime or forecasting targets across communication gaps. Outliers are retained for investigation rather than automatically deleted.

Shutdown is a conservative proxy: both gas temperatures below 150 and absolute inlet draft below 30 for at least 30 consecutive minutes. Thresholds use the observed separation between ambient and hot operation and require operator confirmation. Missing intervals break events. Event end timestamps are exclusive. Each sample contributes five minutes. Total inferred downtime is 5,156.42 hours in 77 events; this excludes 204.67 hours with incomplete sensor telemetry. These categories can overlap when unrelated sensors are missing, so do not sum them as mutually exclusive accounting categories.

KMeans uses complete non-shutdown observations, six sensors, temperature difference, inlet change and 30-minute rolling variation. StandardScaler fits these descriptive historical features. Candidate k=3 through 6 is selected using a fixed 5,000-point silhouette sample. Six states were selected; their numerical profiles are in `clusters_summary.csv`. These are descriptive clusters, not validated fault or efficiency labels. Short episodes indicate boundary switching and should not be interpreted as physical switching without smoothing and operator validation.

Within each state, anomalies exceed six robust standard deviations from a sensor median, using 1.4826 times MAD with a floor of one sensor unit. Consecutive flags form events. This retrospective detector fits state distributions to the history; it is not a prospective validation. The 926 events are investigation candidates, not confirmed faults. Four separated high-score examples are plotted.

Forecasting uses chronological 60/20/20 splits and 12 direct gradient-boosting regressors. Training targets cannot cross into validation; validation targets cannot cross into test. Features use only origin-time and past observations. Missing feature or target rows are excluded. Training samples are thinned to every third eligible row for runtime. Leaf count is selected on validation MAE. Test starts 2019-11-18 14:40. Models are not retrained on validation. Persistence predicts the current observed value for every horizon.

## Outputs

- `shutdown_periods.csv`: half-open start/end and duration in minutes.
- `anomalous_periods.csv`: event timing, state, implicated sensors and peak robust score.
- `clusters_summary.csv`: profiles, percentiles, frequency and episode duration.
- `forecasts.csv`: origin, target time, horizon, actual and both predictions.
- `forecast_metrics.csv`: MAE and RMSE by horizon and pooled across horizons.
- `sample_labels.csv.gz`: five-minute shutdown, state, anomaly and telemetry labels.
- `plots/`: representative week, 2018 overview, correlation and four anomaly windows.

## Findings and recommendations

1. The 77 cold low-draft events support explicit downtime reporting; validate boundaries against operator logs before using them as availability KPIs.
2. Communication gaps warrant separate telemetry alerts. Missing readings cannot establish a mechanical shutdown.
3. Six clusters and frequent short episodes show that operating context matters. Review cluster profiles with an operator before assigning semantic load or degradation labels.
4. State-relative flags identify 926 candidate events. Require persistence and maintenance evidence before turning these into operator alarms.
5. At one hour, boosting achieves MAE 10.90 and RMSE 19.48 versus persistence MAE 12.48 and RMSE 22.68. Evaluate separately around shutdown transitions before deployment. Sensor units are not explicitly documented in the supplied brief; errors are reported in native temperature units.

Run `python -m pytest -q` for deterministic core tests. Forecast origins overlap, so errors are correlated and the point metrics are not confidence intervals.
