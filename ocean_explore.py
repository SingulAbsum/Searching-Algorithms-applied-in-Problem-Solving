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
grid_weights = [[{"weight":0, "explored": False} for _ in range(ROWS)] for _ in range(COLS)]
pygame.font.init()
font = pygame.font.SysFont(None, 20)
frontier = []

# Colors
WATER_COLOR = (80, 180, 255)
AIR_COLOR   = (240, 240, 255)
PLAYER_COLOR = (255, 200, 80)

# Player
player_x, player_y = random.randint(0, COLS-1), random.randint(0, ROWS-1)
breath = 200

# Air gaps
air_positions = {(random.randint(0, COLS-1), random.randint(0, ROWS-1)) for _ in range(
    random.randint(1, max(1, (COLS*ROWS)//20))
)}

# Fill weights
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

# Player path
player_path = [(player_x, player_y)]
grid_weights[player_x][player_y]["explored"] = True

# Draw the scene
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
            if rect.right < 0 or rect.left > WIDTH or rect.bottom < 0 or rect.top > HEIGHT:
                continue

            cell = grid_weights[c][r]
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

            text_surf = font.render(str(w), True, (0, 0, 0))
            text_rect = text_surf.get_rect(center=(
                (c * TILE - scroll_x + TILE // 2) * zoom,
                (r * TILE - scroll_y + TILE // 2) * zoom
            ))
            screen.blit(text_surf, text_rect)

    # Draw path
    for i,(px, py) in enumerate(player_path):
        rect = pygame.Rect(
            (px * TILE - scroll_x) * zoom,
            (py * TILE - scroll_y) * zoom,
            TILE * zoom,
            TILE * zoom
        )
        if i == 0:
            pygame.draw.rect(screen, (255, 0, 0), rect, 3)
        else:
            pygame.draw.rect(screen, (255, 255, 0), rect, 3)
    # Player on top
    player_rect = pygame.Rect(
        (player_x * TILE - scroll_x) * zoom,
        (player_y * TILE - scroll_y) * zoom,
        TILE * zoom,
        TILE * zoom
    )
    pygame.draw.rect(screen, PLAYER_COLOR, player_rect)

# Draw stats overlay
def draw_stats():
    move_count = len(player_path)
    surface_area = (move_count / (ROWS * COLS)) * 100.0
    stats_text = f"Moves: {move_count}  Surface Area: {surface_area:.1f}%  Breath: {breath}"
    text_surf = font.render(stats_text, True, (255, 255, 255))
    screen.blit(text_surf, (10, 10))

# Simulation loop
while breath > 0:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEWHEEL:
            zoom += event.y * 0.1
            zoom = max(0.2, min(3.0, zoom))
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            dragging = True
            last_mouse_pos = event.pos
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            dragging = False
        elif event.type == pygame.MOUSEMOTION and dragging:
            dx = event.pos[0] - last_mouse_pos[0]
            dy = event.pos[1] - last_mouse_pos[1]
            scroll_x -= dx / zoom
            scroll_y -= dy / zoom
            last_mouse_pos = event.pos

    scroll_x = max(-200, min(scroll_x, max(0, COLS * TILE - WIDTH / zoom)))
    scroll_y = max(-200, min(scroll_y, max(0, ROWS * TILE - HEIGHT / zoom)))

    # Build frontier
    frontier.clear()
    def consider(nx, ny):
        if 0 <= nx < COLS and 0 <= ny < ROWS:
            if not grid_weights[nx][ny]["explored"]:
                frontier.append((grid_weights[nx][ny]["weight"], nx, ny))

    neighbors = [
        (1,0), (-1,0), (0,1), (0,-1),
        (1,1), (1,-1), (-1,-1), (-1,1)
    ]
    for dx, dy in neighbors:
        consider(player_x + dx, player_y + dy)

    if not frontier:
        x, y = random.randint(0, COLS-1), random.randint(0, ROWS-1)
        frontier.append((grid_weights[x][y]["weight"], x, y))

    if frontier:
        destination = max(frontier)
        player_x, player_y = destination[1], destination[2]
        grid_weights[player_x][player_y]["explored"] = True
        player_path.append((player_x, player_y))
        breath += grid_weights[player_x][player_y]["weight"]

    # Draw scene and stats
    draw_scene()
    draw_stats()
    pygame.display.flip()
    clock.tick(60)

# Final interactive loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEWHEEL:
            zoom += event.y * 0.1
            zoom = max(0.2, min(3.0, zoom))
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            dragging = True
            last_mouse_pos = event.pos
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            dragging = False
        elif event.type == pygame.MOUSEMOTION and dragging:
            dx = event.pos[0] - last_mouse_pos[0]
            dy = event.pos[1] - last_mouse_pos[1]
            scroll_x -= dx / zoom
            scroll_y -= dy / zoom
            last_mouse_pos = event.pos

    scroll_x = max(-200, min(scroll_x, max(0, COLS * TILE - WIDTH / zoom)))
    scroll_y = max(-200, min(scroll_y, max(0, ROWS * TILE - HEIGHT / zoom)))

    draw_scene()
    draw_stats()
    pygame.display.flip()
    clock.tick(60)
