#!/usr/bin/env python3
"""
Test script for GUI functionality
"""

import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main_gui import create_main_window, create_manual_pick_window
from data_loader import load_and_clean_data
import PySimpleGUI as sg

def test_gui():
    """Test the GUI components"""
    
    print("🧪 Testing GUI Components")
    print("=" * 40)
    
    # Load data
    df = load_and_clean_data()
    if df is None:
        print("❌ Failed to load data")
        return
    
    print("✅ Data loaded successfully")
    print(f"📊 Loaded {len(df)} players")
    
    # Test main window creation
    try:
        main_window = create_main_window()
        print("✅ Main window created successfully")
        main_window.close()
    except Exception as e:
        print(f"❌ Main window creation failed: {e}")
        return
    
    # Test manual pick window creation
    try:
        manual_window = create_manual_pick_window(df, set(), 1)
        print("✅ Manual pick window created successfully")
        manual_window.close()
    except Exception as e:
        print(f"❌ Manual pick window creation failed: {e}")
        return
    
    print("\n🎉 All GUI tests passed!")
    print("You can now run: python main_gui.py")

if __name__ == "__main__":
    test_gui()
