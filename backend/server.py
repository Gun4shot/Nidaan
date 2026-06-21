import os
import sys
import json
import glob
import base64
import zipfile
import io
import uuid
import shutil

from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'nidaan_outputs')
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
SCRIPT_PATH = os.path.join(BASE_DIR, '..', 'nidaan_blood_analytics.py')

VIZ_NAMES = [
    '01_organ_panel_summary', '02_reference_range_bars', '03_correlation_heatmap',
    '04_distribution_plots', '05_radar_chart', '06_trend_lines',
    '07_anomaly_detection', '08_risk_score_gauge', '09_pca_clustering',
    '10_population_percentile', '11_what_if_simulator', '12_causal_graph',
]
VIZ_TITLES = [
    'Organ Panel Summary', 'Reference Range Bars', 'Correlation Heatmap',
    'Distribution Plots', 'Patient Radar Chart', 'Trend Lines Over Time',
    'Anomaly Detection', 'Composite Risk Score Gauge', 'PCA Clustering',
    'Population Percentile Rank', 'What-If Simulator', 'Biomarker Causal Graph',
]

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)


def load_plots_from_dir(directory):
    png_files = sorted(glob.glob(os.path.join(directory, '*.png')))
    plots = []
    for f in png_files:
        name = os.path.splitext(os.path.basename(f))[0]
        title = name
        for vn, vt in zip(VIZ_NAMES, VIZ_TITLES):
            if vn == name:
                title = vt
                break
        with open(f, 'rb') as fh:
            b64 = base64.b64encode(fh.read()).decode('utf-8')
        plots.append({
            'name': name,
            'title': title,
            'filename': os.path.basename(f),
            'data': f'data:image/png;base64,{b64}',
        })
    return plots


@app.route('/api/analytics/run', methods=['POST'])
def run_analytics():
    import subprocess
    try:
        result = subprocess.run(
            [sys.executable, SCRIPT_PATH],
            capture_output=True, text=True, timeout=120,
            cwd=os.path.join(BASE_DIR, '..'),
        )
        if result.returncode != 0:
            return jsonify({'error': result.stderr[-500:] if result.stderr else 'Script failed'}), 500

        plots = load_plots_from_dir(OUTPUT_DIR)
        return jsonify({'plots': plots, 'count': len(plots)})
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Analysis timed out'}), 504
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analytics/plots', methods=['GET'])
def list_plots():
    plots = load_plots_from_dir(OUTPUT_DIR)
    return jsonify({'plots': plots, 'count': len(plots)})


@app.route('/api/analytics/upload', methods=['POST'])
def upload_dataset():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'Only CSV files are accepted'}), 400

    dataset_id = str(uuid.uuid4())[:8]
    dataset_dir = os.path.join(UPLOAD_DIR, dataset_id)
    os.makedirs(dataset_dir, exist_ok=True)

    csv_path = os.path.join(dataset_dir, file.filename)
    file.save(csv_path)

    meta = {
        'id': dataset_id,
        'filename': file.filename,
        'size': os.path.getsize(csv_path),
    }
    with open(os.path.join(dataset_dir, 'meta.json'), 'w') as f:
        json.dump(meta, f)

    return jsonify({'dataset': meta})


@app.route('/api/analytics/datasets', methods=['GET'])
def list_datasets():
    datasets = []
    for did in sorted(os.listdir(UPLOAD_DIR)):
        meta_path = os.path.join(UPLOAD_DIR, did, 'meta.json')
        if os.path.exists(meta_path):
            with open(meta_path) as f:
                datasets.append(json.load(f))

    if os.path.exists(os.path.join(OUTPUT_DIR, 'nidaan_blood_dataset.csv')):
        datasets.insert(0, {
            'id': 'synthetic',
            'filename': 'nidaan_blood_dataset.csv',
            'size': os.path.getsize(os.path.join(OUTPUT_DIR, 'nidaan_blood_dataset.csv')),
        })

    return jsonify({'datasets': datasets})


@app.route('/api/analytics/datasets/<dataset_id>', methods=['DELETE'])
def delete_dataset(dataset_id):
    dataset_dir = os.path.join(UPLOAD_DIR, dataset_id)
    if os.path.exists(dataset_dir):
        shutil.rmtree(dataset_dir)
        return jsonify({'ok': True})
    return jsonify({'error': 'Not found'}), 404


@app.route('/api/analytics/download/<filename>', methods=['GET'])
def download_plot(filename):
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)


@app.route('/api/analytics/download-all', methods=['GET'])
def download_all():
    png_files = sorted(glob.glob(os.path.join(OUTPUT_DIR, '*.png')))
    if not png_files:
        return jsonify({'error': 'No plots generated yet'}), 404
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in png_files:
            zf.write(f, os.path.basename(f))
    buf.seek(0)
    return send_file(buf, mimetype='application/zip', as_attachment=True,
                     download_name='nidaan_blood_analytics.zip')


@app.route('/api/analytics/download-csv', methods=['GET'])
def download_csv():
    csv_path = os.path.join(OUTPUT_DIR, 'nidaan_blood_dataset.csv')
    if not os.path.exists(csv_path):
        return jsonify({'error': 'No dataset generated yet'}), 404
    return send_file(csv_path, mimetype='text/csv', as_attachment=True,
                     download_name='nidaan_blood_dataset.csv')


# ============================================================
# IMAGE CLASSIFICATION
# ============================================================

sys.path.insert(0, os.path.join(BASE_DIR, 'models'))
from classifier import classify_image, get_available_models


@app.route('/api/classify', methods=['POST'])
def classify():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    model_key = request.form.get('model', 'brain_tumor')
    if model_key not in ('brain_tumor', 'chest_xray', 'covid19', 'malaria'):
        return jsonify({'error': 'Invalid model key'}), 400

    image_file = request.files['image']
    image_bytes = image_file.read()

    try:
        result = classify_image(image_bytes, model_key)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/classify/models', methods=['GET'])
def classify_models():
    return jsonify({'models': get_available_models()})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
