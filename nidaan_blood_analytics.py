import sys
sys.stdout.reconfigure(encoding='utf-8')

import os, json, warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyArrowPatch
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.figure_factory as ff
from sklearn.ensemble import IsolationForest
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from scipy import stats
import networkx as nx

warnings.filterwarnings('ignore')
matplotlib.rcParams.update({
    'font.family': 'DejaVu Sans',
    'figure.facecolor': '#0f1117',
    'axes.facecolor': '#1a1d2e',
    'axes.edgecolor': '#2d3250',
    'axes.labelcolor': '#e0e0e0',
    'text.color': '#e0e0e0',
    'xtick.color': '#a0a0b0',
    'ytick.color': '#a0a0b0',
    'grid.color': '#2d3250',
    'figure.dpi': 120
})

NIDAAN_COLORS = {
    'primary':   '#7c6af7',
    'teal':      '#00d2c6',
    'coral':     '#ff6b6b',
    'amber':     '#ffd166',
    'green':     '#06d6a0',
    'pink':      '#ef476f',
    'bg':        '#0f1117',
    'card':      '#1a1d2e',
    'border':    '#2d3250',
    'text':      '#e0e0e0',
    'muted':     '#8888aa'
}

print('Imports complete')

# ============================================================
# GENERATE DATASET
# ============================================================
print('Generating synthetic blood test dataset (2000 patients)...')

np.random.seed(42)
n = 2000
diseases = np.random.choice(
    ['Healthy', 'Liver Disease', 'Diabetes', 'Anemia', 'Kidney Disease', 'Vitamin Deficiency'],
    size=n, p=[0.35, 0.15, 0.20, 0.10, 0.10, 0.10]
)

def make_col(healthy_mean, healthy_std, disease_map, disease_arr):
    base = np.random.normal(healthy_mean, healthy_std, n)
    for dis, (shift, scale) in disease_map.items():
        mask = disease_arr == dis
        base[mask] = np.random.normal(healthy_mean + shift, healthy_std * scale, mask.sum())
    return np.clip(base, 0, None)

df = pd.DataFrame({
    'PatientID': [f'P{str(i).zfill(4)}' for i in range(n)],
    'Age':       np.random.randint(18, 80, n),
    'Gender':    np.random.choice(['Male', 'Female'], n),
    'Disease':   diseases,
    'ALT':       make_col(25, 8,  {'Liver Disease': (60, 3.5), 'Diabetes': (15, 1.5)}, diseases),
    'AST':       make_col(22, 7,  {'Liver Disease': (55, 3.0), 'Diabetes': (10, 1.4)}, diseases),
    'ALP':       make_col(80, 20, {'Liver Disease': (90, 2.0), 'Anemia': (30, 1.3)},   diseases),
    'GGT':       make_col(30, 10, {'Liver Disease': (80, 3.0), 'Diabetes': (20, 1.5)}, diseases),
    'Bilirubin': make_col(0.8, 0.3, {'Liver Disease': (2.5, 3.0), 'Anemia': (1.2, 2.0)}, diseases),
    'Creatinine': make_col(0.9, 0.2, {'Kidney Disease': (2.0, 2.5)}, diseases),
    'BUN':        make_col(15,  4,   {'Kidney Disease': (30, 2.5)},  diseases),
    'UricAcid':   make_col(5.5, 1.2, {'Kidney Disease': (3.0, 1.8), 'Diabetes': (1.5, 1.3)}, diseases),
    'Hemoglobin': make_col(13.5, 1.5, {'Anemia': (-4.5, 1.8), 'Kidney Disease': (-2.0, 1.5)}, diseases),
    'WBC':        make_col(7.0, 1.5,  {'Liver Disease': (3.0, 1.5), 'Anemia': (-1.5, 1.2)},  diseases),
    'Platelets':  make_col(250, 55,   {'Liver Disease': (-80, 1.5), 'Anemia': (-50, 1.3)},    diseases),
    'RBC':        make_col(4.8, 0.5,  {'Anemia': (-1.5, 1.4)},    diseases),
    'MCV':        make_col(90, 7,     {'Anemia': (12, 1.5), 'Vitamin Deficiency': (15, 1.4)}, diseases),
    'VitaminD':   make_col(35, 12, {'Vitamin Deficiency': (-22, 1.5), 'Kidney Disease': (-15, 1.4)}, diseases),
    'VitaminB12': make_col(400, 100, {'Vitamin Deficiency': (-250, 1.5), 'Anemia': (-180, 1.4)}, diseases),
    'Ferritin':   make_col(80, 30, {'Anemia': (-55, 1.5), 'Liver Disease': (80, 2.0)}, diseases),
    'Folate':     make_col(12, 3,  {'Vitamin Deficiency': (-7, 1.5), 'Anemia': (-4, 1.3)}, diseases),
    'Glucose':    make_col(90, 12, {'Diabetes': (60, 2.5), 'Liver Disease': (20, 1.5)}, diseases),
    'HbA1c':      make_col(5.2, 0.4, {'Diabetes': (2.8, 2.0)}, diseases),
    'Cholesterol':make_col(185, 30, {'Diabetes': (40, 1.5), 'Kidney Disease': (50, 1.6)}, diseases),
    'Triglycerides': make_col(130, 35, {'Diabetes': (80, 2.0), 'Kidney Disease': (60, 1.8)}, diseases),
})

visits = []
for pid in df['PatientID'].sample(50, random_state=42):
    base_row = df[df['PatientID'] == pid].iloc[0]
    for visit in range(1, 4):
        row = base_row.copy()
        row['Visit'] = visit
        row['Date']  = pd.Timestamp('2024-01-01') + pd.DateOffset(months=(visit - 1) * 3)
        for col in ['ALT', 'AST', 'Glucose', 'Hemoglobin', 'Creatinine', 'VitaminD']:
            row[col] = max(0, row[col] + np.random.normal(0, row[col] * 0.08))
        visits.append(row)
longitudinal = pd.DataFrame(visits)

