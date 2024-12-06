import os
import subprocess
import json
from pynput import keyboard

# Path to the main wallpapers folder
WALLPAPERS_FOLDER = "wallpapers"
SUPPORTED_FORMATS = (".jpg", ".jpeg", ".png", ".bmp")  # Add other formats if needed

# Path to store the state (theme and wallpaper index)
STATE_FILE = "wallpaper_state.json"

# Fetch subfolders as themes
theme_folders = [os.path.join(WALLPAPERS_FOLDER, d) for d in os.listdir(WALLPAPERS_FOLDER)
                 if os.path.isdir(os.path.join(WALLPAPERS_FOLDER, d))]
theme_folders.sort()  # Sort themes alphabetically

# Debug: Print theme folders found
print(f"Themes found: {theme_folders}")

# Initialize state variables
current_theme_index = 0
current_wallpaper_index = 0
current_wallpapers = []

# Load the saved state from file (if it exists)
def load_state():
    global current_theme_index, current_wallpaper_index
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
                current_theme_index = state.get("theme_index", 0)
                current_wallpaper_index = state.get("wallpaper_index", 0)
                print(f"Loaded state: Theme {current_theme_index}, Wallpaper {current_wallpaper_index}")
        except Exception as e:
            print(f"Error loading state: {e}")

# Save the current state to the file
def save_state():
    try:
        with open(STATE_FILE, 'w') as f:
            state = {
                "theme_index": current_theme_index,
                "wallpaper_index": current_wallpaper_index
            }
            json.dump(state, f)
            print(f"State saved: Theme {current_theme_index}, Wallpaper {current_wallpaper_index}")
    except Exception as e:
        print(f"Error saving state: {e}")

def load_wallpapers_for_theme(theme_index):
    """Load wallpapers for a given theme index."""
    global current_wallpapers
    theme_path = theme_folders[theme_index]
    print(f"Loading wallpapers for theme: {theme_path}")  # Debug
    current_wallpapers = [os.path.join(theme_path, f) for f in os.listdir(theme_path)
                          if f.lower().endswith(SUPPORTED_FORMATS)]
    current_wallpapers.sort()  # Sort alphabetically

    # Debug: Print wallpapers found
    print(f"Wallpapers in theme '{theme_path}': {current_wallpapers}")
    if not current_wallpapers:
        print(f"No wallpapers found in theme: {theme_path}")


# Load wallpapers for the saved theme at the beginning
load_state()
if theme_folders:
    load_wallpapers_for_theme(current_theme_index)
else:
    print("No themes found in the main folder.")

def set_wallpaper(file_path):
    """Set the wallpaper using qdbus."""
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


def change_wallpaper(direction):
    """Change wallpaper within or across themes."""
    global current_theme_index, current_wallpaper_index

    if not theme_folders:
        print("No themes found.")
        return

    if not current_wallpapers:
        print("No wallpapers in the current theme.")
        return

    # Update the wallpaper index
    current_wallpaper_index += direction

    # Handle moving between wallpapers
    if current_wallpaper_index >= len(current_wallpapers):
        current_wallpaper_index = 0  # Reset to first wallpaper in the next theme
        current_theme_index = (current_theme_index + 1) % len(theme_folders)  # Next theme
        load_wallpapers_for_theme(current_theme_index)

    elif current_wallpaper_index < 0:
        current_theme_index = (current_theme_index - 1) % len(theme_folders)  # Previous theme
        load_wallpapers_for_theme(current_theme_index)
        current_wallpaper_index = len(current_wallpapers) - 1  # Last wallpaper in the previous theme

    # Set the wallpaper
    set_wallpaper(current_wallpapers[current_wallpaper_index])
    print(f"Theme: {os.path.basename(theme_folders[current_theme_index])}, "
          f"Wallpaper: {os.path.basename(current_wallpapers[current_wallpaper_index])}")

    # Save the new state
    save_state()


def change_theme(direction):
    """Switch to the next or previous theme."""
    global current_theme_index, current_wallpaper_index

    if not theme_folders:
        print("No themes found.")
        return

    # Move to the next or previous theme and set the first wallpaper
    current_theme_index += direction
    if current_theme_index >= len(theme_folders):
        current_theme_index = 0  # Loop back to the first theme
    elif current_theme_index < 0:
        current_theme_index = len(theme_folders) - 1  # Loop to the last theme

    # Reset wallpaper to the first one in the new theme
    current_wallpaper_index = 0
    load_wallpapers_for_theme(current_theme_index)
    set_wallpaper(current_wallpapers[current_wallpaper_index])
    print(f"Switched to theme: {os.path.basename(theme_folders[current_theme_index])}, "
          f"Wallpaper: {os.path.basename(current_wallpapers[current_wallpaper_index])}")

    # Save the new state
    save_state()


# Track currently pressed keys
pressed_keys = set()


def on_press(key):
    """Handle key presses."""
    try:
        # Add the pressed key to the set
        pressed_keys.add(key)

        # Check for Ctrl + Shift + Left or Right (for wallpaper change)
        if (keyboard.Key.ctrl_l in pressed_keys or keyboard.Key.ctrl_r in pressed_keys) and \
           (keyboard.Key.shift in pressed_keys):

            if key == keyboard.Key.left:
                change_wallpaper(-1)  # Go backward
            elif key == keyboard.Key.right:
                change_wallpaper(1)  # Go forward

        # Check for Ctrl + Left Alt + Left or Right (for theme change)
        if (keyboard.Key.ctrl_l in pressed_keys or keyboard.Key.ctrl_r in pressed_keys) and \
           (keyboard.Key.alt_l in pressed_keys or keyboard.Key.alt_r in pressed_keys):

            if key == keyboard.Key.left:
                change_theme(-1)  # Go to previous theme
            elif key == keyboard.Key.right:
                change_theme(1)  # Go to next theme

    except Exception as e:
        print(f"Error: {e}")


def on_release(key):
    """Handle key releases."""
    try:
        # Remove the released key from the set
        if key in pressed_keys:
            pressed_keys.remove(key)
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Main function to listen for keypresses."""
    print("Listening for Ctrl+Shift+Arrow key presses... (left/right to change wallpaper)")
    print("Listening for Ctrl+Alt+Arrow key presses... (left/right to change theme)")
    print(f"Current wallpaper folder: {WALLPAPERS_FOLDER}")
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()
    listener.join()


if __name__ == "__main__":
    main()
