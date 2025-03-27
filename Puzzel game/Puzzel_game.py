import tkinter as tk
import random
import math

# Screen settings
WIDTH, HEIGHT = 800, 600  # Increased screen size for a larger maze
GRID_SIZE = 20  # Grid size for the maze
MAZE_COLS, MAZE_ROWS = 100, 75  # Larger maze dimensions

# Create main window
root = tk.Tk()
root.title("Maze Game")
root.geometry(f"{WIDTH + 200}x{HEIGHT}")  # Adjust window size for side panel

# Frame for the maze (Canvas)
maze_frame = tk.Frame(root)
maze_frame.pack(side=tk.LEFT)

# Create Canvas for the maze
canvas = tk.Canvas(maze_frame, width=WIDTH, height=HEIGHT, bg="black")
canvas.pack()

# Frame for the side panel
side_panel = tk.Frame(root, width=200, height=HEIGHT, bg="gray")
side_panel.pack(side=tk.RIGHT, fill=tk.Y)

# Add Text widget to the side panel for displaying text
text_display = tk.Text(side_panel, width=30, height=30, bg="light gray", fg="black", font=("Helvetica", 12))
text_display.pack(side=tk.BOTTOM, padx=10, pady=10)  # Pack the text at the bottom of the panel

# Display Text within the widget and ensure it scrolls to the bottom
def display_text(text):
    text_display.insert(tk.END, text + '\n')  # Adds new text at the end with a newline
    text_display.yview_moveto(1.0)  # Scrolls to the bottom to show the latest text

# Example of adding text to display
display_text("Testing")  # Initially display "Testing"