print(f'Dataset ready: {df.shape[0]} patients x {df.shape[1]} features')

BIOMARKERS = {
    'Liver Enzymes': ['ALT', 'AST', 'ALP', 'GGT', 'Bilirubin'],
    'Kidney':        ['Creatinine', 'BUN', 'UricAcid'],
    'Blood Count':   ['Hemoglobin', 'WBC', 'Platelets', 'RBC', 'MCV'],
    'Vitamins':      ['VitaminD', 'VitaminB12', 'Ferritin', 'Folate'],
    'Metabolic':     ['Glucose', 'HbA1c', 'Cholesterol', 'Triglycerides']
}
ALL_MARKERS = [m for group in BIOMARKERS.values() for m in group]

REFERENCE_RANGES = {
    'ALT':          (0,  7,   56,  200),
    'AST':          (0,  10,  40,  200),
    'ALP':          (0,  44,  147, 400),
    'GGT':          (0,  9,   48,  200),
    'Bilirubin':    (0,  0.2, 1.2, 5),
    'Creatinine':   (0,  0.6, 1.2, 5),
    'BUN':          (0,  7,   25,  60),
    'UricAcid':     (0,  2.4, 7.0, 12),
    'Hemoglobin':   (0,  12,  17,  22),
    'WBC':          (0,  4.5, 11,  20),
    'Platelets':    (0,  150, 400, 600),
    'RBC':          (0,  4.2, 5.9, 8),
    'MCV':          (0,  80,  100, 130),
    'VitaminD':     (0,  20,  50,  100),
    'VitaminB12':   (0,  200, 900, 1500),
    'Ferritin':     (0,  20,  200, 500),
    'Folate':       (0,  4,   20,  40),
    'Glucose':      (0,  70,  100, 300),
    'HbA1c':        (0,  4,   5.7, 15),
    'Cholesterol':  (0,  100, 200, 350),
    'Triglycerides':(0,  50,  150, 500),
}

os.makedirs('nidaan_outputs', exist_ok=True)
print('Output folder: ./nidaan_outputs')


# ============================================================
# VIZ 1 - Organ Panel Summary
# ============================================================
print('\n[Viz 1/12] Organ Panel Summary...')

def get_status(val, marker):
    lo, nlo, nhi, hi = REFERENCE_RANGES[marker]
    if nlo <= val <= nhi:  return 'Normal',    NIDAAN_COLORS['green']
    if val < nlo:          return 'Low',       NIDAAN_COLORS['teal']
    if val <= nhi * 1.3:   return 'Borderline',NIDAAN_COLORS['amber']
    return 'High', NIDAAN_COLORS['coral']

patient = df[df['Disease'] == 'Liver Disease'].iloc[0]

fig, axes = plt.subplots(1, 5, figsize=(22, 5))
fig.patch.set_facecolor(NIDAAN_COLORS['bg'])
fig.suptitle(f"Nidaan - Organ Panel Summary  |  Patient: {patient['PatientID']}  |  {patient['Disease']}",
             color=NIDAAN_COLORS['text'], fontsize=13, fontweight='bold', y=1.02)

for ax, (group, markers) in zip(axes, BIOMARKERS.items()):
    ax.set_facecolor(NIDAAN_COLORS['card'])
    for spine in ax.spines.values():
        spine.set_edgecolor(NIDAAN_COLORS['border'])

    group_colors = {
        'Liver Enzymes': NIDAAN_COLORS['amber'],
        'Kidney':        NIDAAN_COLORS['teal'],
        'Blood Count':   NIDAAN_COLORS['coral'],
        'Vitamins':      NIDAAN_COLORS['green'],
        'Metabolic':     NIDAAN_COLORS['primary'],
    }
    header_color = group_colors[group]

    ax.set_xlim(0, 1)
    ax.set_ylim(0, len(markers) + 1.5)
    ax.axis('off')

    ax.text(0.5, len(markers) + 1.1, group, ha='center', va='center',
            fontsize=11, fontweight='bold', color=header_color)
    ax.axhline(y=len(markers) + 0.75, color=header_color, linewidth=1.5, alpha=0.5)

    for i, marker in enumerate(reversed(markers)):
        val = patient.get(marker, np.nan)
        if pd.isna(val):
            continue
        status, color = get_status(val, marker)
        y = i + 0.5

        _, _, nhi, hi = REFERENCE_RANGES[marker]
        pct = min(val / hi, 1.0)
        ax.barh(y, pct * 0.55, left=0.42, height=0.35, color=color, alpha=0.25)
        ax.barh(y, min(pct, nhi/hi) * 0.55, left=0.42, height=0.35, color=color, alpha=0.5)

        ax.text(0.02, y, marker,  color=NIDAAN_COLORS['text'],   fontsize=8.5, va='center')
        ax.text(0.40, y, f'{val:.1f}', color=color, fontsize=8.5, va='center', ha='right', fontweight='bold')
        ax.text(0.99, y, status, color=color, fontsize=7.5, va='center', ha='right')

plt.tight_layout()
plt.savefig('nidaan_outputs/01_organ_panel_summary.png', dpi=150,
            bbox_inches='tight', facecolor=NIDAAN_COLORS['bg'])
plt.close()
print('  Saved -> nidaan_outputs/01_organ_panel_summary.png')


# ============================================================
# VIZ 2 - Reference Range Bars
# ============================================================
print('[Viz 2/12] Reference Range Bars...')

patient = df[df['Disease'] == 'Diabetes'].iloc[2]
markers_to_show = ['ALT', 'AST', 'Glucose', 'HbA1c', 'Creatinine',
                   'Cholesterol', 'Triglycerides', 'VitaminD', 'Hemoglobin']

fig, axes = plt.subplots(len(markers_to_show), 1, figsize=(12, 11))
fig.patch.set_facecolor(NIDAAN_COLORS['bg'])
fig.suptitle(f"Reference Range - Patient {patient['PatientID']} ({patient['Disease']})",
             color=NIDAAN_COLORS['text'], fontsize=13, fontweight='bold')

