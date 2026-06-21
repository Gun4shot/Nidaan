'use client';

import { useState, useRef, useEffect } from 'react';

interface PlotData {
  name: string;
  title: string;
  filename: string;
  data: string;
}

interface Dataset {
  id: string;
  filename: string;
  size: number;
}

const API_BASE = 'http://localhost:5000';
const STATE_KEY = 'nidaan_analytics_state';

function loadState() {
  if (typeof window === 'undefined') return null;
  try {
    const raw = localStorage.getItem(STATE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch { return null; }
}

function saveState(state: { plots: PlotData[]; selectedPlot: number | null; selectedDataset: string | null }) {
  if (typeof window === 'undefined') return;
  try {
    const toSave = { ...state, plots: state.plots.map(p => ({ ...p, data: '' })) };
    localStorage.setItem(STATE_KEY, JSON.stringify(toSave));
  } catch {}
}

export default function AnalyticsTab() {
  const saved = loadState();

  const [plots, setPlots] = useState<PlotData[]>(saved?.plots || []);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedPlot, setSelectedPlot] = useState<number | null>(saved?.selectedPlot ?? null);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<string | null>(saved?.selectedDataset || null);
  const [uploading, setUploading] = useState(false);
  const [showUpload, setShowUpload] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const hasPlots = plots.length > 0 && plots.some(p => p.data);

  useEffect(() => {
    loadDatasets();
  }, []);

  useEffect(() => {
    saveState({ plots, selectedPlot, selectedDataset });
  }, [plots, selectedPlot, selectedDataset]);

  const loadDatasets = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/analytics/datasets`);
      const data = await res.json();
      if (res.ok) setDatasets(data.datasets);
    } catch {}
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const res = await fetch(`${API_BASE}/api/analytics/upload`, { method: 'POST', body: formData });
      const data = await res.json();

      if (!res.ok) {
        setError(data.error || 'Upload failed');
        return;
      }

      await loadDatasets();
      setSelectedDataset(data.dataset.id);
      setShowUpload(false);
      await runAnalysis();
    } catch (err) {
      setError('Cannot connect to analytics server.');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const runAnalysis = async () => {
    setLoading(true);
    setError('');
    setPlots([]);
    setSelectedPlot(null);

    try {
      const res = await fetch(`${API_BASE}/api/analytics/run`, { method: 'POST' });
      const data = await res.json();

      if (!res.ok) {
        setError(data.error || 'Failed to run analysis');
        return;
      }

      setPlots(data.plots);
      if (data.plots.length > 0) setSelectedPlot(0);
    } catch (err) {
      setError('Cannot connect to analytics server. Make sure the Python backend is running on port 5000.');
    } finally {
      setLoading(false);
    }
  };

  const handleLoadExisting = async (datasetId: string) => {
    setSelectedDataset(datasetId);
    await runAnalysis();
  };

  const handleDeleteDataset = async (datasetId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await fetch(`${API_BASE}/api/analytics/datasets/${datasetId}`, { method: 'DELETE' });
      await loadDatasets();
      if (selectedDataset === datasetId) {
        setSelectedDataset(null);
        setPlots([]);
        setSelectedPlot(null);
      }
    } catch {}
  };

  const handleDownload = (filename: string) => {
    window.open(`${API_BASE}/api/analytics/download/${filename}`, '_blank');
  };

  const handleDownloadAll = () => {
    window.open(`${API_BASE}/api/analytics/download-all`, '_blank');
  };

  const handleDownloadCSV = () => {
    window.open(`${API_BASE}/api/analytics/download-csv`, '_blank');
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(1)} MB`;
  };

  return (
    <div className="analytics">
      <input ref={fileInputRef} type="file" accept=".csv" className="analytics__file-input" onChange={handleUpload} />

      {!hasPlots ? (
        <div className="analytics__empty">
          <span className="material-symbols-outlined analytics__empty-icon">biotech</span>
          <p className="analytics__empty-title">Blood Analytics</p>
          <p className="analytics__empty-desc">Upload a blood test dataset (CSV) to generate visualizations, or load an existing dataset.</p>

          <div className="analytics__upload-zone" onClick={() => fileInputRef.current?.click()}>
            <span className="material-symbols-outlined analytics__upload-icon">cloud_upload</span>
            <p className="analytics__upload-text">{uploading ? 'Uploading...' : 'Drop CSV here or click to browse'}</p>
            <p className="analytics__upload-hint">Supports .csv files</p>
          </div>

          {datasets.length > 0 && (
            <div className="analytics__datasets">
              <span className="analytics__datasets-label">OR LOAD EXISTING</span>
              <div className="analytics__datasets-list">
                {datasets.map((ds) => (
                  <div key={ds.id} className={`analytics__dataset ${selectedDataset === ds.id ? 'analytics__dataset--active' : ''}`}>
                    <button className="analytics__dataset-btn" onClick={() => handleLoadExisting(ds.id)}>
                      <span className="material-symbols-outlined analytics__dataset-icon">table_chart</span>
                      <div className="analytics__dataset-info">
                        <span className="analytics__dataset-name">{ds.filename}</span>
                        <span className="analytics__dataset-size">{formatSize(ds.size)}</span>
                      </div>
                    </button>
                    {ds.id !== 'synthetic' && (
                      <button className="analytics__dataset-delete" onClick={(e) => handleDeleteDataset(ds.id, e)} title="Delete">
                        <span className="material-symbols-outlined">close</span>
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {loading && (
            <div className="analytics__loading">
              <span className="analytics__spinner" />
              <span>Running analysis...</span>
            </div>
          )}
          {error && <p className="analytics__error">{error}</p>}
        </div>
      ) : (
        <div className="analytics__results">
          <div className="analytics__sidebar">
            <div className="analytics__sidebar-header">
              <span className="analytics__sidebar-title">VISUALIZATIONS</span>
              <span className="analytics__sidebar-count">{plots.length}</span>
            </div>
            <nav className="analytics__sidebar-list custom-scrollbar">
              {plots.map((plot, i) => (
                <button
                  key={plot.name}
                  className={`analytics__sidebar-item ${selectedPlot === i ? 'analytics__sidebar-item--active' : ''}`}
                  onClick={() => setSelectedPlot(i)}
                >
                  <span className="analytics__sidebar-num">{String(i + 1).padStart(2, '0')}</span>
                  <span className="analytics__sidebar-label">{plot.title}</span>
                </button>
              ))}
            </nav>
            <div className="analytics__sidebar-footer">
              <button className="analytics__upload-new-btn" onClick={() => { setPlots([]); setSelectedPlot(null); setShowUpload(true); }}>
                <span className="material-symbols-outlined">upload_file</span>
                Upload New Dataset
              </button>
              <button className="analytics__download-all-btn" onClick={handleDownloadAll}>
                <span className="material-symbols-outlined">download</span>
                Download All (ZIP)
              </button>
              <button className="analytics__csv-btn" onClick={handleDownloadCSV}>
                <span className="material-symbols-outlined">description</span>
                Download Dataset CSV
              </button>
              <button className="analytics__rerun-btn" onClick={runAnalysis} disabled={loading}>
                <span className="material-symbols-outlined">refresh</span>
                Re-run Analysis
              </button>
            </div>
          </div>

          <div className="analytics__viewer">
            {selectedPlot !== null && plots[selectedPlot] && (
              <>
                <div className="analytics__viewer-header">
                  <div>
                    <h2 className="analytics__viewer-title">{plots[selectedPlot].title}</h2>
                    <span className="analytics__viewer-file">{plots[selectedPlot].filename}</span>
                  </div>
                  <button className="analytics__viewer-download" onClick={() => handleDownload(plots[selectedPlot].filename)}>
                    <span className="material-symbols-outlined">download</span>
                    Download PNG
                  </button>
                </div>
                <div className="analytics__viewer-canvas custom-scrollbar">
                  {plots[selectedPlot].data ? (
                    <img src={plots[selectedPlot].data} alt={plots[selectedPlot].title} className="analytics__viewer-img" />
                  ) : (
                    <div className="analytics__viewer-placeholder">
                      <span className="material-symbols-outlined">image</span>
                      <p>Re-run analysis to generate this plot</p>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
