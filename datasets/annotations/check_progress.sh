#!/bin/bash

# YOLOv8s Annotation Progress Checker

echo "======================================================================="
echo "🔍 YOLOv8s High-Accuracy Annotation Progress"
echo "======================================================================="
echo ""

# Check if process is running
if ps aux | grep -q "[p]ython high_accuracy_annotate.py"; then
    echo "✅ Status: RUNNING"
    RUNTIME=$(ps aux | grep "[p]ython high_accuracy_annotate.py" | awk '{print $10}')
    CPU=$(ps aux | grep "[p]ython high_accuracy_annotate.py" | awk '{print $3}')
    echo "   Runtime: $RUNTIME"
    echo "   CPU Usage: $CPU%"
else
    echo "⚠️  Status: NOT RUNNING"
fi

echo ""
echo "-----------------------------------------------------------------------"
echo "📊 Annotation Progress"
echo "-----------------------------------------------------------------------"

# Count annotation files
COUNT=$(find /app/datasets/annotations/yolov8s_annotations -name "*.txt" 2>/dev/null | wc -l)
TOTAL=9342
PROGRESS=$(awk "BEGIN {printf \"%.1f\", $COUNT * 100 / $TOTAL}")

echo "   Annotations Created: $COUNT / $TOTAL"
echo "   Progress: $PROGRESS%"

# Create progress bar
FILLED=$(awk "BEGIN {printf \"%.0f\", $COUNT * 50 / $TOTAL}")
printf "   ["
for i in $(seq 1 $FILLED); do printf "█"; done
for i in $(seq $FILLED 49); do printf "░"; done
printf "] $PROGRESS%%\n"

echo ""

# Estimate remaining time
if [ $COUNT -gt 0 ]; then
    SPEED=2  # images per second
    REMAINING=$(awk "BEGIN {printf \"%.0f\", ($TOTAL - $COUNT) / $SPEED / 60}")
    echo "   Estimated Time Remaining: $REMAINING minutes"
fi

echo ""
echo "-----------------------------------------------------------------------"
echo "📁 Output Directory"
echo "-----------------------------------------------------------------------"
echo "   /app/datasets/annotations/yolov8s_annotations/"
echo ""

# Count by split if directories exist
if [ -d "/app/datasets/annotations/yolov8s_annotations/train" ]; then
    TRAIN_COUNT=$(find /app/datasets/annotations/yolov8s_annotations/train -name "*.txt" 2>/dev/null | wc -l)
    echo "   Train: $TRAIN_COUNT annotations"
fi

if [ -d "/app/datasets/annotations/yolov8s_annotations/val" ]; then
    VAL_COUNT=$(find /app/datasets/annotations/yolov8s_annotations/val -name "*.txt" 2>/dev/null | wc -l)
    echo "   Val: $VAL_COUNT annotations"
fi

if [ -d "/app/datasets/annotations/yolov8s_annotations/test" ]; then
    TEST_COUNT=$(find /app/datasets/annotations/yolov8s_annotations/test -name "*.txt" 2>/dev/null | wc -l)
    echo "   Test: $TEST_COUNT annotations"
fi

echo ""
echo "-----------------------------------------------------------------------"
echo "📋 Quick Commands"
echo "-----------------------------------------------------------------------"
echo "   View log: tail -f /app/datasets/annotations/tools/annotation_full.log"
echo "   Stop process: pkill -f high_accuracy_annotate.py"
echo "   Check this again: bash /app/datasets/annotations/check_progress.sh"
echo ""
echo "======================================================================="

# If complete
if [ $COUNT -eq $TOTAL ]; then
    echo ""
    echo "🎉 ANNOTATION COMPLETE!"
    echo ""
    echo "Next steps:"
    echo "1. Validate: python validate_yolov8s_annotations.py"
    echo "2. Visualize: python visualize_yolov8s_annotations.py --samples 100"
    echo "3. View stats: cat annotation_statistics.json"
    echo ""
    echo "======================================================================="
fi