for ax, marker in zip(axes, markers_to_show):
    ax.set_facecolor(NIDAAN_COLORS['bg'])
    for s in ax.spines.values(): s.set_visible(False)
    ax.set_yticks([])

    lo, nlo, nhi, hi = REFERENCE_RANGES[marker]
    val = patient.get(marker, np.nan)
    if pd.isna(val): continue

    ax.barh(0, nlo,       left=lo,  height=0.6, color=NIDAAN_COLORS['teal'],  alpha=0.35)
    ax.barh(0, nhi - nlo, left=nlo, height=0.6, color=NIDAAN_COLORS['green'], alpha=0.35)
    ax.barh(0, hi  - nhi, left=nhi, height=0.6, color=NIDAAN_COLORS['coral'], alpha=0.35)

    _, color = get_status(val, marker)
    ax.axvline(val, color=color, linewidth=2.5, zorder=5)
    ax.scatter([val], [0], color=color, s=80, zorder=6)

    ax.text(-hi * 0.02, 0, marker,  color=NIDAAN_COLORS['text'],  fontsize=9,
            ha='right', va='center', fontweight='bold')
    ax.text(val, 0.42, f'{val:.1f}', color=color, fontsize=8,
            ha='center', va='bottom', fontweight='bold')
    ax.set_xlim(lo, hi)
    ax.set_xticks([nlo, nhi])
    ax.set_xticklabels([f'Low\n{nlo}', f'High\n{nhi}'], fontsize=7,
                       color=NIDAAN_COLORS['muted'])
    ax.tick_params(axis='x', length=0)

legend_patches = [
    mpatches.Patch(color=NIDAAN_COLORS['teal'],  alpha=0.6, label='Low'),
    mpatches.Patch(color=NIDAAN_COLORS['green'], alpha=0.6, label='Normal'),
    mpatches.Patch(color=NIDAAN_COLORS['coral'], alpha=0.6, label='High'),
]
fig.legend(handles=legend_patches, loc='upper right', framealpha=0,
           labelcolor=NIDAAN_COLORS['text'], fontsize=9)

plt.tight_layout()
plt.savefig('nidaan_outputs/02_reference_range_bars.png', dpi=150,
            bbox_inches='tight', facecolor=NIDAAN_COLORS['bg'])
plt.close()
print('  Saved -> nidaan_outputs/02_reference_range_bars.png')


# ============================================================
# VIZ 3 - Correlation Heatmap
# ============================================================
print('[Viz 3/12] Correlation Heatmap...')

corr = df[ALL_MARKERS].corr()

fig, ax = plt.subplots(figsize=(14, 11))
fig.patch.set_facecolor(NIDAAN_COLORS['bg'])
ax.set_facecolor(NIDAAN_COLORS['card'])

cmap = sns.diverging_palette(240, 10, s=80, l=45, as_cmap=True)
mask = np.triu(np.ones_like(corr, dtype=bool))

sns.heatmap(
    corr, mask=mask, cmap=cmap,
    vmin=-1, vmax=1, center=0,
    annot=True, fmt='.2f', annot_kws={'size': 7, 'color': 'white'},
    linewidths=0.4, linecolor=NIDAAN_COLORS['bg'],
    cbar_kws={'shrink': 0.7, 'label': 'Pearson r'},
    ax=ax
)

group_sizes = [len(v) for v in BIOMARKERS.values()]
cumulative = np.cumsum(group_sizes)
for c in cumulative[:-1]:
    ax.axhline(c, color=NIDAAN_COLORS['primary'], linewidth=1.5, alpha=0.7)
    ax.axvline(c, color=NIDAAN_COLORS['primary'], linewidth=1.5, alpha=0.7)

ax.set_title('Biomarker Correlation Heatmap - Nidaan',
             color=NIDAAN_COLORS['text'], fontsize=13, fontweight='bold', pad=15)
ax.tick_params(colors=NIDAAN_COLORS['muted'], labelsize=8)

prev = 0
group_colors_list = [NIDAAN_COLORS['amber'], NIDAAN_COLORS['teal'],
                     NIDAAN_COLORS['coral'], NIDAAN_COLORS['green'], NIDAAN_COLORS['primary']]
for (grp, markers), color, size in zip(BIOMARKERS.items(), group_colors_list, group_sizes):
    mid = prev + size / 2
    ax.text(-0.8, mid, grp, color=color, fontsize=8, fontweight='bold',
            ha='right', va='center', transform=ax.get_yaxis_transform())
    prev += size

plt.tight_layout()
plt.savefig('nidaan_outputs/03_correlation_heatmap.png', dpi=150,
            bbox_inches='tight', facecolor=NIDAAN_COLORS['bg'])
plt.close()
print('  Saved -> nidaan_outputs/03_correlation_heatmap.png')


# ============================================================
# VIZ 4 - Distribution Plots (Violin + KDE)
# ============================================================
print('[Viz 4/12] Distribution Plots...')

key_markers = ['ALT', 'Glucose', 'Hemoglobin', 'VitaminD', 'Creatinine', 'Cholesterol']
pal = {'Healthy': NIDAAN_COLORS['green'],
       'Liver Disease': NIDAAN_COLORS['amber'],
       'Diabetes': NIDAAN_COLORS['coral'],
       'Anemia': NIDAAN_COLORS['teal'],
       'Kidney Disease': NIDAAN_COLORS['primary'],
       'Vitamin Deficiency': NIDAAN_COLORS['pink']}

fig, axes = plt.subplots(2, 3, figsize=(18, 10))
fig.patch.set_facecolor(NIDAAN_COLORS['bg'])
fig.suptitle('Biomarker Distributions by Disease - Nidaan',
             color=NIDAAN_COLORS['text'], fontsize=13, fontweight='bold')

