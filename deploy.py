import os
import sys
import json
import shutil
import subprocess
import requests

# Ensure required packages are installed
try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

def run_cmd(cmd):
    print(f">>> {cmd}")
    return subprocess.run(cmd, shell=True, text=True, capture_output=True)

def main():
    print("🚀 YTDownloader - 1-Click Standalone Deployment")
    print("=" * 60)
    
    # 1. Compile Python Backend
    print("Step 1: Compiling Python Backend into standalone .exe...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    if os.path.exists('backend.exe'): os.remove('backend.exe')
    if os.path.exists('backend/dist'): shutil.rmtree('backend/dist')
    if os.path.exists('backend/build'): shutil.rmtree('backend/build')
    
    os.chdir('backend')
    subprocess.run([sys.executable, "-m", "PyInstaller", "--onefile", "--name", "backend", "app.py"], check=True)
    os.chdir('..')
    shutil.copy('backend/dist/backend.exe', 'backend.exe')
    print("✅ Backend compiled!")

    # 2. GitHub Setup
    print("\nStep 2: GitHub Setup")
    username = input("Enter your GitHub username: ").strip()
    print("Open this link: https://github.com/settings/tokens/new?scopes=repo,workflow")
    print("Click 'Generate token' and copy it.")
    token = input("Paste your token here: ").strip()
    
    repo_name = "team-ninja-pro-app"
    
    print(f"\nChecking repository '{repo_name}' on GitHub...")
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "name": repo_name,
        "private": False,
        "description": "YTDownloader Pro"
    }
    res = requests.post("https://api.github.com/user/repos", headers=headers, json=data)
    if res.status_code == 201: print("✅ Repository created successfully!")
    elif res.status_code == 422: print("⚠️ Repository already exists. Continuing...")
    else: return print("❌ Failed to create repository:", res.json())

    # 3. Push Code to GitHub
    print("\nInitializing Git and pushing code...")
    if not os.path.exists(".git"): run_cmd("git init")
    
    with open(".gitignore", "w") as f:
        f.write("node_modules/\nbackend/__pycache__/\nbackend/venv/\nTeamNinjaDownloads/\nrelease/\nbuild/\ndist/\nbackend/dist/\nbackend/build/\nbackend.exe\n")
    
    run_cmd("git add .")
    run_cmd('git commit -m "Update code"')
    run_cmd("git branch -M main")
    
    remote_url = f"https://{token}@github.com/{username}/{repo_name}.git"
    run_cmd("git remote remove origin")
    run_cmd(f"git remote add origin {remote_url}")
    
    print("Force pushing code to GitHub...")
    push_result = subprocess.run("git push -u origin main --force", shell=True, text=True, capture_output=True)
    if push_result.returncode != 0: return print("❌ Git push failed:", push_result.stderr)
    print("✅ Code successfully pushed to GitHub!")

    # 4. Update Version
    print("\nUpdating package.json version...")
    with open("package.json", "r") as f: pkg = json.load(f)
    
    current_version = pkg.get("version", "1.0.0")
    print(f"Current version is {current_version}.")
    new_version = input("Enter new version number (e.g., 1.0.1): ").strip()
    if not new_version: new_version = current_version
    
    pkg["version"] = new_version
    pkg["build"]["publish"] = {"provider": "github", "owner": username, "repo": repo_name}
    
    with open("package.json", "w") as f: json.dump(pkg, f, indent=2)
    
    run_cmd("git add package.json")
    run_cmd('git commit -m "Update version"')
    subprocess.run("git push", shell=True, text=True, capture_output=True)

    # 5. Build Electron App
    print("\nStep 3: Building the YTDownloader Desktop App (this takes 3-5 minutes)...")
    subprocess.run("npm install", shell=True)
    build_process = subprocess.run("npm run build:win", shell=True)
    if build_process.returncode != 0: return print("❌ Build failed.")

    # 6. Find Built Files
    dist_dir = "dist"
    if not os.path.exists(dist_dir): return print("❌ dist folder not found.")
    
    exe_path = None
    yml_path = None
    for file in os.listdir(dist_dir):
        if file.endswith(".exe") and "Setup" in file: exe_path = os.path.join(dist_dir, file)
        elif file.endswith(".yml"): yml_path = os.path.join(dist_dir, file)

    if not exe_path or not yml_path: return print("❌ Could not find .exe or .yml in dist folder.")

    # 7. Create GitHub Release
    tag_name = f"v{new_version}"
    print(f"\nCreating GitHub Release {tag_name}...")
    release_data = {"tag_name": tag_name, "name": f"Release {new_version}", "body": "Latest update for YTDownloader.", "draft": False, "prerelease": False}
    
    res = requests.post(f"https://api.github.com/repos/{username}/{repo_name}/releases", headers=headers, json=release_data)
    if res.status_code == 201:
        release_info = res.json()
        upload_url = release_info["upload_url"].replace("{?name,label}", "")
        print("✅ Release created!")
    else: return print("❌ Failed to create release:", res.json())

    # 8. Upload Assets
    print(f"\nUploading {os.path.basename(exe_path)}...")
    with open(exe_path, "rb") as f:
        res = requests.post(f"{upload_url}?name={os.path.basename(exe_path)}", headers={**headers, "Content-Type": "application/octet-stream"}, data=f)
    if res.status_code == 201: print("✅ App uploaded!")
    else: print("❌ Failed to upload app:", res.json())

    print(f"Uploading {os.path.basename(yml_path)}...")
    with open(yml_path, "rb") as f:
        res = requests.post(f"{upload_url}?name=latest.yml", headers={**headers, "Content-Type": "text/yaml"}, data=f)
    if res.status_code == 201: print("✅ Update manifest uploaded!")
    else: print("❌ Failed to upload manifest:", res.json())

    print("\n" + "=" * 60)
    print("🎉 DEPLOYMENT COMPLETE! 🎉")
    print(f"Your standalone app is hosted at: https://github.com/{username}/{repo_name}")
    print("Users can download the .exe and run it without needing Python installed!")
    print("=" * 60)

if __name__ == "__main__":
    main()