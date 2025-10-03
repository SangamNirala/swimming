# Swimming Pool Drowning Detection - Annotation Guidelines

## 📋 Overview

These guidelines ensure consistent, high-quality annotations for training a YOLO drowning detection model. Each annotator must follow these rules to maintain dataset quality and model accuracy.

---

## 🎯 Class Definitions

### Class 0: "swimming" (Normal Swimming Behavior)
**Label when you see:**
- ✅ Person actively swimming (any stroke style)
- ✅ Floating calmly on surface
- ✅ Standing or sitting in shallow water
- ✅ Playing, splashing, or recreating normally
- ✅ Swimming underwater briefly (< 3 seconds visible)
- ✅ Diving and immediately surfacing
- ✅ Swimming laps (brief submersion is normal)
- ✅ Treading water comfortably
- ✅ Getting in/out of pool normally

**Visual Indicators:**
- Controlled body movements
- Horizontal swimming position
- Head above water most of the time
- Purposeful movements
- Relaxed body posture

### Class 1: "drowning" (Distress/Sinking Behavior)
**Label when you see:**
- ❌ Vertical body position in water (struggling)
- ❌ Arms flailing or not moving at all
- ❌ Head tilted back, mouth gasping for air
- ❌ Body sinking or submerged for extended period (>3 seconds)
- ❌ Struggling with no forward progress
- ❌ Person appears to be in distress
- ❌ Unusual body position (not swimming normally)
- ❌ Panicked or erratic movements

**Visual Indicators:**
- Vertical body orientation
- Arms moving ineffectively
- Head low in water or submerged
- No forward swimming progress
- Panicked or distressed expression
- Body appearing to sink

---

## 📏 Bounding Box Guidelines

### Box Size and Positioning
1. **Tight Boxes:** Draw bounding boxes as tight as possible around the person
2. **Full Body:** Include the entire visible person (head to feet if visible)
3. **No Extra Space:** Minimize empty space inside the box
4. **Partial Visibility:** If person is partially out of frame, box only visible parts

### Box Quality Standards
```
✅ GOOD BOUNDING BOX:
┌─────────────────┐
│     👤          │  ← Tight around person
│    /|\          │  ← Includes full visible body
│    / \          │  ← Minimal empty space
└─────────────────┘

❌ BAD BOUNDING BOX:
┌───────────────────────┐
│                       │  ← Too much empty space
│         👤            │  ← Person too small in box
│        /|\            │  ← Wasted annotation area
│        / \            │
│                       │
└───────────────────────┘
```

### Multiple People Guidelines
- **Each person gets their own bounding box**
- **Overlapping boxes are OK when people are close**
- **Assign appropriate class to each individual**
- **If people are tightly grouped, use best judgment for individual boxes**

---

## 🔍 Special Cases and Edge Situations

### Case 1: Partially Visible People
**Scenario:** Person is partially cut off by image edge
**Action:** 
- Draw box around visible parts only
- Don't extend box beyond image boundaries
- If <30% of person visible, consider skipping annotation

### Case 2: Underwater Swimmers (Competitive/Lap Swimming)
**Scenario:** Swimmer intentionally underwater (diving, lap swimming)
**Action:**
- If brief underwater (< 3 seconds context): Label as "swimming" 
- If extended underwater with struggling motion: Label as "drowning"
- Consider body language and movement pattern

### Case 3: Children vs Adults
**Scenario:** Different age groups in pool
**Action:**
- Same rules apply regardless of age
- Children may have different swimming patterns - judge by distress level
- Normal child play = "swimming"
- Child in distress = "drowning"

### Case 4: Reflections and Water Distortion
**Scenario:** Water surface creates reflections or distorts appearance
**Action:**
- Annotate the actual person, not the reflection
- If distortion makes classification unclear, use best judgment
- Skip annotation if person is completely unclear

### Case 5: Multiple People Close Together
**Scenario:** Swimmers very close or overlapping
**Action:**
- Draw individual boxes for each person if distinguishable
- If people are completely overlapping, draw one box and use majority class
- Prioritize drowning classification if any person appears distressed

### Case 6: Person Entering/Exiting Pool
**Scenario:** Person partially in water (getting in/out)
**Action:**
- Label as "swimming" if getting in/out normally
- Include full visible body in bounding box
- If falling or struggling to get out, may be "drowning"

### Case 7: Floating or Stationary People
**Scenario:** Person floating still or not moving
**Action:**
- If floating comfortably on back/stomach: "swimming"
- If appears unconscious or motionless in distress: "drowning"
- Consider facial expression and body position

---

## 🎨 LabelImg Workflow

### Before Starting
1. **Review these guidelines thoroughly**
2. **Examine 5-10 sample images to understand the data**
3. **Set up LabelImg with proper class names**
4. **Prepare comfortable workspace (good lighting, large monitor if possible)**

### Annotation Process
```
For each image:
1. Open image in LabelImg
2. Review any pre-existing annotations (from YOLO pre-annotation)
3. For each person in image:
   a. Draw bounding box around person
   b. Assign correct class (swimming=0, drowning=1)
   c. Verify box is tight and accurate
4. Double-check all annotations
5. Save annotation file (.txt format)
6. Move to next image
```

### LabelImg Keyboard Shortcuts
- **W:** Create new bounding box
- **A/D:** Navigate to previous/next image
- **Del:** Delete selected bounding box
- **Ctrl+S:** Save annotations
- **Ctrl+D:** Duplicate bounding box
- **Space:** Flag image as verified

### Quality Checklist (Per Image)
- [ ] All people in image are annotated
- [ ] Bounding boxes are tight around people
- [ ] Correct class assigned (swimming vs drowning)
- [ ] No overlapping boxes for same person
- [ ] Boxes don't extend beyond image boundaries
- [ ] Annotation saved in YOLO format