for ax, marker in zip(axes.flat, key_markers):
    ax.set_facecolor(NIDAAN_COLORS['card'])
    for s in ax.spines.values(): s.set_edgecolor(NIDAAN_COLORS['border'])

    sns.violinplot(
        data=df, x='Disease', y=marker,
        palette=pal, inner='quartile',
        linewidth=0.8, ax=ax
    )

    _, nlo, nhi, _ = REFERENCE_RANGES[marker]
    ax.axhspan(nlo, nhi, alpha=0.08, color=NIDAAN_COLORS['green'], zorder=0)
    ax.axhline(nhi, color=NIDAAN_COLORS['coral'], linewidth=0.8, linestyle='--', alpha=0.6)
    ax.axhline(nlo, color=NIDAAN_COLORS['teal'],  linewidth=0.8, linestyle='--', alpha=0.6)

    ax.set_title(marker, color=NIDAAN_COLORS['text'], fontsize=11, fontweight='bold')
    ax.set_xlabel('')
    ax.set_ylabel('', fontsize=8)
    ax.tick_params(colors=NIDAAN_COLORS['muted'], labelsize=7)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=25, ha='right')

plt.tight_layout()
plt.savefig('nidaan_outputs/04_distribution_plots.png', dpi=150,
            bbox_inches='tight', facecolor=NIDAAN_COLORS['bg'])
plt.close()
print('  Saved -> nidaan_outputs/04_distribution_plots.png')


# ============================================================
# VIZ 5 - Patient Radar Chart
# ============================================================
print('[Viz 5/12] Patient Radar Chart...')

radar_markers = ['ALT', 'AST', 'Creatinine', 'Hemoglobin',
                 'Glucose', 'Cholesterol', 'VitaminD', 'Platelets']

def normalize_for_radar(val, marker):
    _, nlo, nhi, hi = REFERENCE_RANGES[marker]
    mid = (nlo + nhi) / 2
    return min(abs(val - mid) / (hi - mid) * 100, 100)

patients_to_compare = [
    df[df['Disease'] == 'Healthy'].iloc[0],
    df[df['Disease'] == 'Liver Disease'].iloc[0],
    df[df['Disease'] == 'Diabetes'].iloc[0],
]
colors_radar = [NIDAAN_COLORS['green'], NIDAAN_COLORS['amber'], NIDAAN_COLORS['coral']]

fig = go.Figure()
for patient, color in zip(patients_to_compare, colors_radar):
    values = [normalize_for_radar(patient[m], m) for m in radar_markers]
    values += [values[0]]
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=radar_markers + [radar_markers[0]],
        fill='toself', fillcolor=color,
        opacity=0.25, line=dict(color=color, width=2),
        name=f"{patient['PatientID']} ({patient['Disease']})"
    ))

fig.update_layout(
    polar=dict(
        bgcolor=NIDAAN_COLORS['card'],
        radialaxis=dict(
            visible=True, range=[0, 100],
            tickfont=dict(color=NIDAAN_COLORS['muted'], size=9),
            gridcolor=NIDAAN_COLORS['border'], linecolor=NIDAAN_COLORS['border']
        ),
        angularaxis=dict(
            tickfont=dict(color=NIDAAN_COLORS['text'], size=10),
            gridcolor=NIDAAN_COLORS['border'], linecolor=NIDAAN_COLORS['border']
        )
    ),
    paper_bgcolor=NIDAAN_COLORS['bg'],
    plot_bgcolor=NIDAAN_COLORS['bg'],
    title=dict(text='Patient Comparison Radar - Nidaan<br><sup>Higher = more abnormal</sup>',
               font=dict(color=NIDAAN_COLORS['text'], size=14), x=0.5),
    legend=dict(font=dict(color=NIDAAN_COLORS['text']), bgcolor=NIDAAN_COLORS['card'],
                bordercolor=NIDAAN_COLORS['border']),
    height=550
)
fig.write_image('nidaan_outputs/05_radar_chart.png', scale=2)
print('  Saved -> nidaan_outputs/05_radar_chart.png')


# ============================================================
# VIZ 6 - Trend Lines Over Time
# ============================================================
print('[Viz 6/12] Trend Lines Over Time...')

trend_markers = ['ALT', 'Glucose', 'Hemoglobin', 'VitaminD', 'Creatinine', 'HbA1c']
sample_pids   = longitudinal['PatientID'].unique()[:6]

fig, axes = plt.subplots(2, 3, figsize=(18, 9))
fig.patch.set_facecolor(NIDAAN_COLORS['bg'])
fig.suptitle('Longitudinal Biomarker Trends (3 Visits) - Nidaan',
             color=NIDAAN_COLORS['text'], fontsize=13, fontweight='bold')

trend_colors = [NIDAAN_COLORS['primary'], NIDAAN_COLORS['teal'],
                NIDAAN_COLORS['coral'], NIDAAN_COLORS['amber'],
                NIDAAN_COLORS['green'], NIDAAN_COLORS['pink']]

for ax, marker in zip(axes.flat, trend_markers):
    ax.set_facecolor(NIDAAN_COLORS['card'])
    for s in ax.spines.values(): s.set_edgecolor(NIDAAN_COLORS['border'])

    _, nlo, nhi, _ = REFERENCE_RANGES[marker]
    ax.axhspan(nlo, nhi, alpha=0.10, color=NIDAAN_COLORS['green'], zorder=0, label='Normal range')
    ax.axhline(nhi, color=NIDAAN_COLORS['coral'], linewidth=0.7, linestyle='--', alpha=0.5)
    ax.axhline(nlo, color=NIDAAN_COLORS['teal'],  linewidth=0.7, linestyle='--', alpha=0.5)

    for pid, color in zip(sample_pids, trend_colors):
        pdata = longitudinal[longitudinal['PatientID'] == pid].sort_values('Visit')
        if marker not in pdata.columns: continue
        ax.plot(pdata['Visit'], pdata[marker], marker='o', color=color,
                linewidth=2, markersize=5, alpha=0.85, label=pid)
        for _, row in pdata.iterrows():
            if row[marker] > nhi or row[marker] < nlo:
                ax.scatter(row['Visit'], row[marker], s=100, color=NIDAAN_COLORS['coral'],
                           zorder=5, edgecolors='white', linewidth=0.8)

    ax.set_title(marker, color=NIDAAN_COLORS['text'], fontsize=11, fontweight='bold')
    ax.set_xlabel('Visit', color=NIDAAN_COLORS['muted'], fontsize=8)
    ax.set_xticks([1, 2, 3])
    ax.set_xticklabels(['Visit 1', 'Visit 2', 'Visit 3'], fontsize=8, color=NIDAAN_COLORS['muted'])
    ax.tick_params(colors=NIDAAN_COLORS['muted'])

