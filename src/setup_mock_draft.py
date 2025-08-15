"""
Quick setup script for ESPN Mock Draft
"""

import os
import sys

def main():
    print("🏈 ESPN Mock Draft Setup")
    print("=" * 40)
    print()
    
    print("Choose your setup method:")
    print("1. Automated setup (recommended)")
    print("2. Manual setup")
    print("3. Test mode only")
    print("4. View setup guide")
    print("5. Exit")
    
    while True:
        try:
            choice = input("\nEnter choice (1-5): ").strip()
            
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
                print("\n🧪 Test Mode Setup:")
                print("1. Edit src/main.py")
                print("2. Set TEST_MODE = True")
                print("3. Run: python src/main.py")
                print("4. Use option 'A' to add mock picks")
                break
                
            elif choice == '4':
                print("\n📖 Opening setup guide...")
                if os.path.exists("ESPN_SETUP_GUIDE.md"):
                    with open("ESPN_SETUP_GUIDE.md", 'r') as f:
                        print(f.read())
                else:
                    print("Setup guide not found. Check README.md for instructions.")
                break
                
            elif choice == '5':
                print("Goodbye!")
                break
                
            else:
                print("Please enter 1-5")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break

if __name__ == "__main__":
    main()
