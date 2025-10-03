# Quick Start Guide - Dataset Sourcing

## 🚀 Getting Started in 5 Minutes

This guide will help you quickly download and organize datasets for the drowning detection system.

---

## Step 1: Install Dependencies

```bash
cd /app/datasets/scripts
pip install -r requirements.txt
```

---

## Step 2: Get Roboflow API Key

1. Go to https://roboflow.com and sign up (free account)
2. Navigate to **Settings → Roboflow API**
3. Copy your API key
4. Create `.env` file:

```bash
cd /app/datasets/scripts
cp .env.example .env
# Edit .env and add your API key
echo "ROBOFLOW_API_KEY=your_actual_api_key_here" > .env
```

---

## Step 3: Download Datasets

```bash
# Download all 4 Roboflow datasets
python download_roboflow.py
```

This will download:
- Maritime Swimmer Dataset
- Drowning Detection (Zidan)
- Swimming & Drowning Detection
- Drowning Prevention in Pools

**Time:** ~10-20 minutes depending on your internet speed

---

## Step 4: Organize Dataset

```bash
# Organize into train/val/test splits (70/15/15)
python organize_dataset.py
```

This will:
- Merge all downloaded datasets
- Remove duplicates
- Split into train/validation/test sets
- Organize by class (swimming/drowning)

**Time:** ~5-10 minutes

---

## Step 5: Verify Dataset

```bash
# Check dataset quality
python verify_dataset.py
```

This will:
- Check for corrupted images
- Verify annotations
- Identify duplicates
- Generate quality report

---

## Step 6: View Statistics

```bash
# See dataset statistics
python dataset_stats.py
```

This shows:
- Total images per split
- Class distribution
- Image properties
- Recommendations

---

## 📊 Expected Results

After completion, you should have:

```
datasets/
├── train/
│   ├── swimming/    (~1400+ images)
│   └── drowning/    (~1400+ images)
├── val/
│   ├── swimming/    (~300+ images)
│   └── drowning/    (~300+ images)
├── test/
│   ├── swimming/    (~300+ images)
│   └── drowning/    (~300+ images)
└── raw/             (downloaded datasets)
```

**Total:** 4000+ images ready for training!

---

## 🔧 Troubleshooting

### Issue: "Roboflow API key not found"
**Solution:** Make sure you created `.env` file with your API key

### Issue: "No images found after organizing"
**Solution:** Check that datasets downloaded successfully in `/app/datasets/raw/`

### Issue: "Import error for packages"
**Solution:** Run `pip install -r requirements.txt` again

### Issue: "Permission denied"
**Solution:** Make scripts executable: `chmod +x *.py`

---

## 📝 Additional Resources

- **Full Documentation:** See `/app/datasets/README.md`
- **Dataset Sources:** Listed in README.md
- **Manual Collection:** Use `download_youtube.py` for additional videos

---

## ✅ Next Steps

Once you have the dataset organized:

1. ✅ Dataset is ready for Phase 2: Model Training
2. Proceed to train YOLO detection model
3. Train action classification model
4. Integrate models into the application

---

## 📞 Need Help?

If you encounter any issues:
1. Check the troubleshooting section above
2. Review error messages carefully
3. Ensure all dependencies are installed
4. Verify Roboflow API key is correct

---

**Estimated Total Time:** 30-45 minutes

**Next Phase:** Model Training (Phase 2)