plt.tight_layout()
plt.savefig('nidaan_outputs/06_trend_lines.png', dpi=150,
            bbox_inches='tight', facecolor=NIDAAN_COLORS['bg'])
plt.close()
print('  Saved -> nidaan_outputs/06_trend_lines.png')


# ============================================================
# VIZ 7 - Anomaly Detection (Isolation Forest)
# ============================================================
print('[Viz 7/12] Anomaly Detection...')

scaler = StandardScaler()
X = scaler.fit_transform(df[ALL_MARKERS].fillna(df[ALL_MARKERS].median()))

iso = IsolationForest(contamination=0.08, random_state=42, n_jobs=-1)
df['anomaly']       = iso.fit_predict(X)
df['anomaly_score'] = iso.score_samples(X)
df['is_anomaly']    = df['anomaly'] == -1

pca_2d = PCA(n_components=2, random_state=42)
X_2d   = pca_2d.fit_transform(X)
df['PC1'] = X_2d[:, 0]
df['PC2'] = X_2d[:, 1]

fig, axes = plt.subplots(1, 2, figsize=(16, 6))
fig.patch.set_facecolor(NIDAAN_COLORS['bg'])
fig.suptitle('Anomaly Detection - Isolation Forest | Nidaan',
             color=NIDAAN_COLORS['text'], fontsize=13, fontweight='bold')

ax = axes[0]
ax.set_facecolor(NIDAAN_COLORS['card'])
for s in ax.spines.values(): s.set_edgecolor(NIDAAN_COLORS['border'])

normal   = df[~df['is_anomaly']]
anomalies = df[df['is_anomaly']]
ax.scatter(normal['PC1'],   normal['PC2'],   c=NIDAAN_COLORS['teal'],  alpha=0.35, s=12, label='Normal')
ax.scatter(anomalies['PC1'], anomalies['PC2'], c=NIDAAN_COLORS['coral'], alpha=0.85, s=35,
           marker='X', label=f'Anomaly ({len(anomalies)})', zorder=5)
ax.set_title('PCA - Anomaly Scatter', color=NIDAAN_COLORS['text'], fontsize=11)
ax.set_xlabel(f"PC1 ({pca_2d.explained_variance_ratio_[0]*100:.1f}%)", color=NIDAAN_COLORS['muted'], fontsize=9)
ax.set_ylabel(f"PC2 ({pca_2d.explained_variance_ratio_[1]*100:.1f}%)", color=NIDAAN_COLORS['muted'], fontsize=9)
ax.tick_params(colors=NIDAAN_COLORS['muted'])
ax.legend(facecolor=NIDAAN_COLORS['card'], labelcolor=NIDAAN_COLORS['text'], fontsize=9)

ax2 = axes[1]
ax2.set_facecolor(NIDAAN_COLORS['card'])
for s in ax2.spines.values(): s.set_edgecolor(NIDAAN_COLORS['border'])

ax2.hist(normal['anomaly_score'],    bins=40, color=NIDAAN_COLORS['teal'],  alpha=0.6, label='Normal',  density=True)
ax2.hist(anomalies['anomaly_score'], bins=20, color=NIDAAN_COLORS['coral'], alpha=0.8, label='Anomaly', density=True)
ax2.axvline(df['anomaly_score'].quantile(0.08), color=NIDAAN_COLORS['amber'],
            linestyle='--', linewidth=1.5, label='Threshold')
ax2.set_title('Anomaly Score Distribution', color=NIDAAN_COLORS['text'], fontsize=11)
ax2.set_xlabel('Isolation Forest Score', color=NIDAAN_COLORS['muted'], fontsize=9)
ax2.set_ylabel('Density', color=NIDAAN_COLORS['muted'], fontsize=9)
ax2.tick_params(colors=NIDAAN_COLORS['muted'])
ax2.legend(facecolor=NIDAAN_COLORS['card'], labelcolor=NIDAAN_COLORS['text'], fontsize=9)

plt.tight_layout()
plt.savefig('nidaan_outputs/07_anomaly_detection.png', dpi=150,
            bbox_inches='tight', facecolor=NIDAAN_COLORS['bg'])
plt.close()
print(f'  Saved -> nidaan_outputs/07_anomaly_detection.png')
print(f'  Flagged {len(anomalies)} patients ({len(anomalies)/len(df)*100:.1f}%) as anomalies')


# ============================================================
# VIZ 8 - Composite Risk Score Gauge
# ============================================================
print('[Viz 8/12] Composite Risk Score Gauge...')

def compute_risk_score(row):
    weights = {
        'ALT': 0.12, 'AST': 0.10, 'Bilirubin': 0.08,
        'Glucose': 0.12, 'HbA1c': 0.10,
        'Creatinine': 0.08,
        'Hemoglobin': 0.07,
        'Cholesterol': 0.08, 'Triglycerides': 0.07,
        'VitaminD': 0.06, 'VitaminB12': 0.05, 'Ferritin': 0.07
    }
    score = 0
    for marker, w in weights.items():
        if marker not in row or pd.isna(row[marker]):
            continue
        _, nlo, nhi, hi = REFERENCE_RANGES[marker]
        val = row[marker]
        mid = (nlo + nhi) / 2
        deviation = abs(val - mid) / max(hi - mid, 1e-9)
        score += min(deviation, 1.0) * w * 100
    return min(score, 100)

