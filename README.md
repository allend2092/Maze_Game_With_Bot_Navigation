# Simulant AI Prototype

This is a Python-based game simulation built with `pygame` that explores AI behavior inspired by the **Simulants** in *Perfect Dark* (Nintendo 64). The project focuses on replicating intelligent-seeming bot behavior within a top-down, 2D maze world.

---

## 🎮 Project Overview

You control a player (blue square) moving around a maze-like environment.

An AI-controlled **Simulant bot** (red square) operates using a **finite state machine (FSM)** and exhibits the following behaviors:

### 🔁 Bot States

- **`spawn`**: 
  - The bot appears and spins in place for one second, as if surveying its environment.
  
- **`explore`**: 
  - Chooses a random reachable point on the map and begins planning a path.

- **`navigate`**:
  - Uses **A\*** pathfinding to follow a list of waypoints (breadcrumbs) to the target.
  - Dynamically avoids walls and recalculates if blocked.
  - Vision cone follows the direction of movement.

- **`pursue`**: 
  - If the player is detected in the bot's **field of view (FOV)** and **line-of-sight (LOS)**, the bot moves toward the player at full speed.

- **`hunt`**: 
  - If the player escapes the vision cone, the bot goes to the last known position and spins in place for 5 seconds before resuming exploration.

---

## 👁️ Vision System

- The bot has a **visible yellow cone** indicating its FOV.
- **Line-of-sight** is blocked by walls: the bot must "see" the player directly.
- The cone automatically rotates to match the bot's facing direction (toward next waypoint or player).

---

## 🧠 Technical Features

- Top-down 2D rendering using `pygame`
- Grid-based world with walkable and wall tiles
- Pixel-accurate movement (not tile-snapped)
- A* pathfinding for intelligent navigation
- Collision detection with walls
- Visual path breadcrumbs (cyan) to show bot planning
- FSM-driven AI with real-time state labels above the bot

---

## 🧭 Why I'm Building This

> As a teenager, I was fascinated by the Simulant bots in *Perfect Dark* — how they moved, reacted, and created the illusion of intelligence on limited hardware.  
>  
> This project is my attempt to **reverse-engineer and recreate** that behavior.  
>  
> It's a hands-on experiment in:
> - Artificial intelligence
> - Game simulation
> - FSMs and pathfinding
> - Visual debugging
> - Reconnecting with my original inspiration to study computer science

---

## 🛠️ Requirements

- Python 3.8+
- `pygame` library

To install `pygame`:
```bash
pip install pygame
```

---

## 🚀 How to Run

Save the script (e.g., `simulant_game.py`) and run it in a Python environment:
```bash
python simulant_game.py
```

Use **arrow keys** to move the player.  
Watch the red Simulant bot adapt, pursue, and hunt intelligently.

---

## 📌 Next Steps

- Add multiple Simulants with different personalities
- Implement cover-seeking and group behavior
- Introduce objectives (e.g., player escape, bot patrols)
- Move to a 3D environment using Unity or Godot (long-term)

---

## 👤 Author

**Daryl Allen**  
Engineer | AI Enthusiast | Lifelong Gamer  
Inspired by *Perfect Dark*, driven by curiosity.

