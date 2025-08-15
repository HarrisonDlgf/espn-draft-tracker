#!/usr/bin/env python3

import subprocess
import sys
import os

def main():
    print("ESPN Draft Assistant Launcher")
    print("=" * 40)
    print("Choose your preferred interface:")
    print()
    print("1. GUI Version (Recommended)")
    print("   - Full graphical interface")
    print("   - Easy manual pick selection")
    print("   - Real-time updates")
    print("   - Position analysis buttons")
    print()
    print("2. Console Version")
    print("   - Text-based interface")
    print("   - Works in terminal")
    print("   - Manual pick with numbers")
    print()
    print("3. Test Mode (GUI)")
    print("   - GUI without ESPN connection")
    print("   - For testing features")
    print()
    
    while True:
        try:
            choice = input("Enter your choice (1-3): ").strip()
            
            if choice == '1':
                print("\nLaunching GUI version...")
                subprocess.run([sys.executable, "main_gui.py"])
                break
            elif choice == '2':
                print("\nLaunching console version...")
                subprocess.run([sys.executable, "main.py"])
                break
            elif choice == '3':
                print("\nLaunching test mode...")
                # Set TEST_MODE to True in main_gui.py
                with open("main_gui.py", "r") as f:
                    content = f.read()
                content = content.replace("TEST_MODE = False", "TEST_MODE = True")
                with open("main_gui.py", "w") as f:
                    f.write(content)
                subprocess.run([sys.executable, "main_gui.py"])
                # Reset TEST_MODE to False
                content = content.replace("TEST_MODE = True", "TEST_MODE = False")
                with open("main_gui.py", "w") as f:
                    f.write(content)
                break
            else:
                print("Please enter 1, 2, or 3")
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
