#!/usr/bin/env python3
"""
LabelImg Setup and Configuration for Swimming Pool Drowning Detection
Installs and configures LabelImg for YOLO annotation workflow
"""

import os
import sys
import subprocess
import json
import shutil
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible with LabelImg"""
    if sys.version_info < (3, 6):
        print("❌ Error: Python 3.6+ required for LabelImg")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def install_labelimg():
    """Install LabelImg via pip"""
    print("\n🔧 Installing LabelImg...")
    
    try:
        # Try to import labelImg to check if already installed
        import labelImg
        print("✅ LabelImg already installed")
        return True
    except ImportError:
        pass
    
    # Install LabelImg
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "labelImg"
        ])
        print("✅ LabelImg installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install LabelImg: {e}")
        
        # Try alternative installation methods
        print("\n🔄 Trying alternative installation...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "labelImg==1.8.6"
            ])
            print("✅ LabelImg installed successfully (version 1.8.6)")
            return True
        except subprocess.CalledProcessError:
            pass
        
        print("\n💡 Manual installation required:")
        print("1. Try: pip install labelImg")
        print("2. Or: pip install git+https://github.com/tzutalin/labelImg.git")
        print("3. Or download from: https://github.com/tzutalin/labelImg")
        return False

def check_qt_dependencies():
    """Check if Qt dependencies are available"""
    print("\n🔍 Checking Qt dependencies...")
    
    try:
        import PyQt5
        print("✅ PyQt5 found")
        return True
    except ImportError:
        pass
    
    try:
        import PySide2
        print("✅ PySide2 found")
        return True
    except ImportError:
        pass
    
    print("⚠️  Qt dependencies not found. Installing PyQt5...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "PyQt5"
        ])
        print("✅ PyQt5 installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install PyQt5: {e}")
        return False

def create_predefined_classes():
    """Create predefined classes file for YOLO"""
    print("\n📝 Creating predefined classes...")
    
    classes_dir = Path("/app/datasets/annotations/tools")
    classes_dir.mkdir(parents=True, exist_ok=True)
    
    classes_file = classes_dir / "predefined_classes.txt"
    
    classes_content = """swimming
drowning"""
    
    with open(classes_file, 'w') as f:
        f.write(classes_content)
    
    print(f"✅ Created classes file: {classes_file}")
    return classes_file

def create_labelimg_config():
    """Create LabelImg configuration directory and files"""
    print("\n⚙️  Creating LabelImg configuration...")
    
    # Create config directory
    config_dir = Path.home() / ".labelImgSettings"
    config_dir.mkdir(exist_ok=True)
    
    # Create settings file for YOLO format
    settings = {
        "autoSaveMode": True,
        "singleClassMode": False,
        "displayLabelOption": True,
        "saveFormat": "YOLO",
        "recentFiles": [],
        "predefinedClassesFile": str(Path("/app/datasets/annotations/tools/predefined_classes.txt").absolute())
    }
    
    settings_file = config_dir / "settings.json"
    with open(settings_file, 'w') as f:
        json.dump(settings, f, indent=2)
    
    print(f"✅ Configuration saved to: {settings_file}")
    return settings_file

def create_launch_script():
    """Create convenient launch script for LabelImg"""
    print("\n🚀 Creating launch script...")
    
    tools_dir = Path("/app/datasets/annotations/tools")
    launch_script = tools_dir / "launch_labelimg.py"
    
    script_content = '''#!/usr/bin/env python3
"""
Launch LabelImg with proper configuration for drowning detection annotation
"""

import sys
import os
import subprocess
from pathlib import Path

def launch_labelimg(image_dir=None, annotation_dir=None):
    """Launch LabelImg with specified directories"""
    
    # Default directories
    if image_dir is None:
        image_dir = "/app/datasets/annotations/pilot_batch/images"
    if annotation_dir is None:
        annotation_dir = "/app/datasets/annotations/pilot_batch/annotations"
    
    # Ensure directories exist
    Path(image_dir).mkdir(parents=True, exist_ok=True)
    Path(annotation_dir).mkdir(parents=True, exist_ok=True)
    
    # Set predefined classes
    classes_file = "/app/datasets/annotations/tools/predefined_classes.txt"
    
    print("🎯 Launching LabelImg for Drowning Detection Annotation")
    print(f"📁 Images: {image_dir}")
    print(f"📝 Annotations: {annotation_dir}")
    print(f"🏷️  Classes: {classes_file}")
    print()
    print("💡 Quick Tips:")
    print("- Press W to create new bounding box")
    print("- Press A/D to navigate between images")
    print("- Press Ctrl+S to save")
    print("- Use class shortcuts: S (swimming), D (drowning)")
    print()
    
    try:
        # Launch LabelImg
        import labelImg.labelImg as labelImg_main
        
        # Set up arguments
        sys.argv = [
            'labelImg',
            image_dir,
            classes_file,
            annotation_dir
        ]
        
        # Launch
        labelImg_main.main()
        
    except ImportError:
        print("❌ LabelImg not found. Please run setup_labelimg.py first.")
        return False
    except Exception as e:
        print(f"❌ Error launching LabelImg: {e}")
        print("\\n💡 Alternative launch methods:")
        print(f"1. Command line: labelImg {image_dir} {classes_file} {annotation_dir}")
        print(f"2. Python: python -m labelImg {image_dir} {classes_file}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Launch LabelImg for annotation")
    parser.add_argument("--images", help="Directory containing images to annotate")
    parser.add_argument("--annotations", help="Directory to save annotations")
    
    args = parser.parse_args()
    
    launch_labelimg(args.images, args.annotations)
'''
    
    with open(launch_script, 'w') as f:
        f.write(script_content)
    
    # Make executable
    os.chmod(launch_script, 0o755)
    
    print(f"✅ Launch script created: {launch_script}")
    return launch_script

def create_directory_structure():
    """Create necessary directory structure for annotations"""
    print("\n📁 Creating directory structure...")
    
    base_dir = Path("/app/datasets/annotations")
    
    directories = [
        "guidelines",
        "tools", 
        "pilot_batch/images",
        "pilot_batch/annotations",
        "pilot_batch/labelimg_sessions",
        "quality_control/sample_review", 
        "quality_control/validation_reports",
        "workflows"
    ]
    
    for directory in directories:
        dir_path = base_dir / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  ✅ Created: {dir_path}")

def test_labelimg_installation():
    """Test if LabelImg can be imported and basic functionality works"""
    print("\n🧪 Testing LabelImg installation...")
    
    try:
        import labelImg
        print("✅ LabelImg import successful")
        
        # Test if main module exists
        try:
            import labelImg.labelImg
            print("✅ LabelImg main module accessible")
        except ImportError as e:
            print(f"⚠️  LabelImg main module issue: {e}")
            
        return True
    except ImportError as e:
        print(f"❌ LabelImg import failed: {e}")
        return False

def create_requirements():
    """Create requirements.txt for annotation tools"""
    print("\n📋 Creating requirements.txt...")
    
    requirements_content = """# Requirements for LabelImg and annotation tools
