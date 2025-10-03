# Pilot Batch Annotation - Quick Start Guide

## 🚀 Getting Started (5 Minutes)

### Step 1: Verify Setup
```bash
# Check if images are ready
ls /app/datasets/annotations/pilot_batch/images | wc -l
# Should show ~250 images

# Check if LabelImg is installed
python -c "import labelImg; print('✅ LabelImg ready')"
```

### Step 2: Launch LabelImg
```bash
cd /app/datasets/annotations/tools
python launch_labelimg.py
```

### Step 3: Configure LabelImg (First Time Only)
1. **Set format to YOLO:** View → Auto Save → Format: YOLO
2. **Load classes:** File → Change Save Dir → Select annotations directory
3. **Verify classes:** Should see "swimming" and "drowning"

### Step 4: Start Annotating
1. **Open first image**
2. **Press W** to create bounding box
3. **Draw box around person**
4. **Select class:** swimming (0) or drowning (1)
5. **Press Ctrl+S** to save
6. **Press D** for next image

## 🎯 Annotation Goals

### Target for Pilot Batch:
- **250 images** total
- **~175 swimming class** (normal behavior)
- **~75 drowning class** (distress behavior)
- **Quality threshold:** >95% accuracy

### Key Quality Metrics:
- All people in image annotated
- Bounding boxes tight around people
- Correct class assignments
- Valid YOLO format output

## 💡 Pro Tips

### Efficient Workflow:
1. **Use keyboard shortcuts:**
   - W: Create box
   - A/D: Previous/Next image
   - Ctrl+S: Save
   - Del: Delete selected box

2. **Quality checks:**
   - Zoom in for small people
   - Check image corners for partially visible people
   - Verify classes match behavior

3. **Consistency rules:**
   - When in doubt, choose "swimming"
   - Brief underwater = swimming
   - Extended struggle = drowning
   - Vertical position + distress = drowning

## 📊 Progress Tracking

### Daily Goals:
- **Day 1:** 30-50 images (get comfortable)
- **Day 2:** 50-75 images (build speed)
- **Day 3:** 75-100 images (maintain quality)
- **Day 4:** Complete remaining images

### Quality Check Points:
- After 25 images: Self-review
- After 50 images: Peer review (if available)
- After 100 images: Comprehensive review
- Final: Complete quality validation

## 🔧 Troubleshooting

### Common Issues:

**Issue:** LabelImg won't start
**Solution:** 
```bash
pip install PyQt5
python tools/setup_labelimg.py
```

**Issue:** Classes not showing
**Solution:** 
- Check predefined_classes.txt exists
- Restart LabelImg
- Manually load classes file

**Issue:** Annotations not saving
**Solution:**
- Check write permissions
- Verify save directory path
- Try saving manually (Ctrl+S)

**Issue:** Can't decide on class
**Solution:**
- Review annotation guidelines
- When uncertain, choose "swimming"
- Flag for review with team

## 📁 File Structure

```
pilot_batch/
├── images/                    # 250 selected images
│   ├── train_swimming_*.jpg
│   ├── train_drowning_*.jpg
│   ├── val_swimming_*.jpg
│   └── ...
├── annotations/               # YOLO format annotations
│   ├── train_swimming_*.txt
│   └── ...
├── pilot_metadata.json       # Progress tracking
├── annotation_checklist.md   # Quality checklist
└── QUICK_START.md           # This file
```

## ✅ Success Criteria

Pilot batch is complete when:
- [ ] All ~250 images annotated
- [ ] Quality review passed (>95% accuracy)
- [ ] Consistent standards established
- [ ] Ready to scale to full dataset
- [ ] Team approved to proceed

## 🎓 Next Steps After Pilot

1. **Quality Review:** External validation of annotations
2. **Guidelines Refinement:** Update based on learnings
3. **Full Dataset Planning:** Batch processing strategy
4. **Team Training:** Scale annotation team if needed
5. **Automation Setup:** Integrate with pre-annotation

---

**Estimated Time:** 8-12 hours for 250 images (experienced annotator)  
**Quality Focus:** Accuracy over speed in pilot phase
