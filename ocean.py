import pygame
import sys
import random

pygame.init()

# Window
WIDTH, HEIGHT = 1200, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ocean Maze")

# Grid settings
TILE = 40
ROWS, COLS = random.randint(1, 100), random.randint(1, 100)
# grid_weights indexed as grid_weights[col][row]
grid_weights = [[{"weight":0, "explored": False} for _ in range(ROWS)] for _ in range(COLS)]
pygame.font.init()
font = pygame.font.SysFont(None, 20)
frontier = []

# Colors
WATER_COLOR = (80, 180, 255)
AIR_COLOR   = (240, 240, 255)
PLAYER_COLOR = (255, 200, 80)

# Player - correct ranges (x in [0,COLS-1], y in [0,ROWS-1])
player_x, player_y = random.randint(0, COLS-1), random.randint(0, ROWS-1)
breath = 200

# Air gaps - store as (col, row)
air_positions = {(random.randint(0, COLS-1), random.randint(0, ROWS-1)) for _ in range(
    random.randint(1, max(1, (COLS*ROWS)//20))
)}

# Fill weights correctly
for c in range(COLS):
    for r in range(ROWS):
        if (c, r) in air_positions:
            grid_weights[c][r]["weight"] = random.randint(20, 50)
        else:
            grid_weights[c][r]["weight"] = random.randint(-10, -1)

# Scroll & zoom
scroll_x, scroll_y = 0.0, 0.0
zoom = 1.0
dragging = False
last_mouse_pos = (0, 0)

clock = pygame.time.Clock()

# Keep a continuous path of visited tiles
player_path = [(player_x, player_y)]
grid_weights[player_x][player_y]["explored"] = True

# init stats so they exist from the start
move_count = len(player_path)
surface_area = (move_count / (ROWS * COLS)) * 100.0

def distance_to_nearest_air(x, y):
    """Return Manhattan distance from (x,y) to closest air tile."""
    if not air_positions:
        return 0
    return min(abs(ax - x) + abs(ay - y) for (ax, ay) in air_positions)

def score_tile(nx, ny):
    """Return a score combining weight and distance to nearest air."""
    w = grid_weights[nx][ny]["weight"]
    dist = distance_to_nearest_air(nx, ny)
    return w - 0.1* dist  # you can adjust weighting factor if needed

# Helper to draw the current scene (so we can reuse it after simulation ends)
def draw_scene():
    screen.fill((0, 0, 0))
    for c in range(COLS):
        for r in range(ROWS):
            rect = pygame.Rect(
                (c * TILE - scroll_x) * zoom,
                (r * TILE - scroll_y) * zoom,
                TILE * zoom,
                TILE * zoom
            )

            # Only draw tiles that are visible (optional)
            if rect.right < 0 or rect.left > WIDTH or rect.bottom < 0 or rect.top > HEIGHT:
                continue

            cell = grid_weights[c][r]      # dict with "weight" and "explored"
            w = cell["weight"]

            color_darkener = abs(w) * 14
            red_increase = 0
            if color_darkener > 100:
                red_increase = color_darkener - 100
                color_darkener = 100
            Weighted_WATER_COLOR = (
                min(WATER_COLOR[0] + red_increase, 255),
                max(WATER_COLOR[1] - color_darkener, 0),
                WATER_COLOR[2]
            )
            color = AIR_COLOR if (c, r) in air_positions else Weighted_WATER_COLOR
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, (0, 0, 60), rect, 2)

            # Draw weight number (use the numeric weight)
            text_surf = font.render(str(w), True, (0, 0, 0))
            text_rect = text_surf.get_rect(center=(
                (c * TILE - scroll_x + TILE // 2) * zoom,
                (r * TILE - scroll_y + TILE // 2) * zoom
            ))
            screen.blit(text_surf, text_rect)

    # Draw full player path
    for i,(px, py) in enumerate(player_path):
        rect = pygame.Rect(
            (px * TILE - scroll_x) * zoom,
            (py * TILE - scroll_y) * zoom,
            TILE * zoom,
            TILE * zoom
        )
        if i == 0:
            pygame.draw.rect(screen, (255, 0, 0), rect, 3)  # first position in red
        else:
            pygame.draw.rect(screen, (255, 255, 0), rect, 3)  # rest in yellow
    # Draw player last (so it's on top)
    player_rect = pygame.Rect(
        (player_x * TILE - scroll_x) * zoom,
        (player_y * TILE - scroll_y) * zoom,
        TILE * zoom,
        TILE * zoom
    )
    pygame.draw.rect(screen, PLAYER_COLOR, player_rect)


# Simulation loop: runs moves while breath > 0 and there are neighbors to explore
while breath > 0:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # Zoom with mouse wheel
        elif event.type == pygame.MOUSEWHEEL:
            zoom += event.y * 0.1
            zoom = max(0.2, min(3.0, zoom))

        # Start dragging
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                dragging = True
                last_mouse_pos = event.pos
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                dragging = False

        # Dragging motion
        elif event.type == pygame.MOUSEMOTION:
            if dragging:
                dx = event.pos[0] - last_mouse_pos[0]
                dy = event.pos[1] - last_mouse_pos[1]
                scroll_x -= dx / zoom
                scroll_y -= dy / zoom
                last_mouse_pos = event.pos

    # Clamp scroll so grid stays visible (with margin)
    scroll_x = max(-200, min(scroll_x, max(0, COLS * TILE - WIDTH / zoom)))
    scroll_y = max(-200, min(scroll_y, max(0, ROWS * TILE - HEIGHT / zoom)))

    # Build frontier from neighbors (8-neighborhood) - correct indexing and bounds
    frontier.clear()

    def consider(nx, ny):
        if 0 <= nx < COLS and 0 <= ny < ROWS:
            if not grid_weights[nx][ny]["explored"]:
                frontier.append((score_tile(nx, ny), nx, ny))

    # neighbors around (player_x, player_y)
    consider(player_x + 1, player_y)   # right
    consider(player_x - 1, player_y)   # left
    consider(player_x, player_y + 1)   # down
    consider(player_x, player_y - 1)   # up
    consider(player_x + 1, player_y + 1)  # down-right
    consider(player_x + 1, player_y - 1)  # up-right
    consider(player_x - 1, player_y - 1)  # up-left
    consider(player_x - 1, player_y + 1)  # down-left
    if not frontier:
        x=random.randint(0, COLS-1)
        y=random.randint(0, ROWS-1)
        if(grid_weights[x][y]["explored"]==True):
            while(grid_weights[x][y]["explored"]==True):
                x=random.randint(0, COLS-1)
                y=random.randint(0, ROWS-1)
        frontier.append((grid_weights[x][y]["weight"], x, y))
    # choose destination if frontier not empty
    if frontier:
        destination = max(frontier)   # (score, nx, ny) -> picks highest score
        player_x = destination[1]
        player_y = destination[2]
        # mark explored and append path (continuous)
        grid_weights[player_x][player_y]["explored"] = True
        player_path.append((player_x, player_y))
        # update breath by adding the tile weight (positive for air, negative for water)
        breath += grid_weights[player_x][player_y]["weight"]
        # update surface_area and move_count for info (optional)
        move_count = len(player_path)
        surface_area = (move_count / (ROWS * COLS)) * 100.0

    # Draw and show updates while simulation runs
    # draw scene first (so it won't overwrite the stats)
    draw_scene()
    stats_text = f"Moves: {move_count}  Surface Area: {surface_area:.1f}%  Breath: {breath}"
    text_surf = font.render(stats_text, True, (255, 255, 255))  # white text
    screen.blit(text_surf, (10, 10))  # top-left corner
    pygame.display.flip()
    clock.tick(60)

# Final interactive loop: simulation stopped, keep window open and interactive (zoom/scroll)
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # Keep zoom functionality
        elif event.type == pygame.MOUSEWHEEL:
            zoom += event.y * 0.1
            zoom = max(0.2, min(3.0, zoom))

        # Keep scrolling functionality
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                dragging = True
                last_mouse_pos = event.pos
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if dragging:
                dx = event.pos[0] - last_mouse_pos[0]
                dy = event.pos[1] - last_mouse_pos[1]
                scroll_x -= dx / zoom
                scroll_y -= dy / zoom
                last_mouse_pos = event.pos

    # Clamp scroll limits
    scroll_x = max(-200, min(scroll_x, max(0, COLS * TILE - WIDTH / zoom)))
    scroll_y = max(-200, min(scroll_y, max(0, ROWS * TILE - HEIGHT / zoom)))

    # Redraw the frozen scene (path + weights + player)
    draw_scene()
    # draw stats on top as well
    stats_text = f"Moves: {move_count}  Surface Area: {surface_area:.1f}%  Breath: {breath}"
    text_surf = font.render(stats_text, True, (255, 255, 255))
    screen.blit(text_surf, (10, 10))
    pygame.display.flip()
    clock.tick(60)