labelImg>=1.8.0
PyQt5>=5.12.0
numpy>=1.19.0
Pillow>=8.0.0
matplotlib>=3.3.0
opencv-python>=4.5.0
ultralytics>=8.0.0
torch>=1.12.0
torchvision>=0.13.0
onnxruntime>=1.12.0
tqdm>=4.62.0
"""
    
    requirements_file = Path("/app/datasets/annotations/tools/requirements.txt")
    with open(requirements_file, 'w') as f:
        f.write(requirements_content)
    
    print(f"✅ Requirements saved to: {requirements_file}")
    return requirements_file

def main():
    """Main setup function"""
    print("🏊 Swimming Pool Drowning Detection - LabelImg Setup")
    print("=" * 60)
    
    success_steps = []
    
    # Step 1: Check Python version
    if check_python_version():
        success_steps.append("Python version check")
    else:
        print("❌ Setup failed: Incompatible Python version")
        return False
    
    # Step 2: Check/Install Qt dependencies  
    if check_qt_dependencies():
        success_steps.append("Qt dependencies")
    else:
        print("⚠️  Continuing without Qt (may cause issues)")
    
    # Step 3: Install LabelImg
    if install_labelimg():
        success_steps.append("LabelImg installation")
    else:
        print("❌ Setup failed: Could not install LabelImg")
        return False
    
    # Step 4: Create directory structure
    create_directory_structure()
    success_steps.append("Directory structure")
    
    # Step 5: Create predefined classes
    classes_file = create_predefined_classes()
    success_steps.append("Predefined classes")
    
    # Step 6: Create configuration
    config_file = create_labelimg_config()
    success_steps.append("LabelImg configuration")
    
    # Step 7: Create launch script
    launch_script = create_launch_script()
    success_steps.append("Launch script")
    
    # Step 8: Create requirements
    requirements_file = create_requirements()
    success_steps.append("Requirements file")
    
    # Step 9: Test installation
    if test_labelimg_installation():
        success_steps.append("Installation test")
    else:
        print("⚠️  Installation test failed, but continuing...")
    
    # Summary
    print("\n" + "=" * 60)
    print("🎉 LabelImg Setup Complete!")
    print(f"✅ Successful steps: {len(success_steps)}/8")
    
    print("\n📋 Setup Summary:")
    for step in success_steps:
        print(f"  ✅ {step}")
    
    print(f"\n📁 Files created:")
    print(f"  📝 Classes: {classes_file}")
    print(f"  ⚙️  Config: {config_file}")
    print(f"  🚀 Launch: {launch_script}")
    print(f"  📋 Requirements: {requirements_file}")
    
    print(f"\n🎯 Next Steps:")
    print("1. Run: python tools/create_pilot_batch.py")
    print("2. Run: python tools/pre_annotate.py")
    print("3. Run: python tools/launch_labelimg.py")
    print("4. Start annotating images!")
    
    print(f"\n💡 Quick Commands:")
    print("# Launch LabelImg for pilot batch:")
    print("python /app/datasets/annotations/tools/launch_labelimg.py")
    print()
    print("# Launch with custom directories:")
    print("python /app/datasets/annotations/tools/launch_labelimg.py --images /path/to/images --annotations /path/to/annotations")
    
    return True

if __name__ == "__main__":
    main()