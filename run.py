import sys
import os

def main():
    print("🏈 ESPN Draft Tracker")
    print("=" * 30)
    print("Choose your interface:")
    print("1. GUI Version (Recommended)")
    print("2. Console Version")
    print("3. Exit")
    
    while True:
        try:
            choice = input("\nEnter choice (1-3): ").strip()
            
            if choice == '1':
                print("Launching GUI version...")
                os.system(f"{sys.executable} src/main_gui.py")
                break
            elif choice == '2':
                print("Launching console version...")
                os.system(f"{sys.executable} src/main.py")
                break
            elif choice == '3':
                print("Goodbye!")
                break
            else:
                print("Please enter 1, 2, or 3")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break

if __name__ == "__main__":
    main()