df['risk_score'] = df.apply(compute_risk_score, axis=1)

sample_patients = pd.concat([
    df[df['Disease'] == 'Healthy'].iloc[:1],
    df[df['Disease'] == 'Diabetes'].iloc[:1],
    df[df['Disease'] == 'Liver Disease'].iloc[:1],
    df[df['Disease'] == 'Anemia'].iloc[:1],
])

fig = make_subplots(
    rows=2, cols=2,
    specs=[[{'type': 'indicator'}] * 2, [{'type': 'indicator'}] * 2],
    subplot_titles=[f"{r['PatientID']} - {r['Disease']}" for _, r in sample_patients.iterrows()]
)

positions = [(1,1),(1,2),(2,1),(2,2)]
for (row_i, col_i), (_, patient) in zip(positions, sample_patients.iterrows()):
    score = patient['risk_score']
    color = (NIDAAN_COLORS['green'] if score < 25 else
             NIDAAN_COLORS['amber'] if score < 50 else
             NIDAAN_COLORS['coral'] if score < 75 else
             NIDAAN_COLORS['pink'])
    fig.add_trace(go.Indicator(
        mode='gauge+number+delta',
        value=round(score, 1),
        number={'font': {'color': color, 'size': 28}},
        delta={'reference': 25, 'increasing': {'color': NIDAAN_COLORS['coral']},
               'decreasing': {'color': NIDAAN_COLORS['green']}},
        gauge={
            'axis': {'range': [0, 100], 'tickcolor': NIDAAN_COLORS['muted'],
                     'tickfont': {'size': 9}},
            'bar': {'color': color, 'thickness': 0.25},
            'bgcolor': NIDAAN_COLORS['card'],
            'bordercolor': NIDAAN_COLORS['border'],
            'steps': [
                {'range': [0,  25], 'color': 'rgba(6,214,160,0.13)'},
                {'range': [25, 50], 'color': 'rgba(255,209,102,0.13)'},
                {'range': [50, 75], 'color': 'rgba(255,107,107,0.13)'},
                {'range': [75,100], 'color': 'rgba(239,71,111,0.19)'},
            ],
            'threshold': {'line': {'color': 'white', 'width': 2},
                          'thickness': 0.75, 'value': score}
        }
    ), row=row_i, col=col_i)

fig.update_layout(
    paper_bgcolor=NIDAAN_COLORS['bg'],
    font=dict(color=NIDAAN_COLORS['text']),
    title=dict(text='Composite Risk Score Gauge - Nidaan',
               font=dict(size=14, color=NIDAAN_COLORS['text']), x=0.5),
    height=520
)
fig.write_image('nidaan_outputs/08_risk_score_gauge.png', scale=2)
print('  Saved -> nidaan_outputs/08_risk_score_gauge.png')


# ============================================================
# VIZ 9 - PCA Clustering
# ============================================================
print('[Viz 9/12] PCA Clustering...')

disease_pal = {
    'Healthy':            NIDAAN_COLORS['green'],
    'Liver Disease':      NIDAAN_COLORS['amber'],
    'Diabetes':           NIDAAN_COLORS['coral'],
    'Anemia':             NIDAAN_COLORS['teal'],
    'Kidney Disease':     NIDAAN_COLORS['primary'],
    'Vitamin Deficiency': NIDAAN_COLORS['pink'],
}

fig = px.scatter(
    df, x='PC1', y='PC2',
    color='Disease',
    color_discrete_map=disease_pal,
    hover_data=['PatientID', 'Age', 'Gender', 'risk_score'],
    opacity=0.65,
    title='PCA Patient Clustering by Disease - Nidaan',
    labels={
        'PC1': f"PC1 ({pca_2d.explained_variance_ratio_[0]*100:.1f}% variance)",
        'PC2': f"PC2 ({pca_2d.explained_variance_ratio_[1]*100:.1f}% variance)"
    }
)
fig.update_traces(marker=dict(size=5))
fig.update_layout(
    paper_bgcolor=NIDAAN_COLORS['bg'],
    plot_bgcolor=NIDAAN_COLORS['card'],
    font=dict(color=NIDAAN_COLORS['text']),
    title=dict(x=0.5, font=dict(size=14)),
    legend=dict(bgcolor=NIDAAN_COLORS['card'], bordercolor=NIDAAN_COLORS['border']),
    xaxis=dict(gridcolor=NIDAAN_COLORS['border']),
    yaxis=dict(gridcolor=NIDAAN_COLORS['border']),
    height=520
)
fig.write_image('nidaan_outputs/09_pca_clustering.png', scale=2)
print('  Saved -> nidaan_outputs/09_pca_clustering.png')


# ============================================================
# VIZ 10 - Population Percentile Rank
# ============================================================
print('[Viz 10/12] Population Percentile Rank...')

def get_percentile(patient_val, population_vals):
    return stats.percentileofscore(population_vals, patient_val, kind='rank')

patient = df[df['Disease'] == 'Liver Disease'].iloc[1]
cohort  = df[(df['Gender'] == patient['Gender']) &
             (df['Age'].between(patient['Age'] - 10, patient['Age'] + 10))]

pct_markers = ['ALT', 'AST', 'ALP', 'Glucose', 'Hemoglobin',
               'VitaminD', 'Cholesterol', 'Creatinine']
percentiles = {m: get_percentile(patient[m], cohort[m].dropna()) for m in pct_markers}

fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor(NIDAAN_COLORS['bg'])
ax.set_facecolor(NIDAAN_COLORS['card'])
for s in ax.spines.values(): s.set_edgecolor(NIDAAN_COLORS['border'])

markers_sorted = sorted(percentiles, key=percentiles.get)
pcts = [percentiles[m] for m in markers_sorted]
bar_colors = [NIDAAN_COLORS['green'] if 20 <= p <= 80 else
              NIDAAN_COLORS['amber'] if 10 <= p <= 90 else
              NIDAAN_COLORS['coral'] for p in pcts]

