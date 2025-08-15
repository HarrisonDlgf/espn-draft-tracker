"""
Quick setup script for ESPN Mock Draft
"""

import os
import sys

def set_scoring_type():
    """Set the scoring type for manual mode"""
    print("\n🏈 Manual Mode Setup")
    print("=" * 40)
    print("Select your scoring format:")
    print("1. Non-PPR (Standard)")
    print("2. Half-PPR (0.5 points per reception)")
    print()
    
    while True:
        try:
            choice = input("Enter choice (1-2): ").strip()
            
            if choice == '1':
                print("✅ Set to Non-PPR scoring")
                return 'non_ppr'
            elif choice == '2':
                print("✅ Set to Half-PPR scoring")
                return 'half_ppr'
            else:
                print("Please enter 1 or 2")
        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(0)

def configure_manual_mode(scoring_type):
    """Configure the system for manual mode"""
    print(f"\n🏈 Configuring manual mode for {scoring_type.upper()}...")
    
    # Import and set scoring type
    try:
        sys.path.append('src')
        from config import set_league_type
        set_league_type(scoring_type)
        print(f"✅ Scoring type set to {scoring_type.upper()}")
    except Exception as e:
        print(f"❌ Error setting scoring type: {e}")
        return False
    
    # Set TEST_MODE to True in main_gui.py
    try:
        gui_file = 'src/main_gui.py'
        with open(gui_file, 'r') as f:
            content = f.read()
        
        # Replace TEST_MODE setting
        content = content.replace('TEST_MODE = False', 'TEST_MODE = True')
        
        with open(gui_file, 'w') as f:
            f.write(content)
        
        print("✅ Manual mode enabled")
        return True
        
    except Exception as e:
        print(f"❌ Error configuring manual mode: {e}")
        return False

def launch_manual_gui():
    """Launch the GUI in manual mode"""
    print("\n🚀 Launching GUI in manual mode...")
    print("=" * 40)
    print("Features available:")
    print("• Manual pick selection (50 players per position)")
    print("• VOR-based recommendations")
    print("• Position analysis")
    print("• Color-coded tiers")
    print("• Auto-refresh after adding players")
    print()
    print("Use the '➕ Add Pick' button to add players manually")
    print("Press Ctrl+C to exit")
    print("=" * 40)
    
    try:
        os.system(f"{sys.executable} src/main_gui.py")
    except KeyboardInterrupt:
        print("\nExiting manual mode...")
    except Exception as e:
        print(f"❌ Error launching GUI: {e}")

def cleanup():
    """Reset TEST_MODE to False after exiting"""
    try:
        gui_file = 'src/main_gui.py'
        with open(gui_file, 'r') as f:
            content = f.read()
        
        # Reset TEST_MODE to False
        content = content.replace('TEST_MODE = True', 'TEST_MODE = False')
        
        with open(gui_file, 'w') as f:
            f.write(content)
        
        print("✅ Manual mode disabled")
        
    except Exception as e:
        print(f"⚠️  Warning: Could not reset manual mode: {e}")

def main():
    print("🏈 ESPN Mock Draft Setup")
    print("=" * 40)
    print()
    
    print("Choose your setup method:")
    print("1. Automated setup (recommended)")
    print("2. Manual setup")
    print("3. Manual mode only (no ESPN config needed)")
    print("4. Test mode only")
    print("5. View setup guide")
    print("6. Exit")
    
    while True:
        try:
            choice = input("\nEnter choice (1-6): ").strip()
            
            if choice == '1':
                print("\n🚀 Running automated setup...")
                os.system(f"{sys.executable} src/utils/setup_espn_draft.py")
                break
                
            elif choice == '2':
                print("\n📝 Manual Setup Instructions:")
                print("1. Edit src/config.py")
                print("2. Update these values:")
                print("   - LEAGUE_ID = your_league_id")
                print("   - ESPN_S2 = your_espn_s2_cookie")
                print("   - SWID = your_swid_cookie")
                print("   - YOUR_DRAFT_SLOT = your_position_minus_1")
                print("3. Run: python src/tests/test_espn_connection.py")
                break
                
            elif choice == '3':
                print("\n🎯 Manual Mode - No ESPN Configuration Required")
                print("This mode bypasses ESPN setup and only requires scoring type selection.")
                print()
                
                # Get scoring type
                scoring_type = set_scoring_type()
                
                # Configure manual mode
                if configure_manual_mode(scoring_type):
                    # Launch GUI
                    launch_manual_gui()
                else:
                    print("❌ Failed to configure manual mode")
                    return
                break
                
            elif choice == '4':
                print("\n🧪 Test Mode Setup:")
                print("1. Edit src/main.py")
                print("2. Set TEST_MODE = True")
                print("3. Run: python src/main.py")
                print("4. Use option 'A' to add mock picks")
                break
                
            elif choice == '5':
                print("\n📖 Opening setup guide...")
                if os.path.exists("ESPN_SETUP_GUIDE.md"):
                    with open("ESPN_SETUP_GUIDE.md", 'r') as f:
                        print(f.read())
                else:
                    print("Setup guide not found. Check README.md for instructions.")
                break
                
            elif choice == '6':
                print("Goodbye!")
                break
                
            else:
                print("Please enter 1-6")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        finally:
            # Always cleanup if manual mode was used
            if choice == '3':
                cleanup()

if __name__ == "__main__":
    main()