# Player settings
player_size = int(GRID_SIZE // 1.5)
player_x, player_y = GRID_SIZE + player_size // 2, GRID_SIZE + player_size // 2
player_speed = 4
movement = {"Up": False, "Down": False, "Left": False, "Right": False}

# Maze generation using Depth-First Search
maze = [[1 for _ in range(MAZE_COLS)] for _ in range(MAZE_ROWS)]

def generate_maze():
    """ Generate a random maze using DFS """
    stack = [(1, 1)]
    visited = set(stack)
    directions = [(0, -2), (0, 2), (-2, 0), (2, 0)]
    
    while stack:
        cx, cy = stack[-1]
        maze[cy][cx] = 0
        random.shuffle(directions)
        found = False
        
        for dx, dy in directions:
            nx, ny = cx + dx, cy + dy
            if 0 < nx < MAZE_COLS-1 and 0 < ny < MAZE_ROWS-1 and (nx, ny) not in visited:
                maze[cy + dy//2][cx + dx//2] = 0
                stack.append((nx, ny))
                visited.add((nx, ny))
                found = True
                break
        
        if not found:
            stack.pop()

generate_maze()

# Precalculate wall positions
wall_tiles = {(x, y) for y in range(MAZE_ROWS) for x in range(MAZE_COLS) if maze[y][x] == 1}

# Define the lighting radius
LIGHT_RADIUS = 125

def calculate_shading(x, y, is_wall):
    """ Lighting effect based on player distance, applies to walls and ground differently """
    if debug_mode:
        return "#808080" if is_wall else "#eeeeee"  # Walls remain white, floors a bit lighter in debug mode
    
    distance = math.sqrt((player_x - (x * GRID_SIZE))**2 + (player_y - (y * GRID_SIZE))**2)
    shade_factor = min(1, distance / LIGHT_RADIUS)
    if distance > LIGHT_RADIUS:
        return "#000000"  # Completely black if outside the light radius
    if is_wall:
        color_value = max(30, 100 - int(100 * shade_factor))  # Walls stay darker
    else:
        color_value = max(0, 255 - int(255 * shade_factor))  # Floors get full range of light
    return f"#{color_value:02x}{color_value:02x}{color_value:02x}"

# Random starting position in an open space
floor_tiles = [(x, y) for y in range(MAZE_ROWS) for x in range(MAZE_COLS) if maze[y][x] == 0]
player_x, player_y = random.choice(floor_tiles)
player_x = int(player_x * GRID_SIZE + player_size // 2)
player_y = int(player_y * GRID_SIZE + player_size // 2)

# Camera settings
camera_x, camera_y = 0.0, 0.0  # Camera positions should be floats for smooth movement
camera_speed = 10.0  # Camera speed (higher = faster follow)
camera_x_target, camera_y_target = float(player_x), float(player_y)  # Camera target positions

def can_move(new_x, new_y):
    """Check if the player can move to the new position without colliding with walls"""
    left = (new_x - player_size // 2) // GRID_SIZE
    right = (new_x + player_size // 2) // GRID_SIZE
    top = (new_y - player_size // 2) // GRID_SIZE
    bottom = (new_y + player_size // 2) // GRID_SIZE
    return (left, top) not in wall_tiles and (right, top) not in wall_tiles and \
           (left, bottom) not in wall_tiles and (right, bottom) not in wall_tiles

def update_movement():
    global player_x, player_y, camera_x, camera_y, camera_x_target, camera_y_target
    dx, dy = 0, 0
    if movement["Up"]:
        dy -= player_speed
    if movement["Down"]:
        dy += player_speed
    if movement["Left"]:
        dx -= player_speed
    if movement["Right"]:
        dx += player_speed
    
    new_x, new_y = player_x + dx, player_y + dy
    if can_move(new_x, player_y):
        player_x = int(new_x)
    if can_move(player_x, new_y):
        player_y = int(new_y)
    
    # Set the camera target to the player's position
    camera_x_target = float(player_x - WIDTH // 2)  # Ensure float type for target position
    camera_y_target = float(player_y - HEIGHT // 2)
    
    # Update the camera position gradually towards the target (smooth camera movement)
    camera_x += (camera_x_target - camera_x) / camera_speed
    camera_y += (camera_y_target - camera_y) / camera_speed
    
    redraw()
    root.after(16, update_movement)

def redraw():
    """ Redraw the visible portion of the maze and player """
    canvas.delete("all")
    start_x, start_y = max(0, int(camera_x // GRID_SIZE)), max(0, int(camera_y // GRID_SIZE))
    end_x, end_y = min(MAZE_COLS, int((camera_x + WIDTH) // GRID_SIZE)), min(MAZE_ROWS, int((camera_y + HEIGHT) // GRID_SIZE))
    
    # Optimized rendering loop for large mazes
    for y in range(start_y, end_y + 1):
        for x in range(start_x, end_x + 1):
            is_wall = (x, y) in wall_tiles
            color = calculate_shading(x, y, is_wall)
            canvas.create_rectangle(
                x * GRID_SIZE - camera_x, y * GRID_SIZE - camera_y,
                (x + 1) * GRID_SIZE - camera_x, (y + 1) * GRID_SIZE - camera_y,
                fill=color, outline=color)
    
    # Draw the player
    canvas.create_oval(
        player_x - player_size // 2 - camera_x, player_y - player_size // 2 - camera_y,
        player_x + player_size // 2 - camera_x, player_y + player_size // 2 - camera_y,
        fill="blue")

def on_key_press(event):
    if event.keysym in ("w", "Up"):
        movement["Up"] = True
    elif event.keysym in ("s", "Down"):
        movement["Down"] = True
    elif event.keysym in ("a", "Left"):
        movement["Left"] = True
    elif event.keysym in ("d", "Right"):
        movement["Right"] = True
    elif event.keysym == "b":  # Toggle debug mode on 'b' key press
        global debug_mode
        debug_mode = not debug_mode

def on_key_release(event):
    if event.keysym in ("w", "Up"):
        movement["Up"] = False
    elif event.keysym in ("s", "Down"):
        movement["Down"] = False
    elif event.keysym in ("a", "Left"):
        movement["Left"] = False
    elif event.keysym in ("d", "Right"):
        movement["Right"] = False

# Initialize debug_mode flag
debug_mode = False

# Bind keys
root.bind("<KeyPress>", on_key_press)
root.bind("<KeyRelease>", on_key_release)

update_movement()
root.mainloop()