bars = ax.barh(markers_sorted, pcts, color=bar_colors, alpha=0.85, height=0.55)
ax.axvline(50, color=NIDAAN_COLORS['muted'], linestyle='--', linewidth=1, alpha=0.6, label='50th percentile')
ax.axvspan(20, 80, alpha=0.07, color=NIDAAN_COLORS['green'], label='Normal range (20-80th)')

for bar, pct, marker in zip(bars, pcts, markers_sorted):
    ax.text(pct + 1.5, bar.get_y() + bar.get_height()/2,
            f'{pct:.0f}th', va='center', ha='left',
            color=NIDAAN_COLORS['text'], fontsize=9, fontweight='bold')

ax.set_xlim(0, 108)
ax.set_xlabel('Percentile rank vs age/gender-matched cohort',
              color=NIDAAN_COLORS['muted'], fontsize=9)
ax.set_title(f"Population Percentile - {patient['PatientID']} ({patient['Gender']}, {patient['Age']}y) | Nidaan",
             color=NIDAAN_COLORS['text'], fontsize=12, fontweight='bold')
ax.tick_params(colors=NIDAAN_COLORS['muted'])
ax.legend(facecolor=NIDAAN_COLORS['card'], labelcolor=NIDAAN_COLORS['text'], fontsize=9, loc='lower right')

plt.tight_layout()
plt.savefig('nidaan_outputs/10_population_percentile.png', dpi=150,
            bbox_inches='tight', facecolor=NIDAAN_COLORS['bg'])
plt.close()
print('  Saved -> nidaan_outputs/10_population_percentile.png')


# ============================================================
# VIZ 11 - What-If Simulator
# ============================================================
print('[Viz 11/12] What-If Simulator...')

sim_patient = df[df['Disease'] == 'Diabetes'].iloc[0].copy()
sim_markers = ['ALT', 'Glucose', 'HbA1c', 'Cholesterol', 'Triglycerides',
               'Creatinine', 'VitaminD', 'Hemoglobin']
scenarios = {
    'Current':           {m: sim_patient[m]          for m in sim_markers},
    'After medication':  {m: sim_patient[m] * 0.80   for m in sim_markers},
    'Diet + exercise':   {m: sim_patient[m] * 0.70   for m in sim_markers},
    'Worst case':        {m: sim_patient[m] * 1.25   for m in sim_markers},
}

def score_scenario(vals):
    row = sim_patient.copy()
    for m, v in vals.items():
        row[m] = v
    return compute_risk_score(row)

fig, axes = plt.subplots(1, 2, figsize=(16, 7))
fig.patch.set_facecolor(NIDAAN_COLORS['bg'])
fig.suptitle(f"What-If Simulator - {sim_patient['PatientID']} ({sim_patient['Disease']}) | Nidaan",
             color=NIDAAN_COLORS['text'], fontsize=13, fontweight='bold')

ax = axes[0]
ax.set_facecolor(NIDAAN_COLORS['card'])
for s in ax.spines.values(): s.set_edgecolor(NIDAAN_COLORS['border'])

x = np.arange(len(sim_markers))
width = 0.2
sc_colors = [NIDAAN_COLORS['teal'], NIDAAN_COLORS['green'],
             NIDAAN_COLORS['primary'], NIDAAN_COLORS['coral']]

for i, (scenario, vals) in enumerate(scenarios.items()):
    normed = []
    for m in sim_markers:
        _, nlo, nhi, hi = REFERENCE_RANGES[m]
        normed.append(min(vals[m] / nhi * 100, 150))
    ax.bar(x + i * width, normed, width, label=scenario, color=sc_colors[i], alpha=0.8)

ax.axhline(100, color=NIDAAN_COLORS['amber'], linewidth=1.2, linestyle='--',
           alpha=0.7, label='Upper normal')
ax.set_xticks(x + width * 1.5)
ax.set_xticklabels(sim_markers, rotation=30, ha='right', fontsize=8,
                   color=NIDAAN_COLORS['muted'])
ax.set_ylabel('% of upper normal limit', color=NIDAAN_COLORS['muted'], fontsize=9)
ax.set_title('Biomarker values per scenario', color=NIDAAN_COLORS['text'], fontsize=10)
ax.tick_params(colors=NIDAAN_COLORS['muted'])
ax.legend(facecolor=NIDAAN_COLORS['card'], labelcolor=NIDAAN_COLORS['text'], fontsize=8)

ax2 = axes[1]
ax2.set_facecolor(NIDAAN_COLORS['card'])
for s in ax2.spines.values(): s.set_edgecolor(NIDAAN_COLORS['border'])

sc_names  = list(scenarios.keys())
sc_scores = [score_scenario(v) for v in scenarios.values()]
bar_cols  = [sc_colors[i] for i in range(len(sc_names))]

bars2 = ax2.barh(sc_names, sc_scores, color=bar_cols, alpha=0.85, height=0.5)
for bar, score in zip(bars2, sc_scores):
    ax2.text(score + 0.5, bar.get_y() + bar.get_height()/2,
             f'{score:.1f}', va='center', color=NIDAAN_COLORS['text'], fontsize=10, fontweight='bold')
ax2.axvline(25, color=NIDAAN_COLORS['green'],  linestyle='--', linewidth=1, alpha=0.6)
ax2.axvline(50, color=NIDAAN_COLORS['amber'],  linestyle='--', linewidth=1, alpha=0.6)
ax2.axvline(75, color=NIDAAN_COLORS['coral'],  linestyle='--', linewidth=1, alpha=0.6)
ax2.set_xlim(0, 105)
ax2.set_xlabel('Composite Risk Score', color=NIDAAN_COLORS['muted'], fontsize=9)
ax2.set_title('Risk score per scenario', color=NIDAAN_COLORS['text'], fontsize=10)
ax2.tick_params(colors=NIDAAN_COLORS['muted'])

plt.tight_layout()
plt.savefig('nidaan_outputs/11_what_if_simulator.png', dpi=150,
            bbox_inches='tight', facecolor=NIDAAN_COLORS['bg'])
