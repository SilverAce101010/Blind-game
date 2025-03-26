import tkinter as tk
import random
import math

# Screen settings
WIDTH, HEIGHT = 800, 600
grid_size = 20  # Smaller grid size for a more complex maze
cols, rows = WIDTH // grid_size, HEIGHT // grid_size

# Player settings
player_size = grid_size // 1.5
player_x, player_y = grid_size + player_size // 2, grid_size + player_size // 2
player_speed = 3
movement = {"Up": False, "Down": False, "Left": False, "Right": False}

# Maze generation using Depth-First Search with stack-based iterative approach
maze = [[1 for _ in range(cols)] for _ in range(rows)]

def generate_maze():
    """ Improved iterative maze generator using DFS with occasional open rooms """
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
            if 0 < nx < cols-1 and 0 < ny < rows-1 and (nx, ny) not in visited:
                maze[cy + dy//2][cx + dx//2] = 0
                stack.append((nx, ny))
                visited.add((nx, ny))
                found = True
                break
        
        if not found:
            stack.pop()
    
    # Add occasional open rooms
    for _ in range(random.randint(3, 6)):
        room_x = random.randint(1, cols-3)
        room_y = random.randint(1, rows-3)
        room_width = random.randint(2, 4)
        room_height = random.randint(2, 4)
        for ry in range(room_y, min(room_y + room_height, rows-1)):
            for rx in range(room_x, min(room_x + room_width, cols-1)):
                maze[ry][rx] = 0

generate_maze()

# Create window
root = tk.Tk()
root.title("Maze Game")
canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="black")
canvas.pack()

# Precalculate the wall tiles
wall_tiles = []
for y in range(rows):
    for x in range(cols):
        if maze[y][x] == 1:
            wall_tiles.append((x, y))

# Define the lighting radius
LIGHT_RADIUS = 150  # Smaller radius for light to follow the player

def calculate_shading(x, y):
    """ Calculate shading based on player distance """
    distance = math.sqrt((player_x - (x * grid_size))**2 + (player_y - (y * grid_size))**2)
    shade_factor = min(1, distance / LIGHT_RADIUS)  # Normalize the shading factor to the light radius
    return f"#{int(255 * (1 - shade_factor)):02x}{int(255 * (1 - shade_factor)):02x}{int(255 * (1 - shade_factor)):02x}"

# Draw maze walls with initial shading
for x, y in wall_tiles:
    canvas.create_rectangle(
        x * grid_size, y * grid_size, (x + 1) * grid_size, (y + 1) * grid_size, fill="black", outline="black", tags="maze")

# Define the player shape (blue circle)
player = canvas.create_oval(player_x, player_y, player_x + player_size, player_y + player_size, fill="blue", tags="player")

def check_collision(x, y):
    """ Check if the new position collides with any wall """
    for x_wall, y_wall in wall_tiles:
        if (x_wall * grid_size < x + player_size and x < (x_wall + 1) * grid_size and
                y_wall * grid_size < y + player_size and y < (y_wall + 1) * grid_size):
            return True
    return False

def update_movement():
    global player_x, player_y
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
    if not check_collision(new_x, player_y):
        player_x = new_x
        canvas.move(player, dx, 0)
    if not check_collision(player_x, new_y):
        player_y = new_y
        canvas.move(player, 0, dy)

    # Clear all previous lighting and reset canvas to black
    canvas.delete("light")

    # Update lighting for both walls and the ground (background)
    for y in range(rows):
        for x in range(cols):
            dist = math.sqrt((player_x - (x * grid_size))**2 + (player_y - (y * grid_size))**2)
            # For the walls (maze)
            if maze[y][x] == 1:
                if dist <= LIGHT_RADIUS:
                    color = "green"  # Walls in light are green
                else:
                    color = "black"  # Walls outside the light are black
                canvas.create_rectangle(x * grid_size, y * grid_size, (x + 1) * grid_size, (y + 1) * grid_size, 
                                         fill=color, outline=color, tags="light")
            # For the ground (background)
            elif dist <= LIGHT_RADIUS:
                background_color = calculate_shading(x, y)
                # Set background color with a lighter shade based on proximity to player
                canvas.create_rectangle(x * grid_size, y * grid_size, (x + 1) * grid_size, (y + 1) * grid_size, 
                                         fill=background_color, outline=background_color, tags="light")

    # Delete the previous player circle (if it exists) and draw the new one
    canvas.delete("player")  # Delete the previous player circle
    # Draw the player again at the new position
    canvas.create_oval(player_x, player_y, player_x + player_size, player_y + player_size, fill="blue", tags="player")

    root.after(16, update_movement)  # Smooth movement with a frame update every 16ms (~60FPS)

def on_key_press(event):
    if event.keysym in ("w", "Up"):
        movement["Up"] = True
    elif event.keysym in ("s", "Down"):
        movement["Down"] = True
    elif event.keysym in ("a", "Left"):
        movement["Left"] = True
    elif event.keysym in ("d", "Right"):
        movement["Right"] = True

def on_key_release(event):
    if event.keysym in ("w", "Up"):
        movement["Up"] = False
    elif event.keysym in ("s", "Down"):
        movement["Down"] = False
    elif event.keysym in ("a", "Left"):
        movement["Left"] = False
    elif event.keysym in ("d", "Right"):
        movement["Right"] = False

# Bind key events
root.bind("<KeyPress>", on_key_press)
root.bind("<KeyRelease>", on_key_release)

update_movement()
root.mainloop()
