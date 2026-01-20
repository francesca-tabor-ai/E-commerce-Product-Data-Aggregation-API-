#!/bin/bash

# E-commerce Product Data API - Setup Script
# Run this from the outputs folder to set up your local repo

echo "🚀 E-commerce Product Data API - Setup"
echo "========================================"

# Check if we're in the right directory
if [ ! -f "README.md" ]; then
    echo "❌ Error: Please run this script from the E-commerce-Product-Data-Aggregation-API folder"
    echo "   cd to the folder where you downloaded the files first"
    exit 1
fi

# Define target directory
TARGET_DIR="/Users/francescatabor/Documents/1.Technology/Github/API/E-commerce-Product-Data-Aggregation-API-"

echo ""
echo "📁 Target directory: $TARGET_DIR"
echo ""

# Create target if it doesn't exist
if [ ! -d "$TARGET_DIR" ]; then
    echo "Creating target directory..."
    mkdir -p "$TARGET_DIR"
fi

# Copy all files
echo "📦 Copying files..."

# Copy main files
cp -v README.md "$TARGET_DIR/"
cp -v QUICK_START.md "$TARGET_DIR/"
cp -v requirements.txt "$TARGET_DIR/"
cp -v .env.example "$TARGET_DIR/"
cp -v .gitignore "$TARGET_DIR/"

# Copy directories
echo ""
echo "📂 Copying directories..."
cp -rv src "$TARGET_DIR/"
cp -rv .github "$TARGET_DIR/"
mkdir -p "$TARGET_DIR/tests"
mkdir -p "$TARGET_DIR/docs"
mkdir -p "$TARGET_DIR/scripts"

echo ""
echo "✅ Files copied successfully!"
echo ""
echo "📍 Next steps:"
echo "1. cd $TARGET_DIR"
echo "2. python3 -m venv venv"
echo "3. source venv/bin/activate"
echo "4. pip install -r requirements.txt"
echo "5. cp .env.example .env"
echo "6. python src/api/main.py"
echo ""
echo "🚀 Your API will be at http://localhost:8000"
echo "📚 Docs at http://localhost:8000/docs"
echo ""
echo "Happy coding! 🎉"
