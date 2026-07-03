import os
import shutil
import subprocess
import sys

def fix_html_paths():
    """Forces relative paths in index.html to fix Electron ERR_FILE_NOT_FOUND"""
    index_html_path = 'build/index.html'
    if os.path.exists(index_html_path):
        with open(index_html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace absolute paths with relative paths
        content = content.replace('href="/', 'href="./')
        content = content.replace('src="/', 'src="./')
        
        with open(index_html_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ Forced relative paths in index.html!")

def main():
    print("🚀 Quick Local Build & Test (No GitHub) - With Path Fix")
    print("=" * 60)

    # 1. Compile Python Backend
    print("\n1. Compiling Python Backend...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
    if os.path.exists('backend.exe'): os.remove('backend.exe')
    if os.path.exists('backend/dist'): shutil.rmtree('backend/dist')
    if os.path.exists('backend/build'): shutil.rmtree('backend/build')
    
    os.chdir('backend')
    subprocess.run([sys.executable, "-m", "PyInstaller", "--onefile", "--name", "backend", "app.py"], check=True)
    os.chdir('..')
    shutil.copy('backend/dist/backend.exe', 'backend.exe')
    print("✅ Backend compiled!")

    # 2. Compile React UI
    print("\n2. Compiling React UI...")
    # Use --base=./ to tell Vite to use relative paths
    subprocess.run("npx vite build --base=./", shell=True, check=True)
    
    # Force fix the HTML file just in case Vite ignores the config
    fix_html_paths()
    print("✅ React UI compiled!")

    # 3. Build Electron App (Unpacked, no installer, no GitHub)
    print("\n3. Building Electron App (Local Unpacked)...")
    if os.path.exists('dist'): shutil.rmtree('dist')
    subprocess.run("npx electron-builder --win --dir", shell=True, check=True)
    print("✅ Electron app built!")

    # 4. Launch the app
    print("\n4. Launching YTDownloader for testing...")
    exe_path = "dist/win-unpacked/YTDownloader.exe"
    if os.path.exists(exe_path):
        subprocess.run(f'"{exe_path}"', shell=True)
    else:
        print("❌ Could not find YTDownloader.exe in dist/win-unpacked/")

if __name__ == "__main__":
    main()