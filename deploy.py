import os
import sys
import json
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
    print("🚀 Team Ninja Pro - 1-Click Deployment & Auto-Updater Setup")
    print("=" * 60)
    
    print("Step 1: GitHub Setup")
    username = input("Enter your GitHub username: ").strip()
    print("\nStep 2: Generate Access Token")
    print("Open this link: https://github.com/settings/tokens/new?scopes=repo,workflow")
    print("Click 'Generate token' and copy it.")
    token = input("Paste your token here: ").strip()
    
    repo_name = "team-ninja-pro-app"
    
    # 1. Create Repo via API (or continue if it exists)
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
    if res.status_code == 201:
        print("✅ Repository created successfully!")
    elif res.status_code == 422:
        print("⚠️ Repository already exists. Continuing...")
    else:
        print("❌ Failed to create repository:", res.json())
        return

    # 2. Initialize Git and Force Push
    print("\nInitializing Git and pushing code...")
    if not os.path.exists(".git"):
        run_cmd("git init")
    
    # Create .gitignore
    with open(".gitignore", "w") as f:
        f.write("node_modules/\nbackend/__pycache__/\nbackend/venv/\nTeamNinjaDownloads/\nrelease/\nbuild/\ndist/\ncustom_icon.png\nconfig.json\n")
    
    run_cmd("git add .")
    run_cmd('git commit -m "Initial Release"')
    run_cmd("git branch -M main")
    
    remote_url = f"https://{token}@github.com/{username}/{repo_name}.git"
    run_cmd("git remote remove origin")
    run_cmd(f"git remote add origin {remote_url}")
    
    print("Force pushing code to GitHub (this might take a minute)...")
    # Using --force to bypass any branch protection/history issues
    push_result = subprocess.run("git push -u origin main --force", shell=True, text=True, capture_output=True)
    if push_result.returncode != 0:
        print("❌ Git push failed. Error details:")
        print(push_result.stderr)
        return
    else:
        print("✅ Code successfully pushed to GitHub!")

    # 3. Update package.json with user's repo details, version, and NEW APP NAME
    print("\nUpdating package.json with your GitHub details and App Name...")
    with open("package.json", "r") as f:
        pkg = json.load(f)
    
    current_version = pkg.get("version", "1.0.0")
    print(f"Current version is {current_version}.")
    new_version = input("Enter new version number (or press Enter to keep current): ").strip()
    if not new_version:
        new_version = current_version
    
    pkg["version"] = new_version
    pkg["name"] = "ytdownloader-desktop" # Internal package name
    pkg["build"]["productName"] = "YTDownloader" # THIS CHANGES THE EXE NAME
    pkg["build"]["appId"] = "com.ytdownloader.app"
    pkg["build"]["publish"] = {
        "provider": "github",
        "owner": username,
        "repo": repo_name
    }
    
    with open("package.json", "w") as f:
        json.dump(pkg, f, indent=2)
    
    # Commit the updated package.json
    run_cmd("git add package.json")
    run_cmd('git commit -m "Update version and app name"')
    subprocess.run("git push", shell=True, text=True, capture_output=True)

    # 4. Build the App
    print("\nBuilding the YTDownloader App (this takes 3-5 minutes)...")
    subprocess.run("npm install", shell=True)
    
    build_process = subprocess.run("npm run build:win", shell=True)
    if build_process.returncode != 0:
        print("❌ Build failed. Please check the errors above.")
        return

    # 5. Find the built files in the 'dist' folder
    dist_dir = "dist"
    if not os.path.exists(dist_dir):
        print("❌ dist folder not found. Build might have failed.")
        return

    exe_path = None
    yml_path = None
    for file in os.listdir(dist_dir):
        if file.endswith(".exe") and "Setup" in file:
            exe_path = os.path.join(dist_dir, file)
        elif file.endswith(".yml"):
            yml_path = os.path.join(dist_dir, file)

    if not exe_path or not yml_path:
        print("❌ Could not find .exe or .yml in the dist folder.")
        return

    # 6. Create GitHub Release and Upload Assets
    tag_name = f"v{new_version}"
    
    print(f"\nCreating GitHub Release {tag_name}...")
    release_data = {
        "tag_name": tag_name,
        "name": f"Release {new_version}",
        "body": "Latest update for YTDownloader.",
        "draft": False,
        "prerelease": False
    }
    
    res = requests.post(
        f"https://api.github.com/repos/{username}/{repo_name}/releases",
        headers=headers,
        json=release_data
    )
    
    if res.status_code == 201:
        release_info = res.json()
        upload_url = release_info["upload_url"].replace("{?name,label}", "")
        print("✅ Release created!")
    else:
        print("❌ Failed to create release:", res.json())
        return

    # Upload .exe
    print(f"\nUploading {os.path.basename(exe_path)} (this might take a few minutes)...")
    with open(exe_path, "rb") as f:
        res = requests.post(
            f"{upload_url}?name={os.path.basename(exe_path)}",
            headers={**headers, "Content-Type": "application/octet-stream"},
            data=f
        )
    if res.status_code == 201:
        print("✅ App uploaded!")
    else:
        print("❌ Failed to upload app:", res.json())

    # Upload .yml (Crucial for auto-updates)
    print(f"Uploading {os.path.basename(yml_path)}...")
    with open(yml_path, "rb") as f:
        res = requests.post(
            f"{upload_url}?name=latest.yml",
            headers={**headers, "Content-Type": "text/yaml"},
            data=f
        )
    if res.status_code == 201:
        print("✅ Update manifest uploaded!")
    else:
        print("❌ Failed to upload manifest:", res.json())

    print("\n" + "=" * 60)
    print("🎉 DEPLOYMENT COMPLETE! 🎉")
    print(f"Your app is now hosted at: https://github.com/{username}/{repo_name}")
    print("\nTo distribute: Go to your GitHub repo, click 'Releases', and download the YTDownloader Setup .exe to send to your friends.")
    print("=" * 60)

if __name__ == "__main__":
    main()