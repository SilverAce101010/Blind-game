import tkinter as tk
import random
import math
import heapq

# Screen settings
WIDTH, HEIGHT = 800, 600  # Increased screen size for a larger maze
GRID_SIZE = 20  # Grid size for the maze
MAZE_COLS, MAZE_ROWS = 100, 100  # Larger maze dimensions

# Initialize game settings
ghost_mode = False
debug_mode = False

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

# Add Canvas widget for the bar above the text widget
bar_canvas = tk.Canvas(side_panel, width=200, height=20, bg="white")
bar_canvas.pack(side=tk.TOP, padx=10, pady=10)

# Add Text widget to the side panel for displaying text
text_display = tk.Text(side_panel, width=30, height=30, bg="light gray", fg="black", font=("Helvetica", 12))
text_display.pack(side=tk.BOTTOM, padx=10, pady=10)  # Pack the text at the bottom of the panel

# Display Text within the widget and ensure it scrolls to the bottom
def display_text(text):
    text_display.insert(tk.END, text + '\n')  # Adds new text at the end with a newline
    text_display.yview_moveto(1.0)  # Scrolls to the bottom to show the latest text

display_text("You: Where am I...")

# Player settings
player_size = int(GRID_SIZE // 1.5)
player_x, player_y = GRID_SIZE + player_size // 2, GRID_SIZE + player_size // 2
player_speed = 4
movement = {"Up": False, "Down": False, "Left": False, "Right": False}

# Global variables for enemy and player positions
enemy_speed = 5  # Enemy speed for movement
enemy_size = player_size # Enemy size

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

# Variable for the minimum and maximum light radius
MIN_LIGHT_RADIUS = 100
MAX_LIGHT_RADIUS = 150
LIGHT_RADIUS = MIN_LIGHT_RADIUS  # Initialize LIGHT_RADIUS to the minimum light radius value


# You may want to check that the `LIGHT_RADIUS` is being updated properly as the bar decreases
def update_light_radius():
    """Update the light radius based on the current width of the sanity bar."""
    global LIGHT_RADIUS
    
    # Calculate the percentage of the bar width remaining (between 0 and 1)
    bar_percentage = bar_width / 200  # bar_width starts at 200 and decreases to 0
    
    # Map the bar width percentage to the light radius range (from 100 to 125)
    LIGHT_RADIUS = MIN_LIGHT_RADIUS + (MAX_LIGHT_RADIUS - MIN_LIGHT_RADIUS) * bar_percentage

def calculate_shading(x, y, is_wall, target_x=None, target_y=None):
    """ Lighting effect based on player distance, applies to walls and ground differently. """
    if debug_mode:
        return "#808080" if is_wall else "#eeeeee"  # Walls remain white, floors a bit lighter in debug mode
    
    # Default to player's position if no target position is provided
    if target_x is None or target_y is None:
        target_x, target_y = player_x, player_y
    
    # Ensure the coordinates are within the bounds of the maze
    if 0 <= x < MAZE_COLS and 0 <= y < MAZE_ROWS:
        distance = math.sqrt((target_x - (x * GRID_SIZE))**2 + (target_y - (y * GRID_SIZE))**2)
        shade_factor = min(1, distance / LIGHT_RADIUS)
        
        if distance > LIGHT_RADIUS:
            return "#000000"  # Completely black if outside the light radius
        
        if is_wall:
            color_value = max(30, 100 - int(100 * shade_factor))  # Walls stay darker
        else:
            color_value = max(0, 255 - int(255 * shade_factor))  # Floors get full range of light
        return f"#{color_value:02x}{color_value:02x}{color_value:02x}"
    
    return "#000000"  # Return black if out of bounds (this case should be rare)

# Random starting position in an open space
floor_tiles = [(x, y) for y in range(MAZE_ROWS) for x in range(MAZE_COLS) if maze[y][x] == 0]
player_x, player_y = random.choice(floor_tiles)
player_x = int(player_x * GRID_SIZE + player_size // 2)
player_y = int(player_y * GRID_SIZE + player_size // 2)

# Camera settings
camera_x, camera_y = 0.0, 0.0  # Camera positions should be floats for smooth movement
camera_speed = 9  # Camera speed (higher = faster follow)
camera_x_target, camera_y_target = float(player_x), float(player_y)  # Camera target positions

# Variable for the decreasing bar width
bar_width = 200

# Variable for the speed at which the bar reduces (in pixels per update)
bar_decrease_speed = 0.1  # You can change this to a larger number for faster decrease

# Call this function inside the `update_bar` function to update the light radius as the bar decreases.
def update_bar():
    global bar_width
    if bar_width > 0:
        bar_width -= bar_decrease_speed  # Slowly decrease the width of the bar by the speed value
        bar_canvas.delete("all")
        bar_canvas.create_rectangle(0, 0, bar_width, 20, fill="#9668b5")
    
    # Update the light radius based on the current bar width
    update_light_radius()

    # Repeat the update every 50 milliseconds
    root.after(100, update_bar)

# A* pathfinding algorithm to find the shortest path from start to goal, avoiding walls
def a_star(start, goal):
    open_list = []
    closed_list = set()
    came_from = {}
    
    start_node = (0, start)
    heapq.heappush(open_list, start_node)
    
    g_costs = {start: 0}
    f_costs = {start: heuristic(start, goal)}
    
    while open_list:
        _, current = heapq.heappop(open_list)
        
        if current == goal:
            return reconstruct_path(came_from, current)
        
        closed_list.add(current)
        
        # Check neighbors (up, down, left, right, and diagonals)
        for neighbor in get_neighbors(current):
            if neighbor in closed_list:
                continue
            
            tentative_g_cost = g_costs[current] + 1  # Moving to a neighbor costs 1
            
            if neighbor not in g_costs or tentative_g_cost < g_costs[neighbor]:
                came_from[neighbor] = current
                g_costs[neighbor] = tentative_g_cost
                f_costs[neighbor] = g_costs[neighbor] + heuristic(neighbor, goal)
                
                if neighbor not in open_list:
                    heapq.heappush(open_list, (f_costs[neighbor], neighbor))
    
    return []  # No path found

# Random starting position for player in an open space
def random_spawn():
    """ Function to spawn at a random non-wall tile. """
    floor_tiles = [(x, y) for y in range(MAZE_ROWS) for x in range(MAZE_COLS) if maze[y][x] == 0]  # Only walkable tiles
    return random.choice(floor_tiles)  # Random non-wall tile

# Set player and enemy starting positions
player_x, player_y = random_spawn()
player_x = int(player_x * GRID_SIZE + player_size // 2)
player_y = int(player_y * GRID_SIZE + player_size // 2)

# Create a list to hold the positions of multiple enemies
enemies = []

def spawn_enemies(num_enemies=3):
    """Spawn multiple enemies at random non-wall tiles."""
    global enemies
    enemies.clear()  # Clear any existing enemies
    for _ in range(num_enemies):
        enemy_x, enemy_y = random_spawn()  # Random spawn for each enemy
        enemy_x = int(enemy_x * GRID_SIZE + enemy_size // 2)
        enemy_y = int(enemy_y * GRID_SIZE + enemy_size // 2)
        enemies.append({'x': enemy_x, 'y': enemy_y})  # Store enemy's position in a dict

spawn_enemies(3)  # Spawn 5 enemies in different locations

# Directions for A* (up, down, left, right, diagonals)
directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]

def heuristic(start, goal):
    """ Calculate the Manhattan distance (or Euclidean) between two points. """
    x1, y1 = start
    x2, y2 = goal
    return abs(x1 - x2) + abs(y1 - y2)  # Manhattan distance for grid-based movement

def get_neighbors(pos):
    """ Get valid neighboring positions (up, down, left, right, and diagonals). """
    x, y = pos
    neighbors = []
    
    for dx, dy in directions:
        nx, ny = x + dx, y + dy
        if 0 <= nx < MAZE_COLS and 0 <= ny < MAZE_ROWS and maze[ny][nx] == 0:  # Walkable tile
            neighbors.append((nx, ny))
    
    return neighbors

def a_star(start, goal):
    """ A* pathfinding algorithm to find the shortest path from start to goal. """
    open_list = []
    closed_list = set()
    came_from = {}
    
    start_node = (0, start)
    heapq.heappush(open_list, start_node)
    
    g_costs = {start: 0}
    f_costs = {start: heuristic(start, goal)}
    
    while open_list:
        _, current = heapq.heappop(open_list)
        
        if current == goal:
            return reconstruct_path(came_from, current)
        
        closed_list.add(current)
        
        for neighbor in get_neighbors(current):
            if neighbor in closed_list:
                continue
            
            tentative_g_cost = g_costs[current] + 1  # Moving to a neighbor costs 1
            
            if neighbor not in g_costs or tentative_g_cost < g_costs[neighbor]:
                came_from[neighbor] = current
                g_costs[neighbor] = tentative_g_cost
                f_costs[neighbor] = g_costs[neighbor] + heuristic(neighbor, goal)
                
                if neighbor not in open_list:
                    heapq.heappush(open_list, (f_costs[neighbor], neighbor))
    
    return []  # No path found

def reconstruct_path(came_from, current):
    """ Reconstruct the path from start to goal by tracing back. """
    path = []
    while current in came_from:
        path.append(current)
        current = came_from[current]
    path.reverse()
    return path

# Modify move_enemy_towards_player to handle multiple enemies
def move_enemies_towards_player():
    """Move each enemy towards the player's position using A* pathfinding or fallback behavior."""
    for enemy in enemies:
        enemy_x, enemy_y = enemy['x'], enemy['y']
        
        # Calculate the distance from the enemy to the player
        distance_to_player = math.sqrt((player_x - enemy_x)**2 + (player_y - enemy_y)**2)
        
        # Calculate the chase radius, which is slightly larger than the light radius
        chase_radius = LIGHT_RADIUS * 1.2  # 20% larger than the light radius
        
        # Adjust the enemy's speed based on its distance to the player
        if distance_to_player > chase_radius:
            current_enemy_speed = enemy_speed * 1.5  # Enemy moves faster outside of chase radius
        else:
            current_enemy_speed = enemy_speed * 0.5  # Enemy moves slower inside chase radius
        
        # Proceed with A* pathfinding as normal
        start = (enemy_x // GRID_SIZE, enemy_y // GRID_SIZE)
        goal = (player_x // GRID_SIZE, player_y // GRID_SIZE)
        
        enemy_path = a_star(start, goal)
        
        if not enemy_path:  # If no path is found, start fallback behavior
            random_wander(enemy)
        else:
            next_position = enemy_path.pop(0)
            target_x, target_y = next_position
            target_x = target_x * GRID_SIZE + GRID_SIZE // 2
            target_y = target_y * GRID_SIZE + GRID_SIZE // 2
            
            dx = target_x - enemy_x
            dy = target_y - enemy_y
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance != 0:
                dx /= distance  # Normalize to move in the correct direction
                dy /= distance
            
            # Adjust the movement speed of the enemy
            new_enemy_x = enemy_x + dx * current_enemy_speed
            new_enemy_y = enemy_y + dy * current_enemy_speed
            
            if can_move(new_enemy_x, enemy_y, is_player=False):
                enemy['x'] = int(new_enemy_x)
            if can_move(enemy_x, new_enemy_y, is_player=False):
                enemy['y'] = int(new_enemy_y)

def random_wander(enemy):
    """ Random wandering behavior for the enemy when stuck. """
    direction = random.choice(directions)
    
    dx, dy = direction
    new_enemy_x = enemy['x'] + dx * enemy_speed
    new_enemy_y = enemy['y'] + dy * enemy_speed
    
    if can_move(new_enemy_x, enemy['y'], is_player=False):
        enemy['x'] = int(new_enemy_x)
    if can_move(enemy['x'], new_enemy_y, is_player=False):
        enemy['y'] = int(new_enemy_y)

# Modify the can_move function to allow ghost mode functionality
def can_move(new_x, new_y, is_player=True):
    """ Check if the enemy or player can move to the new position. """
    if ghost_mode and is_player:  # If ghost mode is enabled, allow the player to walk through walls
        return True
    
    grid_x = int(new_x) // GRID_SIZE  # Ensure grid_x is an integer
    grid_y = int(new_y) // GRID_SIZE  # Ensure grid_y is an integer
    
    if 0 <= grid_x < MAZE_COLS and 0 <= grid_y < MAZE_ROWS:
        return maze[grid_y][grid_x] == 0  # Check if it's a walkable tile for the player
    return False

# Example usage: Calling move_enemy_towards_player will move the enemy towards the player
move_enemies_towards_player()  # The enemy moves towards the player using A* or fallback behavior

# Update movement function to move multiple enemies
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
    
    # Move each enemy towards the player
    move_enemies_towards_player()
    
    redraw()
    root.after(16, update_movement)

# Update the redraw function to handle multiple enemies
def redraw():
    """Redraw the visible portion of the maze, player, and all enemies."""
    canvas.delete("all")
    
    # Make sure the camera's x and y positions do not go out of bounds
    start_x = max(0, int(camera_x // GRID_SIZE))
    start_y = max(0, int(camera_y // GRID_SIZE))
    
    end_x = min(MAZE_COLS - 1, int((camera_x + WIDTH) // GRID_SIZE))  # Ensure it's within bounds
    end_y = min(MAZE_ROWS - 1, int((camera_y + HEIGHT) // GRID_SIZE))  # Ensure it's within bounds

    # Optimized rendering loop for large mazes
    for y in range(start_y, end_y + 1):
        for x in range(start_x, end_x + 1):
            if 0 <= x < MAZE_COLS and 0 <= y < MAZE_ROWS:
                if debug_mode:
                    shading = calculate_shading(x, y, is_wall=(maze[y][x] == 1))
                    canvas.create_rectangle(x * GRID_SIZE - camera_x, y * GRID_SIZE - camera_y, 
                                            (x + 1) * GRID_SIZE - camera_x, (y + 1) * GRID_SIZE - camera_y,
                                            fill=shading, outline="black")
                else:
                    canvas.create_rectangle(x * GRID_SIZE - camera_x, y * GRID_SIZE - camera_y, 
                                            (x + 1) * GRID_SIZE - camera_x, (y + 1) * GRID_SIZE - camera_y,
                                            fill=calculate_shading(x, y, is_wall=(maze[y][x] == 1)),
                                            outline="")

    # Draw the player
    canvas.create_oval(player_x - player_size // 2 - camera_x, player_y - player_size // 2 - camera_y,
                       player_x + player_size // 2 - camera_x, player_y + player_size // 2 - camera_y,
                       fill="blue")

    # Draw each enemy
    for enemy in enemies:
        enemy_x, enemy_y = enemy['x'], enemy['y']
        
        # Calculate the distance from the player to the enemy
        distance_to_enemy = math.sqrt((player_x - enemy_x)**2 + (player_y - enemy_y)**2)
        
        # Calculate the red component based on the distance
        max_distance = LIGHT_RADIUS  # Maximum distance for full red intensity
        red_intensity = max(0, min(255, int(255 * (1 - (distance_to_enemy / max_distance)))) )  # Inverse distance

        # In debug mode, always show the enemy, with a fixed red color
        if debug_mode:
            enemy_color = "#FF0000"  # Fixed bright red color for the enemy
        elif distance_to_enemy <= LIGHT_RADIUS - 5:
            enemy_color = f"#{red_intensity:02x}00{0:02x}"  # RGB color: (red_intensity, 0, 0)
        else:
            enemy_color = "#000000"  # Fully black (invisible)

        # Draw the enemy with the calculated color
        canvas.create_oval(enemy_x - enemy_size // 2 - camera_x, enemy_y - enemy_size // 2 - camera_y,
                           enemy_x + enemy_size // 2 - camera_x, enemy_y + enemy_size // 2 - camera_y,
                           fill=enemy_color)

# Keyboard controls
def on_key_press(event):
    global ghost_mode, debug_mode
    key = event.keysym
    if key == "Up":
        movement["Up"] = True
    elif key == "Down":
        movement["Down"] = True
    elif key == "Left":
        movement["Left"] = True
    elif key == "Right":
        movement["Right"] = True
    elif key == "w":
        movement["Up"] = True
    elif key == "s":
        movement["Down"] = True
    elif key == "a":
        movement["Left"] = True
    elif key == "d":
        movement["Right"] = True
    elif key == "b":
        debug_mode = not debug_mode  # Toggle debug mode on 'b' key press
        display_text(f"Debug Mode: {'On' if debug_mode else 'Off'}")
    elif key == "g":
        ghost_mode = not ghost_mode  # Toggle ghost mode on 'g' key press
        display_text(f"Ghost Mode: {'On' if ghost_mode else 'Off'}")

def on_key_release(event):
    key = event.keysym
    if key == "Up":
        movement["Up"] = False
    elif key == "Down":
        movement["Down"] = False
    elif key == "Left":
        movement["Left"] = False
    elif key == "Right":
        movement["Right"] = False
    elif key == "w":
        movement["Up"] = False
    elif key == "s":
        movement["Down"] = False
    elif key == "a":
        movement["Left"] = False
    elif key == "d":
        movement["Right"] = False

# Bind the keys to the controls
root.bind("<KeyPress>", on_key_press)
root.bind("<KeyRelease>", on_key_release)

# Update the bar
update_bar()

# Start updating the game logic
update_movement()

# Start the Tkinter event loop
root.mainloop()
# Hello