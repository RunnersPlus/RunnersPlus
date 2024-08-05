import subprocess
import sys

def uninstall_all_packages():
    try:
        # Get a list of installed packages
        result = subprocess.run([sys.executable, '-m', 'pip', 'freeze'], stdout=subprocess.PIPE)
        installed_packages = result.stdout.decode().split('\n')

        # Uninstall each package
        for package in installed_packages:
            if package.strip():
                subprocess.run([sys.executable, '-m', 'pip', 'uninstall', '-y', package.split('==')[0]])
        
        print("All packages have been uninstalled successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    uninstall_all_packages()