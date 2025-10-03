# 🖥️ Running YOLOv8s Annotation on Your Local Machine

## 📋 Prerequisites

1. **Python 3.8+** installed
2. **At least 4GB RAM** available
3. **10GB free disk space** for dataset and annotations
4. **Internet connection** (for first-time model download)

---

## 🚀 Step-by-Step Instructions

### Step 1: Download the Annotation Script

Download `high_accuracy_annotate.py` from:
```
/app/datasets/annotations/tools/high_accuracy_annotate.py
```

Or copy the script to your local machine.

### Step 2: Install Dependencies

Open terminal/command prompt and run:

```bash
# Install required packages
pip install ultralytics opencv-python torch torchvision numpy

# Or if you have requirements.txt
pip install -r requirements.txt
```

**For Windows users:**
```cmd
pip install ultralytics opencv-python torch torchvision numpy
```

**For Mac/Linux users:**
```bash
pip3 install ultralytics opencv-python torch torchvision numpy
```

---

### Step 3: Navigate to Your Dataset Directory

```bash
# Example: If your dataset is in Documents folder
cd /path/to/your/swimming-pool-dataset

# Your directory structure should look like:
# swimming-pool-dataset/
# ├── train/
# │   ├── swimming/
# │   └── drowning/
# ├── val/
# │   ├── swimming/
# │   └── drowning/
# └── test/
#     ├── swimming/
#     └── drowning/
```

---

### Step 4: Run the Annotation Command

**🎯 MAIN COMMAND TO PROCESS ALL 9,342 IMAGES:**

```bash
python high_accuracy_annotate.py \
    --dataset /path/to/your/dataset \
    --output /path/to/output/annotations \
    --confidence 0.15 \
    --batch-size 500
```

**Replace the paths with your actual paths!**

---

## 💻 Platform-Specific Commands

### For Windows (Command Prompt):

```cmd
python high_accuracy_annotate.py --dataset C:\Users\YourName\Documents\swimming-dataset --output C:\Users\YourName\Documents\annotations --confidence 0.15 --batch-size 500
```

### For Windows (PowerShell):

```powershell
python high_accuracy_annotate.py `
    --dataset "C:\Users\YourName\Documents\swimming-dataset" `
    --output "C:\Users\YourName\Documents\annotations" `
    --confidence 0.15 `
    --batch-size 500
```

### For Mac/Linux:

```bash
python3 high_accuracy_annotate.py \
    --dataset ~/Documents/swimming-dataset \
    --output ~/Documents/annotations \
    --confidence 0.15 \
    --batch-size 500
```

---

## 🔧 If You're in the Same Directory as Dataset

If you're already in the dataset directory:

```bash
python high_accuracy_annotate.py \
    --dataset . \
    --output ./annotations \
    --confidence 0.15 \
    --batch-size 500
```

---

## 📊 Expected Output

You'll see output like:

```
🔍 Checking dependencies...
  ✅ OpenCV
  ✅ Ultralytics YOLO
  ✅ PyTorch
  ✅ NumPy

🤖 Initializing YOLOv8s Model...
   (This will download the model if not already cached)
✅ YOLOv8s model loaded successfully!

🚀 Starting High-Accuracy Annotation with YOLOv8s
📁 Dataset: /path/to/your/dataset
💾 Output: /path/to/output/annotations
🎯 Confidence Threshold: 0.15

🔍 Scanning dataset...
✅ Found 9342 images to process

📊 Progress: 500/9342 (5.4%)
   Speed: 2.1 images/sec | Est. remaining: 70.2 min

...
```

---

## ⏱️ Processing Time

- **Processing Speed:** 2-4 images/second (depends on your CPU)
- **Total Time for 9,342 images:** 60-80 minutes
- **RAM Usage:** ~2-4 GB
- **CPU Usage:** 80-100% (normal)

---

## 🎯 Quick Start (Copy-Paste Ready)

**If your dataset structure is:**
```
/home/user/datasets/
├── train/swimming/
├── train/drowning/
├── val/swimming/
├── val/drowning/
├── test/swimming/
└── test/drowning/
```

**Run this:**
```bash
cd /home/user/datasets
python high_accuracy_annotate.py \
    --dataset . \
    --output ./yolov8s_annotations \
    --confidence 0.15 \
    --batch-size 500
```

---

## 🔍 Run in Background (Optional)

### For Linux/Mac:

```bash
# Run in background and save output to log
nohup python3 high_accuracy_annotate.py \
    --dataset /path/to/dataset \
    --output /path/to/annotations \
    --confidence 0.15 \
    --batch-size 500 > annotation.log 2>&1 &

# Check progress
tail -f annotation.log

# Check if still running
ps aux | grep high_accuracy_annotate
```

### For Windows:

Run normally - the process will show progress in the terminal window.

---

## 📁 Output Location

After completion, you'll find:

```
/path/to/output/annotations/
├── train/
│   ├── swimming/
│   │   ├── swimming_train_00001.txt
│   │   ├── swimming_train_00002.txt
│   │   └── ...
│   └── drowning/
│       ├── drowning_train_00001.txt
│       └── ...
├── val/
│   ├── swimming/
│   └── drowning/
├── test/
│   ├── swimming/
│   └── drowning/
└── annotation_statistics.json  (detailed statistics)
```

---

## 🛠️ Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'ultralytics'"

**Solution:**
```bash
pip install ultralytics
```

### Issue: "CUDA not available" warning

**Solution:** This is normal! The script runs on CPU. You can ignore this warning.

### Issue: Process is slow

**Solution:** 
- Normal speed is 2-4 images/second on CPU
- Close other applications to free up CPU
- Be patient - 9,342 images will take 60-80 minutes

### Issue: "No images found"

**Solution:** Check your dataset path. Make sure structure is:
```
dataset/
├── train/{swimming,drowning}/
├── val/{swimming,drowning}/
└── test/{swimming,drowning}/
```

---

## ✅ Verification After Completion

After the script finishes, verify the results:

```bash
# Count annotation files
find /path/to/annotations -name "*.txt" | wc -l
# Should show: 9342

# View statistics
cat /path/to/annotations/annotation_statistics.json
```

---

## 🎯 Single Command Summary

**The ONE command you need:**

```bash
python high_accuracy_annotate.py --dataset /path/to/your/dataset --output /path/to/annotations --confidence 0.15 --batch-size 500
```

**Just replace `/path/to/your/dataset` and `/path/to/annotations` with your actual paths!**

---

## 💡 Tips

1. **First-time run:** Model will download (~22 MB), takes 1-2 minutes
2. **Subsequent runs:** Model is cached, starts immediately
3. **Test first:** Use `--max-images 100` to test on 100 images first
4. **Leave running:** Don't close terminal window until complete
5. **Check progress:** Progress updates every 500 images

---

## 📞 Need Help?

If you encounter issues:
1. Check that Python and pip are installed: `python --version`
2. Verify dependencies are installed: `pip list | grep ultralytics`
3. Check dataset path exists: `ls /path/to/your/dataset`
4. Ensure sufficient disk space: `df -h` (Linux/Mac) or check in File Explorer (Windows)

---

**Ready to start? Run the command above and let it process for 60-80 minutes!** ☕