plt.close()
print('  Saved -> nidaan_outputs/11_what_if_simulator.png')


# ============================================================
# VIZ 12 - Biomarker Causal Graph (DAG)
# ============================================================
print('[Viz 12/12] Biomarker Causal Graph...')

edges = [
    ('Liver Damage',     'ALT↑',          'releases'),
    ('Liver Damage',     'AST↑',          'releases'),
    ('Liver Damage',     'Bilirubin↑',    'impairs'),
    ('ALT↑',             'Liver Disease', 'marker'),
    ('AST↑',             'Liver Disease', 'marker'),
    ('Insulin Resistance','Glucose↑',     'causes'),
    ('Insulin Resistance','Triglycerides↑','causes'),
    ('Glucose↑',          'HbA1c↑',       'reflects'),
    ('Glucose↑',          'Diabetes',      'diagnostic'),
    ('Iron Deficiency',   'Ferritin↓',    'depletes'),
    ('Iron Deficiency',   'Hemoglobin↓',  'reduces'),
    ('Hemoglobin↓',       'Anemia',        'diagnostic'),
    ('VitaminB12↓',       'MCV↑',          'causes'),
    ('MCV↑',              'Anemia',        'marker'),
    ('VitaminD↓',         'Kidney Disease','associated'),
    ('Creatinine↑',       'Kidney Disease','marker'),
    ('BUN↑',              'Kidney Disease','marker'),
    ('Cholesterol↑',      'CVD Risk',      'increases'),
    ('Triglycerides↑',    'CVD Risk',      'increases'),
]

G = nx.DiGraph()
for src, tgt, label in edges:
    G.add_edge(src, tgt, label=label)

node_colors_dag = {
    'Liver Damage':       NIDAAN_COLORS['amber'],
    'Insulin Resistance': NIDAAN_COLORS['coral'],
    'Iron Deficiency':    NIDAAN_COLORS['teal'],
    'Liver Disease':      NIDAAN_COLORS['amber'],
    'Diabetes':           NIDAAN_COLORS['coral'],
    'Anemia':             NIDAAN_COLORS['teal'],
    'Kidney Disease':     NIDAAN_COLORS['primary'],
    'CVD Risk':           NIDAAN_COLORS['pink'],
}
node_color_list = [node_colors_dag.get(n, NIDAAN_COLORS['muted']) for n in G.nodes()]

fig, ax = plt.subplots(figsize=(16, 9))
fig.patch.set_facecolor(NIDAAN_COLORS['bg'])
ax.set_facecolor(NIDAAN_COLORS['bg'])
ax.axis('off')
ax.set_title('Biomarker Causal Pathway - Nidaan',
             color=NIDAAN_COLORS['text'], fontsize=13, fontweight='bold', pad=15)

pos = nx.spring_layout(G, seed=7, k=2.2)

nx.draw_networkx_edges(
    G, pos, ax=ax,
    edge_color=NIDAAN_COLORS['muted'],
    alpha=0.55, width=1.4,
    arrows=True, arrowsize=18,
    connectionstyle='arc3,rad=0.12',
    node_size=1800
)
nx.draw_networkx_nodes(
    G, pos, ax=ax,
    node_color=node_color_list,
    node_size=1800, alpha=0.90
)
nx.draw_networkx_labels(
    G, pos, ax=ax,
    font_size=7.5, font_color=NIDAAN_COLORS['bg'],
    font_weight='bold'
)
edge_labels = nx.get_edge_attributes(G, 'label')
nx.draw_networkx_edge_labels(
    G, pos, edge_labels=edge_labels, ax=ax,
    font_size=6.5, font_color=NIDAAN_COLORS['text'],
    bbox=dict(boxstyle='round,pad=0.2', facecolor=NIDAAN_COLORS['card'], alpha=0.7)
)

legend_items = [
    mpatches.Patch(color=NIDAAN_COLORS['amber'],  label='Liver pathway'),
    mpatches.Patch(color=NIDAAN_COLORS['coral'],  label='Metabolic pathway'),
    mpatches.Patch(color=NIDAAN_COLORS['teal'],   label='Blood / anemia pathway'),
    mpatches.Patch(color=NIDAAN_COLORS['primary'],label='Kidney pathway'),
    mpatches.Patch(color=NIDAAN_COLORS['pink'],   label='CVD risk'),
    mpatches.Patch(color=NIDAAN_COLORS['muted'],  label='Biomarker node'),
]
ax.legend(handles=legend_items, loc='lower left',
          facecolor=NIDAAN_COLORS['card'], labelcolor=NIDAAN_COLORS['text'],
          fontsize=8, framealpha=0.9, edgecolor=NIDAAN_COLORS['border'])

plt.tight_layout()
plt.savefig('nidaan_outputs/12_causal_graph.png', dpi=150,
            bbox_inches='tight', facecolor=NIDAAN_COLORS['bg'])
plt.close()
print('  Saved -> nidaan_outputs/12_causal_graph.png')


# ============================================================
# ZIP OUTPUTS
# ============================================================
import zipfile, glob

png_files = sorted(glob.glob('nidaan_outputs/*.png'))
with zipfile.ZipFile('nidaan_blood_analytics_plots.zip', 'w', zipfile.ZIP_DEFLATED) as zf:
    for f in png_files:
        zf.write(f)
print(f'\nZipped {len(png_files)} plots -> nidaan_blood_analytics_plots.zip')

print('\n============================================')
print('  ALL 12 VISUALIZATIONS COMPLETE')
print('============================================')
files_list = [
    '01_organ_panel_summary',
    '02_reference_range_bars',
    '03_correlation_heatmap',
    '04_distribution_plots',
    '05_radar_chart',
    '06_trend_lines',
    '07_anomaly_detection',
    '08_risk_score_gauge',
    '09_pca_clustering',
    '10_population_percentile',
    '11_what_if_simulator',
    '12_causal_graph',
]
for f in files_list:
    print(f'  Done: {f}.png')
