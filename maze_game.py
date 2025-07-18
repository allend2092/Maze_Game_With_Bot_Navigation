import pygame
import sys
import math
import random
import time
from queue import PriorityQueue
from collections import deque

# ─── Configuration ────────────────────────────────────────────────
TILE_SIZE   = 40
ENTITY_SIZE = int(TILE_SIZE * 0.8)
MAP_WIDTH, MAP_HEIGHT = 20, 15
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FPS = 60

# ─── Colors ───────────────────────────────────────────────────────
WHITE  = (255, 255, 255)
BLACK  = (0, 0, 0)
GRAY   = (50, 50, 50)
BLUE   = (0, 0, 255)
RED    = (255, 0, 0)
YELLOW = (255, 255, 0)
CYAN   = (0, 255, 255)

# ─── Maze Layout ──────────────────────────────────────────────────
maze = [[0 for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
for x in range(MAP_WIDTH):
    maze[0][x] = maze[MAP_HEIGHT - 1][x] = 1
for y in range(MAP_HEIGHT):
    maze[y][0] = maze[y][MAP_WIDTH - 1] = 1
for x in range(5, 15):
    maze[7][x] = 1

# ─── Collision and Grid Helpers ───────────────────────────────────

def rect_from_center(center: pygame.Vector2) -> pygame.Rect:
    half = ENTITY_SIZE // 2
    return pygame.Rect(center.x - half, center.y - half, ENTITY_SIZE, ENTITY_SIZE)

def pos_to_grid(pos: pygame.Vector2) -> tuple[int, int]:
    return int(pos.x // TILE_SIZE), int(pos.y // TILE_SIZE)

def grid_to_center(gx: int, gy: int) -> pygame.Vector2:
    return pygame.Vector2(gx * TILE_SIZE + TILE_SIZE // 2,
                          gy * TILE_SIZE + TILE_SIZE // 2)

def tile_is_wall(gx: int, gy: int) -> bool:
    return maze[gy][gx] == 1

def check_collision(center: pygame.Vector2) -> bool:
    """Check if entity collides with any walls in its 3x3 tile neighborhood."""
    rect = rect_from_center(center)
    gx, gy = pos_to_grid(center)
    for ny in range(max(0, gy - 1), min(MAP_HEIGHT, gy + 2)):
        for nx in range(max(0, gx - 1), min(MAP_WIDTH, gx + 2)):
            if tile_is_wall(nx, ny):
                wall_rect = pygame.Rect(nx * TILE_SIZE, ny * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                if rect.colliderect(wall_rect):
                    return True
    return False

def move_entity(center: pygame.Vector2, direction: float, speed: float) -> bool:
    step = pygame.Vector2(math.cos(direction), math.sin(direction)) * speed
    new_center = center + step
    if not check_collision(new_center):
        center.update(new_center)
        return True
    return False

# ─── A* Pathfinding ───────────────────────────────────────────────

def heuristic(a: tuple[int, int], b: tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def a_star(start: tuple[int, int], goal: tuple[int, int]) -> list[pygame.Vector2]:
    pq = PriorityQueue()
    pq.put((0, start))
    came_from = {start: None}
    g_cost = {start: 0}

    while not pq.empty():
        _, current = pq.get()
        if current == goal:
            break
        cx, cy = current
        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < MAP_WIDTH and 0 <= ny < MAP_HEIGHT and not tile_is_wall(nx, ny):
                tentative_g = g_cost[current] + 1
                if (nx, ny) not in g_cost or tentative_g < g_cost[(nx, ny)]:
                    g_cost[(nx, ny)] = tentative_g
                    priority = tentative_g + heuristic((nx, ny), goal)
                    pq.put((priority, (nx, ny)))
                    came_from[(nx, ny)] = current

    if goal not in came_from:
        return []

    path = deque()
    cur = goal
    while cur != start:
        path.appendleft(grid_to_center(*cur))
        cur = came_from[cur]
    return list(path)

# ─── Vision & LOS ─────────────────────────────────────────────────

FOV_DEG   = 60
SIGHT_LEN = 200

def is_line_clear(a: pygame.Vector2, b: pygame.Vector2) -> bool:
    dist = a.distance_to(b)
    steps = max(1, int(dist // 5))
    for i in range(steps + 1):
        p = a.lerp(b, i / steps)
        if tile_is_wall(*pos_to_grid(p)):
            return False
    return True

def wide_line_clear(a: pygame.Vector2, b: pygame.Vector2) -> bool:
    dist = a.distance_to(b)
    steps = max(1, int(dist // 20))
    for i in range(steps + 1):
        if check_collision(a.lerp(b, i / steps)):
            return False
    return True

def can_see(player: pygame.Vector2, eye: pygame.Vector2, facing: float) -> bool:
    vec = player - eye
    if vec.length() > SIGHT_LEN:
        return False
    angle = (math.degrees(math.atan2(vec.y, vec.x)) - math.degrees(facing)) % 360
    if angle > 180: angle -= 360
    return abs(angle) <= FOV_DEG / 2 and is_line_clear(eye, player)

# ─── Entities ─────────────────────────────────────────────────────

player_pos = grid_to_center(2, 2)
player_speed = 3

bot_pos = grid_to_center(10, 5)
bot_speed = 1.5
bot_max_speed = 3

# ─── Bot FSM ──────────────────────────────────────────────────────

bot_state       = "spawn"
bot_state_timer = time.time()
bot_angle       = 0.0
bot_target      = None
bot_last_seen   = None
bot_path        = []

DIRECT_DELAY     = 1
direct_countdown = -1

def face_towards(vec: pygame.Vector2) -> float:
    return -math.radians(vec.angle_to(pygame.Vector2(1, 0)))

def update_bot():
    global bot_state, bot_state_timer, bot_target
    global bot_last_seen, bot_path, bot_angle, direct_countdown

    now = time.time()
    eye, p_eye = bot_pos, player_pos
    sees_player = can_see(p_eye, eye, bot_angle)

    if bot_state == "spawn":
        if now - bot_state_timer > 1:
            bot_state, bot_state_timer = "explore", now
        bot_angle += 0.05
        return

    if bot_state == "explore":
        if sees_player:
            bot_state, bot_path = "pursue", []
        else:
            if not bot_target:
                while True:
                    gx, gy = random.randint(1, MAP_WIDTH-2), random.randint(1, MAP_HEIGHT-2)
                    if not tile_is_wall(gx, gy):
                        bot_target = grid_to_center(gx, gy)
                        break
            bot_state = "navigate"

    if bot_state == "navigate":
        if sees_player:
            bot_state, bot_path, direct_countdown = "pursue", [], -1
        else:
            if bot_target and wide_line_clear(eye, bot_target):
                direct_countdown = DIRECT_DELAY if direct_countdown == -1 else direct_countdown
            else:
                direct_countdown = -1

            if direct_countdown == 0:
                bot_path = [bot_target]
                direct_countdown = -1

            if not bot_path:
                bot_path = [bot_target] if wide_line_clear(eye, bot_target) else a_star(pos_to_grid(eye), pos_to_grid(bot_target))
                if not bot_path:
                    bot_state, bot_target, direct_countdown = "explore", None, -1
                    return

            wp = bot_path[0]
            bot_angle = face_towards(wp - eye)
            if move_entity(bot_pos, bot_angle, bot_speed):
                if bot_pos.distance_to(wp) <= bot_speed:
                    bot_path.pop(0)
                    if direct_countdown > 0:
                        direct_countdown -= 1
            else:
                bot_path, direct_countdown = [], -1
            if not bot_path:
                bot_state, bot_target, direct_countdown = "explore", None, -1

    if bot_state == "pursue":
        if sees_player:
            bot_last_seen = p_eye.copy()
            bot_angle = face_towards(p_eye - eye)
            move_entity(bot_pos, bot_angle, bot_max_speed)
        else:
            bot_state, bot_state_timer = "hunt", now

    if bot_state == "hunt":
        if sees_player:
            bot_state = "pursue"
        elif bot_last_seen and bot_pos.distance_to(bot_last_seen) > bot_speed:
            bot_angle = face_towards(bot_last_seen - eye)
            if not move_entity(bot_pos, bot_angle, bot_speed):
                bot_last_seen = None
        else:
            bot_angle += 0.05  # idle spin if reached last known location

        if now - bot_state_timer > 5:
            bot_state, bot_target, bot_last_seen = "explore", None, None

# ─── Rendering ────────────────────────────────────────────────────

def draw_cone(center: pygame.Vector2):
    """Draws bot's vision cone based on FOV and angle."""
    half_fov = math.radians(FOV_DEG / 2)
    for ang in (-half_fov, half_fov):
        dx = math.cos(bot_angle + ang) * SIGHT_LEN
        dy = math.sin(bot_angle + ang) * SIGHT_LEN
        pygame.draw.line(screen, YELLOW, center, (center.x + dx, center.y + dy), 1)
    pygame.draw.circle(screen, YELLOW, center, 2)

def cam_offset() -> tuple[int, int]:
    """Camera offset keeps player roughly centered on screen."""
    max_x = MAP_WIDTH * TILE_SIZE - SCREEN_WIDTH
    max_y = MAP_HEIGHT * TILE_SIZE - SCREEN_HEIGHT
    return (
        int(max(0, min(player_pos.x - SCREEN_WIDTH // 2, max_x))),
        int(max(0, min(player_pos.y - SCREEN_HEIGHT // 2, max_y)))
    )

def draw(offset: tuple[int, int]):
    """Main draw routine: tiles, entities, path, and debug info."""
    ox, oy = offset

    # draw maze
    for gy in range(MAP_HEIGHT):
        for gx in range(MAP_WIDTH):
            tile_rect = pygame.Rect(gx * TILE_SIZE - ox, gy * TILE_SIZE - oy, TILE_SIZE, TILE_SIZE)
            color = GRAY if tile_is_wall(gx, gy) else WHITE
            pygame.draw.rect(screen, color, tile_rect)
            pygame.draw.rect(screen, BLACK, tile_rect, 1)

    # draw bot path (breadcrumbs)
    for wp in bot_path:
        pygame.draw.rect(screen, CYAN, pygame.Rect(wp.x - 5 - ox, wp.y - 5 - oy, 10, 10))

    # draw player and bot
    pygame.draw.rect(screen, BLUE, rect_from_center(player_pos).move(-ox, -oy))
    pygame.draw.rect(screen, RED, rect_from_center(bot_pos).move(-ox, -oy))

    # draw bot FOV
    draw_cone(bot_pos - pygame.Vector2(ox, oy))

    # draw bot state text
    text = FONT.render(bot_state, True, BLACK)
    screen.blit(text, (
        bot_pos.x - ox - text.get_width() // 2,
        bot_pos.y - oy - ENTITY_SIZE
    ))

# ─── Main Loop ────────────────────────────────────────────────────

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Simulant AI Prototype")
clock = pygame.time.Clock()
FONT = pygame.font.SysFont(None, 20)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # ── Player Controls ──
    keys = pygame.key.get_pressed()
    move_vector = pygame.Vector2(
        (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * player_speed,
        (keys[pygame.K_DOWN]  - keys[pygame.K_UP])   * player_speed
    )

    if move_vector.length_squared() > 0:
        dir_radians = math.atan2(move_vector.y, move_vector.x)
        move_entity(player_pos, dir_radians, player_speed)

    # ── Update and Draw ──
    update_bot()
    screen.fill(BLACK)
    draw(cam_offset())
    pygame.display.flip()
    clock.tick(FPS)