---

## ⚖️ Consistency Rules

### Classification Priority
1. **When in doubt, lean toward "swimming"** (false positives for drowning are worse than false negatives)
2. **Drowning classification requires clear distress indicators**
3. **Brief underwater activity is usually "swimming"**
4. **Vertical body position + struggling = "drowning"**

### Inter-annotator Agreement
- All annotators must review these guidelines
- Sample images should be annotated by multiple people for consistency check
- Regular calibration sessions recommended
- Disagreements resolved by senior annotator or project lead

### Quality Thresholds
**Target Standards:**
- Bounding box accuracy: >95% (correct person coverage)
- Class accuracy: >90% (correct swimming vs drowning)
- Completeness: >98% (all people annotated)
- Format compliance: 100% (valid YOLO format)

---

## 📊 YOLO Format Specification

### File Format
```
# For each image file: image_name.jpg
# Create annotation file: image_name.txt
# Each line represents one bounding box:
class_id center_x center_y width height

# All coordinates normalized to 0.0 - 1.0
```

### Coordinate System
```
Image coordinate system:
(0,0) ────────── (1,0)
  │                │
  │    center_x,   │
  │    center_y    │
  │       ┌─┐      │
  │       └─┘      │
  │                │
(0,1) ────────── (1,1)

center_x = (left + right) / 2 / image_width
center_y = (top + bottom) / 2 / image_height
width = box_width / image_width  
height = box_height / image_height
```

### Example Annotation Files
```
# swimming_train_00001.txt
# One person swimming (class 0) in center of image
0 0.5 0.4 0.2 0.6

# drowning_train_00002.txt  
# Two people: one swimming, one drowning
0 0.3 0.5 0.15 0.4    # Swimming person on left
1 0.7 0.6 0.18 0.5    # Drowning person on right

# swimming_val_00003.txt
# Multiple swimmers
0 0.2 0.3 0.12 0.35   # Swimmer 1
0 0.6 0.4 0.14 0.42   # Swimmer 2  
0 0.8 0.7 0.16 0.38   # Swimmer 3
```

---

## 🚨 Common Mistakes to Avoid

### ❌ Don't Do This:
1. **Boxes too large:** Including too much water/background
2. **Missing people:** Not annotating everyone in the image
3. **Wrong classes:** Labeling normal swimming as drowning
4. **Inconsistent sizing:** Dramatically different box sizes for similar people
5. **Outside boundaries:** Boxes extending beyond image edges
6. **Duplicate boxes:** Multiple boxes for the same person

### ✅ Best Practices:
1. **Consistent standards:** Apply same criteria to all images
2. **Regular breaks:** Take breaks to maintain concentration
3. **Double-check:** Review annotations before saving
4. **Ask questions:** Clarify uncertain cases with team
5. **Track progress:** Keep notes on challenging images
6. **Quality over speed:** Accuracy is more important than speed

---

## 🔧 Troubleshooting

### Issue: Can't decide between swimming/drowning
**Solution:** Look for key indicators:
- Body position (horizontal vs vertical)
- Arm movements (controlled vs frantic)
- Context clues (other people's reactions)
- When in doubt, choose "swimming"

### Issue: Person partially underwater
**Solution:** 
- Brief submersion (diving, lap swimming) = "swimming"
- Extended underwater with struggling = "drowning"
- Consider visible body language

### Issue: Very small people in image
**Solution:**
- If person is clearly visible and identifiable, annotate
- If person is <20 pixels, consider skipping
- Maintain consistency across dataset

### Issue: Blurry or unclear image
**Solution:**
- Use best judgment with available information
- If completely unclear, flag for review
- Don't guess - accuracy is critical

---

## 📈 Quality Control Process

### Self-Review Checklist (Every 10 Images)
- [ ] Reviewed annotation accuracy
- [ ] Checked for missed people
- [ ] Verified class assignments
- [ ] Ensured proper YOLO format
- [ ] Maintained consistent standards

### Peer Review Process
- Sample 10% of annotations for peer review
- Cross-check difficult cases with other annotators
- Maintain annotation log for quality tracking
- Regular calibration sessions

### Validation Scripts
Automated checks will verify:
- File format compliance
- Coordinate bounds (0.0-1.0)
- Missing annotation files
- Class ID validity (0 or 1)
- Bounding box reasonableness

---

## 📝 Progress Tracking

### Daily Goals
- **Pilot Phase:** 20-30 images/day (focus on quality)
- **Production Phase:** 50-100 images/day (experienced annotators)
- **Quality Review:** 100-200 images/day

### Milestones
- ✅ Guidelines reviewed and understood
- ⏳ Pilot batch completed (200-300 images)
- ⏳ Quality review passed
- ⏳ Full dataset annotation started
- ⏳ All 9,342 images annotated
- ⏳ Final validation completed

---

## 📞 Support and Questions

### When to Ask for Help
- Unclear class assignment
- Technical issues with LabelImg
- Unusual edge cases not covered
- Quality concerns
- Process questions

### How to Report Issues
1. Note image filename and issue description
2. Take screenshot if helpful
3. Continue with other images
4. Compile questions for batch review

---

## ✅ Final Checklist

Before considering annotation complete:
- [ ] All guidelines reviewed and understood
- [ ] LabelImg properly configured
- [ ] Pilot batch successfully annotated
- [ ] Quality review passed
- [ ] Consistent standards maintained
- [ ] All files in proper YOLO format
- [ ] Progress tracking updated
- [ ] Final validation completed

---

**Remember:** Quality and consistency are more important than speed. Take time to do annotations correctly the first time!

---

*Guidelines Version: 1.0*  
*Last Updated: 2025-01-15*  
*Project: Swimming Pool Drowning Detection System*