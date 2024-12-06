import os
import subprocess
import json

# Configuration
WALLPAPERS_FOLDER = "/wallpapers"
STATE_FILE = "/wallpaper_state.json"
SUPPORTED_FORMATS = (".jpg", ".jpeg", ".png", ".bmp")

def load_state():
    """Load the saved state from the JSON file."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {"theme_index": 0, "wallpaper_index": 0}

def save_state(state):
    """Save the current state to the JSON file."""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

def load_wallpapers(theme_path):
    """Load all wallpapers in the specified theme directory."""
    return sorted(
        [os.path.join(theme_path, f) for f in os.listdir(theme_path) if f.lower().endswith(SUPPORTED_FORMATS)]
    )

def set_wallpaper(file_path):
    """Set the wallpaper using qdbus6."""
    command = [
        "qdbus6",
        "org.kde.plasmashell",
        "/PlasmaShell",
        "org.kde.PlasmaShell.evaluateScript",
        f"""
        var allDesktops = desktops();
        for (i = 0; i < allDesktops.length; i++) {{
            d = allDesktops[i];
            d.wallpaperPlugin = "org.kde.image";
            d.currentConfigGroup = Array("Wallpaper", "org.kde.image", "General");
            d.writeConfig("Image", "file://{file_path}");
        }}
        """
    ]
    subprocess.run(command)

# Main logic
state = load_state()
theme_folders = sorted(
    [os.path.join(WALLPAPERS_FOLDER, d) for d in os.listdir(WALLPAPERS_FOLDER) if os.path.isdir(os.path.join(WALLPAPERS_FOLDER, d))]
)

if theme_folders:
    theme_path = theme_folders[state["theme_index"]]
    wallpapers = load_wallpapers(theme_path)

    if wallpapers:
        state["wallpaper_index"] -= 1
        if state["wallpaper_index"] < 0:
            state["theme_index"] = (state["theme_index"] - 1) % len(theme_folders)
            theme_path = theme_folders[state["theme_index"]]
            wallpapers = load_wallpapers(theme_path)
            state["wallpaper_index"] = len(wallpapers) - 1

        set_wallpaper(wallpapers[state["wallpaper_index"]])
        save_state(state)
