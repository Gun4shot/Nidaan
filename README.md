# MedSuite — multi-domain medical image diagnosis (hackathon kit)

**Architecture:** 1 router model (detects image type) + 5 lightweight specialist
models (one per dataset). All MobileNetV3-Small, ~10MB each, ~60MB total.
Trains fast on Colab's free T4 GPU.

```
Upload image -> [Router] -> "this is a chest X-ray"
                                  |
                         -> [Chest specialist(s)] -> diagnosis
```

## 0. Folder structure to set up in Google Drive

Upload your 5 already-downloaded dataset folders into Drive like this
(exact sub-paths matter, they're referenced in each train_*.py):

```
MyDrive/hackathon_data/
  covid_radiography/        <- from covid19-radiography-database
  chest_xray_nih/           <- from nih-chest-xrays/sample
  brain_tumor_mri/          <- from brain-tumor-mri-dataset
  malaria/cell_images/      <- from cell-images-for-detecting-malaria
  bone_fracture/            <- from fracture-multi-region-x-ray-data
  weights/                  <- (empty, gets filled with .pth files as you train)
```

If Kaggle's zip extracts to slightly different folder/file names, just
rename folders to match, or edit the path constants at the top of each
`train_*.py` (they're all clearly marked `# ---- EDIT THESE PATHS ----`).

## 1. Colab setup (run once at the top of your notebook)

```python
from google.colab import drive
drive.mount('/content/drive')

!pip install -q torch torchvision pandas pillow

# upload all the .py files from this kit into the Colab file browser
# (or git clone / drive-mount them), so train_*.py and model_utils.py
# are all in the Colab working directory.
```

## 2. Train the 5 specialists (run each as a cell, ~5-20 min each on T4)

```python
!python train_chest_covid.py
!python train_chest_nih.py
!python train_brain_mri.py
!python train_malaria.py
!python train_fracture.py
```

Each one prints per-epoch train/val accuracy and saves the **best** epoch's
weights to `MyDrive/hackathon_data/weights/<name>.pth`.

## 3. Build + train the router (the "auto-detect" magic)

```python
!python build_router_dataset.py   # samples images from all 5 datasets
!python train_router.py
```

This gives you `weights/router.pth` — a 4-way classifier:
`chest_xray / brain_mri / blood_cell / bone_xray`.

## 4. Sanity check the full pipeline in Colab

```python
import os
os.environ["MEDSUITE_WEIGHTS_DIR"] = "/content/drive/MyDrive/hackathon_data/weights"
from inference import diagnose
print(diagnose("/path/to/any/test/image.png"))
```

You should get back something like:
```json
{
  "detected_modality": "chest_xray",
  "modality_confidence": 0.97,
  "diagnosis": {
    "covid_screen": [{"label": "COVID", "confidence": 0.88}, ...],
    "finding_screen": [{"label": "Infiltration", "confidence": 0.61}, ...]
  }
}
```

## 5. Hand off to your friend (GPU laptop) for the live demo

You only need to send **6 small files**, not the datasets:
```
weights/router.pth
weights/chest_covid.pth
weights/chest_nih.pth
weights/brain_mri.pth
weights/malaria.pth
weights/fracture.pth
```
Plus the code files: `model_utils.py`, `inference.py`, `serve_api.py`, `requirements.txt`.

On the friend's laptop:
```bash
pip install -r requirements.txt
export MEDSUITE_WEIGHTS_DIR=./weights      # Windows: set MEDSUITE_WEIGHTS_DIR=./weights
uvicorn serve_api:app --host 0.0.0.0 --port 8000
```

## 6. Connect the frontend

POST an image file to `http://<friend-laptop-ip>:8000/predict` as
`multipart/form-data` with field name `file`. Returns the JSON shown above.

Quick test without any frontend:
```bash
curl -F "file=@test_xray.png" http://localhost:8000/predict
```

## Notes / things to tune if you have spare time before the demo

- **Class imbalance**: malaria and NIH chest datasets are imbalanced. If
  accuracy looks suspicious (e.g. always predicting the majority class),
  add `class_weight` to `CrossEntropyLoss`/`BCEWithLogitsLoss` in
  `model_utils.py` / `multilabel_utils.py`.
- **Epochs**: defaults (6-8) are tuned for hackathon time budgets. Bump
  `EPOCHS` in any train script if you have GPU time to spare and accuracy
  is still climbing.
- **Router accuracy matters most for the demo** — if it misroutes, the
  whole "auto-detect" experience breaks. Eyeball its val_acc in the
  training logs; it should be near-perfect (>98%) since the 4 modalities
  look extremely different visually.
- These are screening-tool demos, not real diagnostic tools — worth
  saying explicitly during your hackathon pitch (judges like that
  framing, and it's true).
