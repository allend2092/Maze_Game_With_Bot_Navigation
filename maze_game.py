import pygame
import sys
import random
import math
import time
from queue import PriorityQueue

# ─── Configuration ────────────────────────────────────────────────
TILE_SIZE = 40
MAP_WIDTH = 20
MAP_HEIGHT = 15
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
FPS = 60

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
    maze[0][x] = 1
    maze[MAP_HEIGHT - 1][x] = 1
for y in range(MAP_HEIGHT):
    maze[y][0] = 1
    maze[y][MAP_WIDTH - 1] = 1
for x in range(5, 15):
    maze[7][x] = 1

# ─── Initialization ──────────────────────────────────────────────
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Simulant Debug Overlay")
clock = pygame.time.Clock()
FONT = pygame.font.SysFont(None, 20)

player_pos = pygame.Vector2(100, 100)
player_speed = 3

bot_pos = pygame.Vector2(400, 200)
bot_speed = 1.5
bot_max_speed = 3
bot_state = "spawn"
bot_state_timer = time.time()
bot_angle = 0
bot_target = None
bot_last_seen = None
bot_path = []

# ─── Utility Functions ────────────────────────────────────────────
def pos_to_grid(pos):
    return int(pos.x // TILE_SIZE), int(pos.y // TILE_SIZE)

def grid_to_pos(x, y):
    return pygame.Vector2(x * TILE_SIZE + TILE_SIZE // 2, y * TILE_SIZE + TILE_SIZE // 2)

def check_collision(pos):
    rect = pygame.Rect(pos.x, pos.y, TILE_SIZE, TILE_SIZE)
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            if maze[y][x] == 1:
                if rect.colliderect(pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)):
                    return True
    return False

def move_entity(pos, direction, speed):
    step = pygame.Vector2(math.cos(direction), math.sin(direction)) * speed
    new_pos = pos + step
    if not check_collision(new_pos):
        pos.update(new_pos)
        return True
    return False

# ─── A* ───────────────────────────────────────────────────────────
def heuristic(a, b): return abs(a[0]-b[0]) + abs(a[1]-b[1])

def a_star(start, goal):
    pq = PriorityQueue()
    pq.put((0, start))
    came, cost = {start: None}, {start: 0}
    while not pq.empty():
        _, cur = pq.get()
        if cur == goal: break
        for dx,dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nxt=(cur[0]+dx,cur[1]+dy)
            if 0<=nxt[0]<MAP_WIDTH and 0<=nxt[1]<MAP_HEIGHT and maze[nxt[1]][nxt[0]]==0:
                newc=cost[cur]+1
                if nxt not in cost or newc<cost[nxt]:
                    cost[nxt]=newc
                    pq.put((newc+heuristic(goal,nxt),nxt))
                    came[nxt]=cur
    path=[]
    cur=goal
    while cur!=start and cur in came:
        path.append(cur)
        cur=came[cur]
    path.reverse()
    return [grid_to_pos(x,y) for x,y in path]

def is_line_clear(a,b):
    steps=int(a.distance_to(b)//5)
    for i in range(steps+1):
        p=a.lerp(b,i/steps)
        gx,gy=int(p.x//TILE_SIZE),int(p.y//TILE_SIZE)
        if maze[gy][gx]==1: return False
    return True

# ─── Vision / LOS ────────────────────────────────────────────────
def can_see_player(center, fov=60, length=200):
    vec=player_pos+pygame.Vector2(TILE_SIZE/2)-center
    if vec.length()>length: return False
    ang=(math.degrees(math.atan2(vec.y,vec.x))-math.degrees(bot_angle)+360)%360
    if ang>180: ang-=360
    if abs(ang)>fov/2: return False
    return is_line_clear(center, player_pos+pygame.Vector2(TILE_SIZE/2))

def draw_cone(center):
    length=200; fov=60
    for ang in (-fov/2, fov/2):
        dx=math.cos(bot_angle+math.radians(ang))*length
        dy=math.sin(bot_angle+math.radians(ang))*length
        pygame.draw.line(screen,YELLOW,center,(center.x+dx,center.y+dy),1)
    pygame.draw.line(screen,YELLOW,center,(center.x,center.y),1) # center dot

# ─── FSM update ──────────────────────────────────────────────────
def update_bot():
    global bot_state,bot_state_timer,bot_target,bot_path,bot_last_seen,bot_angle
    now=time.time(); center=bot_pos+pygame.Vector2(TILE_SIZE/2)

    if bot_state=="spawn":
        if now-bot_state_timer>1: bot_state="explore"
        bot_angle+=0.05; return

    if bot_state=="explore":
        if can_see_player(center): bot_state,bot_path="pursue",[]
        else:
            if not bot_target:
                while True:
                    gx,gy=random.randint(1,MAP_WIDTH-2),random.randint(1,MAP_HEIGHT-2)
                    if maze[gy][gx]==0:
                        bot_target=grid_to_pos(gx,gy); break
            bot_state="navigate"; bot_path=[]

    if bot_state=="navigate":
        if not bot_path:
            if is_line_clear(bot_pos,bot_target):
                bot_path=[bot_target]
            else:
                bot_path=a_star(pos_to_grid(bot_pos),pos_to_grid(bot_target))
            if not bot_path: bot_state="explore"; bot_target=None; return
        wp=bot_path[0]
        bot_angle=math.radians(-(wp-bot_pos).angle_to(pygame.Vector2(1,0)))
        if move_entity(bot_pos, bot_angle, bot_speed):
            if bot_pos.distance_to(wp)<=bot_speed: bot_path.pop(0)
        else: bot_path=[] # recalc next frame
        if not bot_path: bot_state,bot_target="explore",None
        if can_see_player(center): bot_state,bot_path="pursue",[]

    if bot_state=="pursue":
        if can_see_player(center):
            bot_last_seen=player_pos.copy()
            bot_angle=math.radians(-(player_pos-bot_pos).angle_to(pygame.Vector2(1,0)))
            move_entity(bot_pos, bot_angle, bot_max_speed)
        else:
            bot_state="hunt"; bot_state_timer=now

    if bot_state=="hunt":
        if can_see_player(center): bot_state="pursue"
        elif bot_last_seen and bot_pos.distance_to(bot_last_seen)>5:
            bot_angle=math.radians(-(bot_last_seen-bot_pos).angle_to(pygame.Vector2(1,0)))
            if not move_entity(bot_pos, bot_angle, bot_speed): bot_last_seen=None
        else:
            bot_angle+=0.05
        if now-bot_state_timer>5: bot_state="explore"; bot_target=None

# ─── Render helpers ───────────────────────────────────────────────
def cam_offset():
    x=max(0,min(player_pos.x-SCREEN_WIDTH//2,MAP_WIDTH*TILE_SIZE-SCREEN_WIDTH))
    y=max(0,min(player_pos.y-SCREEN_HEIGHT//2,MAP_HEIGHT*TILE_SIZE-SCREEN_HEIGHT))
    return x,y

def draw(offset):
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            rect=pygame.Rect(x*TILE_SIZE-offset[0],y*TILE_SIZE-offset[1],TILE_SIZE,TILE_SIZE)
            pygame.draw.rect(screen, GRAY if maze[y][x] else WHITE, rect)
            pygame.draw.rect(screen, BLACK, rect,1)
    screen.blit(FONT.render(bot_state,True,BLACK),
                (bot_pos.x-offset[0],bot_pos.y-15-offset[1]))
    pygame.draw.rect(screen, BLUE, pygame.Rect(player_pos.x-offset[0],player_pos.y-offset[1],TILE_SIZE,TILE_SIZE))
    pygame.draw.rect(screen, RED,  pygame.Rect(bot_pos.x-offset[0],bot_pos.y-offset[1],TILE_SIZE,TILE_SIZE))
    center=bot_pos+pygame.Vector2(TILE_SIZE/2)-pygame.Vector2(offset)
    draw_cone(center)
    for wp in bot_path:
        pygame.draw.rect(screen,CYAN,pygame.Rect(wp.x-5-offset[0],wp.y-5-offset[1],10,10))

# ─── Main loop ────────────────────────────────────────────────────
while True:
    for e in pygame.event.get():
        if e.type==pygame.QUIT: pygame.quit(); sys.exit()
    keys=pygame.key.get_pressed()
    vec=pygame.Vector2((keys[pygame.K_RIGHT]-keys[pygame.K_LEFT])*player_speed,
                       (keys[pygame.K_DOWN]-keys[pygame.K_UP])*player_speed)
    if not check_collision(player_pos+vec): player_pos+=vec

    update_bot()
    screen.fill(BLACK)
    draw(cam_offset())
    pygame.display.flip()
    clock.tick(FPS)
