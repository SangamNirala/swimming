#!/bin/bash

# Automated Dataset Setup Script
# This script automates the entire dataset sourcing process

set -e  # Exit on error

echo "=========================================="
echo "Swimming Pool Drowning Detection"
echo "Dataset Setup Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}Error: Please run this script from /app/datasets/scripts directory${NC}"
    exit 1
fi

echo -e "${GREEN}Step 1: Installing dependencies...${NC}"
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Check for API key
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file not found${NC}"
    echo "Please create .env file with your Roboflow API key:"
    echo ""
    echo "  1. Go to https://roboflow.com"
    echo "  2. Sign up / Log in"
    echo "  3. Go to Settings → Roboflow API"
    echo "  4. Copy your API key"
    echo "  5. Create .env file:"
    echo ""
    echo "     echo 'ROBOFLOW_API_KEY=your_key_here' > .env"
    echo ""
    read -p "Press Enter after creating .env file..."
fi

# Verify API key exists
if ! grep -q "ROBOFLOW_API_KEY" .env 2>/dev/null; then
    echo -e "${RED}Error: ROBOFLOW_API_KEY not found in .env${NC}"
    exit 1
fi

echo -e "${GREEN}Step 2: Downloading datasets from Roboflow...${NC}"
echo "This may take 10-20 minutes depending on your internet speed."
echo ""
python download_roboflow.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Datasets downloaded successfully${NC}"
else
    echo -e "${RED}✗ Error downloading datasets${NC}"
    exit 1
fi
echo ""

echo -e "${GREEN}Step 3: Organizing dataset...${NC}"
echo "Creating train/val/test splits (70/15/15)..."
echo ""
python organize_dataset.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Dataset organized successfully${NC}"
else
    echo -e "${RED}✗ Error organizing dataset${NC}"
    exit 1
fi
echo ""

echo -e "${GREEN}Step 4: Verifying dataset quality...${NC}"
echo ""
python verify_dataset.py
echo ""

echo -e "${GREEN}Step 5: Generating statistics...${NC}"
echo ""
python dataset_stats.py --save
echo ""

echo "=========================================="
echo -e "${GREEN}DATASET SETUP COMPLETE!${NC}"
echo "=========================================="
echo ""
echo "Dataset location: /app/datasets"
echo ""
echo "Next steps:"
echo "  1. Review dataset statistics above"
echo "  2. Proceed to Phase 2: Model Training"
echo "  3. Train YOLO detection model"
echo "  4. Train action classification model"
echo ""
echo "Documentation: /app/datasets/README.md"
echo "Quick Start: /app/datasets/QUICK_START.md"
echo "=========================================="
