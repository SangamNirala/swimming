# Pilot Batch Annotation Checklist

## 🎯 Goal
Annotate 200-300 images to establish annotation quality and consistency standards.

## 📋 Pre-Annotation Checklist
- [ ] Read annotation guidelines thoroughly
- [ ] LabelImg properly installed and configured
- [ ] Understand class definitions (swimming vs drowning)
- [ ] Comfortable with bounding box drawing
- [ ] Know keyboard shortcuts (W, A/D, Ctrl+S)

## 🎨 Annotation Process (Per Image)
- [ ] Open image in LabelImg
- [ ] Identify all people in the image
- [ ] For each person:
  - [ ] Draw tight bounding box around person
  - [ ] Assign correct class (swimming=0, drowning=1)
  - [ ] Verify box doesn't extend beyond image boundaries
- [ ] Double-check all annotations
- [ ] Save annotation file (.txt format)
- [ ] Mark image as completed in checklist

## 🔍 Quality Control (Every 10 Images)
- [ ] Review last 10 annotations for consistency
- [ ] Check for missed people
- [ ] Verify class assignments are correct
- [ ] Ensure bounding boxes are tight and accurate
- [ ] Confirm YOLO format is proper

## 📊 Progress Tracking
- [ ] Update progress in pilot_metadata.json
- [ ] Note any challenging images for review
- [ ] Flag any unclear cases for discussion
- [ ] Maintain annotation quality log

## ✅ Completion Criteria
- [ ] All pilot images annotated
- [ ] Self-review completed
- [ ] Quality metrics meet standards:
  - [ ] >95% of people properly annotated
  - [ ] >90% correct class assignments
  - [ ] <5% bounding box errors
- [ ] Ready for peer review

## 🚨 Common Issues to Watch
- [ ] Boxes too large (including too much background)
- [ ] Missing people in crowded scenes
- [ ] Confusing normal underwater swimming with drowning
- [ ] Inconsistent box sizing
- [ ] Wrong class assignments

## 📞 When to Ask for Help
- Unclear whether behavior is swimming vs drowning
- Technical issues with LabelImg
- Unusual edge cases
- Quality concerns
- Process questions

---

**Remember:** Quality over speed! Take time to do it right.
