# 🔴 Deadlock Detection Visualization System

An interactive **Operating Systems** project that visualizes the **Resource Allocation Graph (RAG)** and detects deadlocks in real time using **DFS cycle detection** — rendered with **OpenGL** and **Pygame**.

> Built as a university project combining Operating Systems concepts with Computer Graphics implementation.

---

## 📌 Project Overview

This system simulates how an OS manages processes and resources, and visually detects when a **deadlock** occurs. Users can interactively create processes, assign resources, and watch the system highlight deadlock cycles instantly.

---

## 🎬 Demo

![Deadlock Detected](https://github.com/user-attachments/assets/5942e6cb-a7d6-4f6f-90c1-699d7f9d6c1a)

> Red pulsing nodes and edges indicate a detected deadlock cycle.

---

## 🛠️ Technologies Used

| Technology | Purpose |
|------------|---------|
| **Python** | Core application logic |
| **Pygame** | Window management and event handling |
| **PyOpenGL (OpenGL + GLUT)** | 2D rendering and visual effects |
| **NumPy** | Mathematical computations |

---

## 🧠 OS Concepts Implemented

### Resource Allocation Graph (RAG)
- **Process nodes** → represented as blue circles
- **Resource nodes** → represented as orange squares with instance dots
- **Request edges** (Process → Resource) → dashed red arrows
- **Allocation edges** (Resource → Process) → solid green arrows

### Deadlock Detection Algorithm
Uses **Depth-First Search (DFS)** on a **Wait-For Graph** to detect cycles:

```
1. Build Wait-For graph from allocation and request edges
2. Run DFS on all process nodes
3. If a back edge is found → cycle detected → DEADLOCK
4. Highlight all nodes and edges in the cycle with pulsing red
```

### Multi-Instance Resources
Resources support multiple instances — a deadlock only occurs when all instances are fully allocated and circular waiting exists.

---

## ✨ Features

- **Real-time deadlock detection** — updates instantly on every graph change
- **Animated RAG** — smooth node movement and auto-layout
- **Pulsing red highlight** — clearly shows which nodes/edges are in the deadlock cycle
- **Interactive controls** — add/remove processes, resources, and edges with keyboard
- **Safe sequence display** — shows execution order when no deadlock exists
- **Step mode** — pause and step through the simulation manually

---

## 🎮 Controls

| Key | Action |
|-----|--------|
| `P` | Add a new Process node |
| `R` | Add a new Resource node (1–3 instances) |
| `Q` | Add a Request edge (Process → Resource) |
| `A` | Add an Allocation edge (Resource → Process) |
| `Click` | Select a node |
| `DEL` | Delete selected node and its edges |
| `C` | Clear all nodes and edges |
| `S` | Toggle Step mode |
| `Space` | Step forward (in Step mode) |
| `H` | Toggle Help overlay |
| `ESC` | Exit |

---

## 🏗️ Architecture

```
OpenGLRenderer          — Main application loop, rendering, event handling
│
├── DeadlockDetector    — Core logic: graph management + deadlock detection
│   ├── add_process()
│   ├── add_resource()
│   ├── add_request_edge()
│   ├── add_allocation_edge()
│   ├── detect_deadlock()   ← DFS cycle detection
│   └── update_layout()     ← Smooth node positioning
│
├── Node                — Process or Resource node with position & animation
└── Edge                — Request or Allocation edge with animation offset
```

---

## 🚀 Getting Started

### Prerequisites
```bash
pip install pygame PyOpenGL PyOpenGL_accelerate numpy
```

### Run
```bash
python main.py
```

The app launches with a **pre-built deadlock scenario** (2 processes + 2 resources in circular wait) so you can see the detection immediately.

---

## 📁 Project Structure

```
deadlock-detection/
│
├── main.py              # Full application (renderer + detector + UI)
├── screenshots/
│   └── deadlock_demo.png
└── README.md
```

---

## 💡 What I Learned

- Implementing deadlock detection using DFS on a Wait-For Graph
- Translating OS theory (RAG, safe sequences, multi-instance resources) into working code
- Real-time 2D rendering with OpenGL primitives (triangles, quads, lines)
- Building interactive simulations with Pygame event handling
- Smooth animations using interpolation and pulse effects

---

## 👥 Team

Developed as a university team project.

**Mohamed Amer** — Core logic (DeadlockDetector, DFS algorithm, OpenGL rendering)

- 📧 mo.abdo.amer123@gmail.com
- 💼 [LinkedIn](https://www.linkedin.com/in/mohamed-amer-217342376)
- 🐙 [GitHub](https://github.com/moabdoamer123-cmd)
