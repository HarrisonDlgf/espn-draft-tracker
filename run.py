import sys
import os

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

def get_current_pick():
    """Get the current draft pick number from the user"""
    print("\n📊 Draft Position Setup")
    print("=" * 40)
    print("What pick number are you drafting on?")
    print("(e.g., 1 = first pick, 11 = 11th pick, etc.)")
    print()
    
    while True:
        try:
            pick = input("Enter current pick number: ").strip()
            pick_num = int(pick)
            
            if pick_num < 1:
                print("Pick number must be 1 or higher")
                continue
                
            print(f"✅ Set to pick #{pick_num}")
            return pick_num
            
        except ValueError:
            print("Please enter a valid number")
        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(0)

def configure_manual_mode(scoring_type, current_pick):
    """Configure the system for manual mode"""
    print(f"\n Configuring manual mode for {scoring_type.upper()} at pick #{current_pick}...")
    
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
    print("• Position-first recommendations with urgency analysis")
    print("• Current roster display")
    print("• Color-coded tiers and urgency levels")
    print("• Auto-refresh after adding players")
    print()
    print("Use the '➕ Add Pick' button to add players manually")
    print("Use the '👥 Show Roster' button to view your current team")
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
    print("🏈 ESPN Draft Tracker")
    print("=" * 30)
    print("Choose your interface:")
    print("1. GUI Version (Recommended)")
    print("2. Console Version")
    print("3. Manual Mode (No ESPN config needed)")
    print("4. Exit")
    
    while True:
        try:
            choice = input("\nEnter choice (1-4): ").strip()
            
            if choice == '1':
                print("Launching GUI version...")
                os.system(f"{sys.executable} src/main_gui.py")
                break
            elif choice == '2':
                print("Launching console version...")
                os.system(f"{sys.executable} src/main.py")
                break
            elif choice == '3':
                print("\n🎯 Manual Mode - No ESPN Configuration Required")
                print("This mode bypasses ESPN setup and only requires scoring type selection.")
                print()
                
                # Get scoring type
                scoring_type = set_scoring_type()
                
                # Get current pick
                current_pick = get_current_pick()
                
                # Configure manual mode
                if configure_manual_mode(scoring_type, current_pick):
                    # Launch GUI
                    launch_manual_gui()
                else:
                    print("❌ Failed to configure manual mode")
                    return
                break
            elif choice == '4':
                print("Goodbye!")
                break
            else:
                print("Please enter 1-4")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        finally:
            # Always cleanup if manual mode was used
            if choice == '3':
                cleanup()

if __name__ == "__main__":
    main()
