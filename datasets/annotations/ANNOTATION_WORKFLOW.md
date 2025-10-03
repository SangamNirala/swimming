# 🎯 Annotation Workflow - Getting Started

## 🚀 Quick Start (5 Minutes)

Your annotation system is ready! Here's how to start reviewing and correcting the 248 pre-annotated images:

### Step 1: Check Current Status
```bash
cd /app/datasets/annotations/tools
python alternative_annotation.py --mode status
```

**Current Status:**
- ✅ 248 images pre-annotated
- ✅ 215 bounding boxes generated
- ⚠️  All boxes labeled as "swimming" (need manual correction)
- 🎯 Need to identify drowning cases and adjust boxes

---

## 🔍 Review Process

### Understanding Pre-Annotations
All 248 images have been automatically processed with:
- **Bounding boxes** around detected people
- **Default class:** All labeled as "swimming" (class 0)
- **Your task:** Review each box and correct class labels

### Key Review Tasks:
1. **Adjust class labels:** Change "swimming" to "drowning" where appropriate
2. **Refine bounding boxes:** Make them tighter around people
3. **Add missing people:** YOLO may have missed some
4. **Remove false positives:** Delete incorrect detections

---

## 🛠️ Using the Annotation Interface

### Launch the Command-Line Interface:
```bash
cd /app/datasets/annotations/tools
python alternative_annotation.py
```

### Interface Commands:
- **n** or **Enter** → Next image
- **p** → Previous image  
- **e** → Edit annotations for current image
- **v** → View image details
- **s** → Skip current image
- **q** → Quit

### Editing Commands (when in edit mode):
- **a** → Add new bounding box
- **d 1** → Delete annotation #1
- **c 1 1** → Change annotation #1 to class 1 (drowning)
- **c 2 0** → Change annotation #2 to class 0 (swimming)
- **s** → Save changes
- **x** → Exit without saving

---

## 📋 Annotation Guidelines Summary

### 🏊 Swimming (Class 0) - Normal Behavior
- Person actively swimming
- Floating calmly on surface
- Playing or recreational activities
- Standing/sitting in water
- Brief underwater (diving, lap swimming)

### 🆘 Drowning (Class 1) - Distress Behavior  
- Vertical body position with struggling
- Arms flailing or not moving
- Head tilted back, gasping
- Extended time underwater (>3 seconds)
- Visible panic or distress

### 💡 When in Doubt:
- **Choose "swimming"** if behavior is unclear
- Focus on **body position** and **movement patterns**
- Consider **context** (other people's reactions)

---

## 📊 Progress Tracking

### Check Your Progress:
```bash
python progress_tracker.py --live
```

### Generate Detailed Report:
```bash
python progress_tracker.py --report
```

### Validate Quality:
```bash
python validate_annotations.py
```

---

## 🎯 Recommended Workflow

### Phase 1: Sample Review (First 25 Images)
1. Launch annotation interface
2. Review first 25 images carefully
3. Focus on understanding the data
4. Establish consistent standards
5. Take notes on challenging cases

### Phase 2: Quality Check (After 50 Images)
1. Run validation script
2. Check class distribution
3. Review difficult cases
4. Adjust approach if needed

### Phase 3: Steady Progress (Remaining Images)
1. Maintain consistent pace
2. Regular validation every 50 images
3. Track progress with reports
4. Focus on quality over speed

---

## 📈 Quality Targets

### Current Status:
- Total bounding boxes: 215
- Swimming: 215 (100%)
- Drowning: 0 (0%)
- **Target:** 15-25% drowning cases

### Quality Goals:
- **Accuracy:** >95% correct class assignments
- **Completeness:** All people annotated
- **Consistency:** Uniform annotation standards
- **Validation:** 100% format compliance

---

## 💡 Pro Tips

### Efficient Workflow:
1. **Scan quickly** through images first
2. **Focus on obvious drowning** cases first
3. **Use keyboard shortcuts** for speed
4. **Take breaks** to maintain focus
5. **Ask questions** when uncertain

### Common Patterns:
- Most images will stay "swimming"
- Look for vertical body positions
- Check for struggling movements
- Consider water activity context
- When uncertain, choose "swimming"

### Quality Indicators:
- Tight bounding boxes around people
- Correct behavior-based classifications
- No missed people in images
- No false positive detections

---

## 🔧 Troubleshooting

### If Interface Won't Start:
```bash
cd /app/datasets/annotations/tools
python -c "import cv2; print('OpenCV OK')"
python alternative_annotation.py --mode status
```

### If Annotations Look Wrong:
1. Check YOLO format: `python validate_annotations.py`
2. View raw annotation file: `cat /app/datasets/annotations/pilot_batch/annotations/filename.txt`
3. Reset if needed: Delete `.txt` file and re-run pre-annotation

### If Progress Tracking Fails:
```bash
# Manual status check:
ls /app/datasets/annotations/pilot_batch/images/*.jpg | wc -l
ls /app/datasets/annotations/pilot_batch/annotations/*.txt | wc -l
```

---

## 📞 Getting Help

### Quick Reference:
- **Guidelines:** `/app/datasets/annotations/guidelines/annotation_guidelines.md`
- **Status Reports:** `python alternative_annotation.py --mode status`  
- **Live Progress:** `python progress_tracker.py --live`
- **Validation:** `python validate_annotations.py`

### Sample Commands:
```bash
# Start annotating
python alternative_annotation.py

# Check progress  
python progress_tracker.py --live

# Validate quality
python validate_annotations.py

# View status
python alternative_annotation.py --mode status
```

---

## 🎊 Success Milestones

### ✅ Checkpoint 1 (25 images reviewed):
- Understand annotation interface
- Establish consistent standards  
- Identify challenging cases
- Estimate time requirements

### ✅ Checkpoint 2 (100 images reviewed):
- Quality validation passed
- Class distribution reasonable
- Consistent annotation quality
- Comfortable with workflow

### ✅ Checkpoint 3 (248 images complete):
- All images reviewed and corrected
- Quality targets achieved
- Ready for full dataset scaling
- Documentation updated

---

## 🚀 Ready to Start!

Your annotation system is fully operational and ready for use. The 248 pilot images provide an excellent foundation for establishing quality standards and workflow efficiency.

**Start with this command:**
```bash
cd /app/datasets/annotations/tools
python alternative_annotation.py
```

**Remember:** Quality over speed! Take time to do it right in the pilot phase. This will save significant time when scaling to the full 9,342 image dataset.

Good luck with your annotations! 🏊‍♂️🆘