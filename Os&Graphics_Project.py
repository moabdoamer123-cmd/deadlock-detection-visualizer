import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import numpy as np
import random
import math
from dataclasses import dataclass
from typing import List, Dict, Set, Tuple, Optional
from enum import Enum
import time

# Initialize GLUT for text rendering
glutInit()


class NodeType(Enum):
    PROCESS = 0
    RESOURCE = 1


class EdgeType(Enum):
    REQUEST = 0  # Process -> Resource (dashed, red)
    ALLOCATION = 1  # Resource -> Process (solid, green)


@dataclass
class Node:
    id: int
    type: NodeType
    x: float
    y: float
    target_x: float
    target_y: float
    label: str
    instances: int = 1  # For resources: total instances
    allocated: int = 0  # For resources: currently allocated
    color: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    selected: bool = False
    pulse: float = 0.0  # For animation effects

    def update_position(self, dt: float):
        # Smooth interpolation to target position
        speed = 5.0 * dt
        self.x += (self.target_x - self.x) * speed
        self.y += (self.target_y - self.y) * speed
        self.pulse += dt * 3.0


@dataclass
class Edge:
    source: int  # Node ID
    target: int  # Node ID
    type: EdgeType
    instances: int = 1  # Number of resource instances
    animated_offset: float = 0.0

    def update(self, dt: float):
        self.animated_offset += dt * 2.0


class DeadlockDetector:
    def __init__(self):
        self.nodes: Dict[int, Node] = {}
        self.edges: List[Edge] = []
        self.next_id = 0
        self.deadlock_cycle: List[int] = []
        self.is_deadlocked = False
        self.simulation_time = 0.0

    def add_process(self, x: float, y: float) -> int:
        node_id = self.next_id
        self.next_id += 1
        color = (0.3, 0.6, 1.0)  # Blue for processes
        self.nodes[node_id] = Node(
            id=node_id,
            type=NodeType.PROCESS,
            x=x, y=y,
            target_x=x, target_y=y,
            label=f"P{node_id}",
            color=color
        )
        return node_id

    def add_resource(self, x: float, y: float, instances: int = 1) -> int:
        node_id = self.next_id
        self.next_id += 1
        color = (1.0, 0.5, 0.2)  # Orange for resources
        self.nodes[node_id] = Node(
            id=node_id,
            type=NodeType.RESOURCE,
            x=x, y=y,
            target_x=x, target_y=y,
            label=f"R{node_id}",
            instances=instances,
            allocated=0,
            color=color
        )
        return node_id

    def add_request_edge(self, process_id: int, resource_id: int):
        for edge in self.edges:
            if edge.source == process_id and edge.target == resource_id and edge.type == EdgeType.REQUEST:
                return
        self.edges.append(Edge(process_id, resource_id, EdgeType.REQUEST))

    def add_allocation_edge(self, resource_id: int, process_id: int, instances: int = 1):
        for edge in self.edges:
            if edge.source == resource_id and edge.target == process_id and edge.type == EdgeType.ALLOCATION:
                return
        self.edges.append(Edge(resource_id, process_id, EdgeType.ALLOCATION, instances))
        if resource_id in self.nodes:
            self.nodes[resource_id].allocated += instances

    def remove_edge(self, source: int, target: int, edge_type: EdgeType):
        self.edges = [e for e in self.edges if not (e.source == source and e.target == target and e.type == edge_type)]
        if edge_type == EdgeType.ALLOCATION:
            if source in self.nodes:
                self.nodes[source].allocated = max(0, self.nodes[source].allocated - 1)

    def detect_deadlock(self) -> bool:
        wait_for: Dict[int, Set[int]] = {node_id: set() for node_id in self.nodes
                                         if self.nodes[node_id].type == NodeType.PROCESS}

        requests = [(e.source, e.target) for e in self.edges if e.type == EdgeType.REQUEST]
        allocations = [(e.source, e.target) for e in self.edges if e.type == EdgeType.ALLOCATION]

        resource_holders: Dict[int, List[int]] = {}
        for res_id, proc_id in allocations:
            if res_id not in resource_holders:
                resource_holders[res_id] = []
            resource_holders[res_id].append(proc_id)

        for proc_id, res_id in requests:
            if res_id in resource_holders:
                for holder_id in resource_holders[res_id]:
                    if holder_id != proc_id:
                        wait_for[proc_id].add(holder_id)

        visited = set()
        rec_stack = set()

        def dfs(node: int, path: List[int]) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            for neighbor in wait_for.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor, path): return True
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    self.deadlock_cycle = path[cycle_start:] + [neighbor]
                    return True
            path.pop()
            rec_stack.remove(node)
            return False

        for process_id in wait_for:
            if process_id not in visited:
                if dfs(process_id, []):
                    self.is_deadlocked = True
                    return True

        self.is_deadlocked = False
        self.deadlock_cycle = []
        return False

    def update_layout(self, dt: float):
        width, height = 1200, 800
        center_x, center_y = width / 2, height / 2
        processes = [n for n in self.nodes.values() if n.type == NodeType.PROCESS]
        resources = [n for n in self.nodes.values() if n.type == NodeType.RESOURCE]

        if processes:
            angle_step = 2 * math.pi / max(len(processes), 1)
            radius = 200
            for i, proc in enumerate(processes):
                angle = math.pi + i * angle_step
                proc.target_x = center_x + radius * math.cos(angle) - 150
                proc.target_y = center_y + radius * math.sin(angle) * 0.6

        if resources:
            angle_step = 2 * math.pi / max(len(resources), 1)
            radius = 200
            for i, res in enumerate(resources):
                angle = i * angle_step
                res.target_x = center_x + radius * math.cos(angle) + 150
                res.target_y = center_y + radius * math.sin(angle) * 0.6

        for node in self.nodes.values():
            node.update_position(dt)
        for edge in self.edges:
            edge.update(dt)
        self.simulation_time += dt

    def get_node_at(self, x: float, y: float, radius: float = 30.0) -> Optional[int]:
        for node_id, node in self.nodes.items():
            dx = node.x - x
            dy = node.y - y
            if math.sqrt(dx * dx + dy * dy) < radius:
                return node_id
        return None

    def get_safe_sequence(self):
        if self.is_deadlocked:
            return None
        return [node.label for node in self.nodes.values() if node.type == NodeType.PROCESS]


class OpenGLRenderer:
    def __init__(self, width: int = 1200, height: int = 800):
        self.width = width
        self.height = height
        self.detector = DeadlockDetector()
        self.selected_node: Optional[int] = None
        self.dragging_node: Optional[int] = None
        self.mode = "normal"
        self.source_node: Optional[int] = None
        self.show_help = True
        self.auto_simulate = False
        self.step_mode = False
        self.step_trigger = False

        pygame.init()
        pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Deadlock Detection Visualization System - OpenGL")

        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        # MODIFIED: Correct glOrtho orientation for matching text data
        glOrtho(0, width, 0, height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)

        self.font = pygame.font.SysFont('monospace', 14)
        self.title_font = pygame.font.SysFont('monospace', 24, bold=True)
        self.create_example_scenario()

    def create_example_scenario(self):
        p0 = self.detector.add_process(300, 300)
        p1 = self.detector.add_process(300, 500)
        r0 = self.detector.add_resource(700, 300, instances=1)
        r1 = self.detector.add_resource(700, 500, instances=1)
        self.detector.add_allocation_edge(r0, p0)
        self.detector.add_request_edge(p0, r1)
        self.detector.add_allocation_edge(r1, p1)
        self.detector.add_request_edge(p1, r0)
        self.detector.detect_deadlock()

    def draw_circle(self, x: float, y: float, radius: float, color: Tuple[float, float, float],
                    filled: bool = True, segments: int = 32):
        if filled:
            glBegin(GL_TRIANGLE_FAN)
        else:
            glBegin(GL_LINE_LOOP)
        glColor3f(*color)
        for i in range(segments + 1):
            angle = 2 * math.pi * i / segments
            glVertex2f(x + radius * math.cos(angle), y + radius * math.sin(angle))
        glEnd()

    def draw_rectangle(self, x: float, y: float, width: float, height: float,
                       color: Tuple[float, float, float], filled: bool = True):
        if filled:
            glBegin(GL_QUADS)
        else:
            glBegin(GL_LINE_LOOP)
        glColor3f(*color)
        glVertex2f(x - width / 2, y - height / 2)
        glVertex2f(x + width / 2, y - height / 2)
        glVertex2f(x + width / 2, y + height / 2)
        glVertex2f(x - width / 2, y + height / 2)
        glEnd()

    def draw_arrow(self, x1: float, y1: float, x2: float, y2: float,
                   color: Tuple[float, float, float], head_size: float = 15.0,
                   dashed: bool = False, animated_offset: float = 0.0):
        if dashed:
            dx, dy = x2 - x1, y2 - y1
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 0:
                dx /= dist;
                dy /= dist
                glColor3f(*color);
                glLineWidth(2.0);
                glBegin(GL_LINES)
                offset = animated_offset % 20.0
                curr = offset
                while curr < dist:
                    start = curr
                    end = min(curr + 10.0, dist)
                    glVertex2f(x1 + dx * start, y1 + dy * start)
                    glVertex2f(x1 + dx * end, y1 + dy * end)
                    curr += 20.0
                glEnd()
        else:
            glColor3f(*color);
            glLineWidth(3.0);
            glBegin(GL_LINES)
            glVertex2f(x1, y1);
            glVertex2f(x2, y2)
            glEnd()

        angle = math.atan2(y2 - y1, x2 - x1)
        node_radius = 35.0
        arrow_x = x2 - node_radius * math.cos(angle)
        arrow_y = y2 - node_radius * math.sin(angle)
        glBegin(GL_TRIANGLES)
        glVertex2f(arrow_x, arrow_y)
        glVertex2f(arrow_x - head_size * math.cos(angle - math.pi / 6),
                   arrow_y - head_size * math.sin(angle - math.pi / 6))
        glVertex2f(arrow_x - head_size * math.cos(angle + math.pi / 6),
                   arrow_y - head_size * math.sin(angle + math.pi / 6))
        glEnd()

    def draw_text(self, text: str, x: float, y: float, color: Tuple[int, int, int] = (255, 255, 255),
                  center: bool = True, font=None):
        if font is None: font = self.font
        surface = font.render(text, True, color)
        # MODIFIED: Text flip is no longer needed with corrected glOrtho
        text_data = pygame.image.tostring(surface, "RGBA", False)
        width, height = surface.get_size()

        glEnable(GL_TEXTURE_2D)
        texid = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texid)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, text_data)

        # Correct Y position for the inverted GL coordinate system
        y_gl = self.height - y
        if center:
            x -= width / 2
            y_gl -= height / 2

        glColor3f(1.0, 1.0, 1.0)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 1);
        glVertex2f(x, y_gl)
        glTexCoord2f(1, 1);
        glVertex2f(x + width, y_gl)
        glTexCoord2f(1, 0);
        glVertex2f(x + width, y_gl + height)
        glTexCoord2f(0, 0);
        glVertex2f(x, y_gl + height)
        glEnd()
        glDeleteTextures([texid])
        glDisable(GL_TEXTURE_2D)

    def draw_glow(self, x: float, y: float, radius: float, color: Tuple[float, float, float], intensity: float = 1.0):
        for i in range(5, 0, -1):
            alpha = 0.1 * intensity * (6 - i) / 5
            r = radius + i * 8
            glColor4f(color[0], color[1], color[2], alpha)
            glBegin(GL_TRIANGLE_FAN)
            glVertex2f(x, y)
            for j in range(32):
                angle = 2 * math.pi * j / 32
                glVertex2f(x + r * math.cos(angle), y + r * math.sin(angle))
            glEnd()

    def render(self):
        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()

        # Calculate pulse intensity once for the entire frame
        # Using a slower pulse for smoothness: math.sin(t) ranges -1 to 1, we map to 0.4 to 1.0
        pulse_val = (math.sin(self.detector.simulation_time * 3.0) + 1.0) / 2.0  # 0 to 1
        pulse_intensity = 0.4 + pulse_val * 0.6  # Smooth red intensity

        # Background
        glBegin(GL_QUADS)
        glColor3f(0.05, 0.05, 0.1);
        glVertex2f(0, 0);
        glVertex2f(self.width, 0)
        glColor3f(0.1, 0.1, 0.15);
        glVertex2f(self.width, self.height);
        glVertex2f(0, self.height)
        glEnd()

        self.draw_text("DEADLOCK DETECTION VISUALIZATION SYSTEM", self.width / 2, 40, (100, 200, 255),
                       font=self.title_font)

        # Edges
        for edge in self.detector.edges:
            source, target = self.detector.nodes[edge.source], self.detector.nodes[edge.target]

            # Base colors
            if edge.type == EdgeType.REQUEST:
                color = (1.0, 0.3, 0.3)
            else:
                color = (0.3, 1.0, 0.3)
            dashed = edge.type == EdgeType.REQUEST

            # ADDED: Smooth Pulsing Transition for Deadlocked Edges
            if self.detector.is_deadlocked and source.id in self.detector.deadlock_cycle and target.id in self.detector.deadlock_cycle:
                # Modulating only the red edge's brightness smoothly
                color = (pulse_intensity, 0.0, 0.0)

            self.draw_arrow(source.x, source.y, target.x, target.y, color, dashed=dashed,
                            animated_offset=edge.animated_offset)

        # Active adding edge
        if self.mode in ["adding_request", "adding_allocation"] and self.source_node is not None:
            mx, my = pygame.mouse.get_pos()
            my = self.height - my
            src = self.detector.nodes[self.source_node]
            self.draw_arrow(src.x, src.y, mx, my, (1.0, 1.0, 0.5), dashed=True)

        # Nodes
        for node in self.detector.nodes.values():
            if node.selected:
                self.draw_glow(node.x, node.y, 40, (1.0, 1.0, 0.0), 0.5 + (math.sin(node.pulse) + 1) * 0.25)
            elif self.detector.is_deadlocked and node.id in self.detector.deadlock_cycle:
                # ADDED: Smooth Pulsing Glow Transition for Deadlocked Nodes
                # We use the fast pulse already in Node for consistency
                # node_pulse = (math.sin(node.pulse*3)+1)*0.15 # This is fast
                # Let's use the slow, frame-based pulse for smoother visual
                self.draw_glow(node.x, node.y, 45, (1.0, 0.0, 0.0), 0.5 + pulse_val * 0.4)

            base_color = node.color

            # ADDED: Smooth Color Pulsing Transition for Deadlocked Nodes
            if self.detector.is_deadlocked and node.id in self.detector.deadlock_cycle:
                # Pulsing red color smoothly instead of switching
                base_color = (pulse_intensity, 0.1, 0.1)

            if node.type == NodeType.PROCESS:
                self.draw_circle(node.x, node.y, 30, base_color)
                self.draw_circle(node.x, node.y, 30, (0.8, 0.8, 0.8), filled=False)
            else:
                self.draw_rectangle(node.x, node.y, 50, 50, base_color)
                self.draw_rectangle(node.x, node.y, 50, 50, (0.8, 0.8, 0.8), filled=False)
                # Instance dots
                available = node.instances - node.allocated
                for i in range(node.instances):
                    dot_color = (0.0, 1.0, 0.0) if i < available else (1.0, 0.0, 0.0)
                    dot_x = node.x - (node.instances - 1) * 6 + i * 12
                    self.draw_circle(dot_x, node.y - 15, 4, dot_color)

            self.draw_text(node.label, node.x, node.y)

        self.draw_ui_panel()
        if self.show_help: self.draw_help_overlay()
        pygame.display.flip()

    def draw_ui_panel(self):
        px, py, pw, ph = 20, 80, 250, 500
        # OpenGL coordinates: convert top-down panel Y to bottom-up
        gl_py = self.height - py - ph
        glColor4f(0.1, 0.1, 0.2, 0.9);
        glBegin(GL_QUADS)
        glVertex2f(px, gl_py);
        glVertex2f(px + pw, gl_py);
        glVertex2f(px + pw, gl_py + ph);
        glVertex2f(px, gl_py + ph);
        glEnd()
        glColor3f(0.5, 0.5, 0.8);
        glLineWidth(2.0);
        glBegin(GL_LINE_LOOP)
        glVertex2f(px, gl_py);
        glVertex2f(px + pw, gl_py);
        glVertex2f(px + pw, gl_py + ph);
        glVertex2f(px, gl_py + ph);
        glEnd()

        y = py + 30
        status_color = (255, 100, 100) if self.detector.is_deadlocked else (100, 255, 100)
        status_txt = "⚠️ DEADLOCK!" if self.detector.is_deadlocked else "✓ Safe"
        self.draw_text(status_txt, px + pw / 2, y, status_color)

        y += 40
        self.draw_text(f"Processes: {len([n for n in self.detector.nodes.values() if n.type == NodeType.PROCESS])}",
                       px + 10, y, center=False)
        y += 25
        self.draw_text(f"Resources: {len([n for n in self.detector.nodes.values() if n.type == NodeType.RESOURCE])}",
                       px + 10, y, center=False)

        y += 60
        controls = ["P: Add Proc", "R: Add Res", "Q: Request", "A: Allocate", "DEL: Delete", "C: Clear", "H: Help",
                    "ESC: Exit"]
        for c in controls:
            self.draw_text(c, px + 10, y, (180, 180, 180), center=False)
            y += 25

        seq = self.detector.get_safe_sequence()
        if seq:
            self.draw_text(f"Safe Seq: {' -> '.join(seq)}", px + 10, y + 40, (100, 255, 100), center=False)

    def draw_help_overlay(self):
        ox, oy, ow, oh = 300, 150, 600, 400
        gl_oy = self.height - oy - oh
        glColor4f(0.0, 0.0, 0.0, 0.95);
        glBegin(GL_QUADS)
        glVertex2f(ox, gl_oy);
        glVertex2f(ox + ow, gl_oy);
        glVertex2f(ox + ow, gl_oy + oh);
        glVertex2f(ox, gl_oy + oh);
        glEnd()

        y = oy + 40
        self.draw_text("HELP MENU", ox + ow / 2, y, (100, 200, 255), font=self.title_font)
        y += 60
        help_lines = ["1. Press P/R to spawn nodes.", "2. Select a node (Click).",
                      "3. Press Q (Request) or A (Allocate).", "4. Click target node to finish edge.",
                      "5. Cycles trigger RED highlight."]
        for line in help_lines:
            self.draw_text(line, ox + 30, y, center=False);
            y += 30
        self.draw_text("Press H to close", ox + ow / 2, oy + oh - 30)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT: return False
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE: return False
                if event.key == K_h: self.show_help = not self.show_help

                if event.key == K_s:
                    self.step_mode = not self.step_mode
                if event.key == K_SPACE:
                    self.step_trigger = True

                if event.key == K_p: self.detector.add_process(random.randint(400, 800), random.randint(200, 600))
                if event.key == K_r: self.detector.add_resource(random.randint(400, 800), random.randint(200, 600),
                                                                random.randint(1, 3))
                if event.key == K_c: self.detector = DeadlockDetector(); self.selected_node = None
                if event.key == K_q and self.selected_node:
                    if self.detector.nodes[self.selected_node].type == NodeType.PROCESS:
                        self.mode, self.source_node = "adding_request", self.selected_node
                if event.key == K_a and self.selected_node:
                    if self.detector.nodes[self.selected_node].type == NodeType.RESOURCE:
                        self.mode, self.source_node = "adding_allocation", self.selected_node
                if event.key in [K_DELETE, K_BACKSPACE] and self.selected_node:
                    self.detector.edges = [e for e in self.detector.edges if
                                           e.source != self.selected_node and e.target != self.selected_node]
                    del self.detector.nodes[self.selected_node]
                    self.selected_node = None
                    self.detector.detect_deadlock()

            if event.type == MOUSEBUTTONDOWN:
                mx, my = event.pos
                my = self.height - my  # Convert to GL coordinates
                clicked = self.detector.get_node_at(mx, my)

                if self.mode == "adding_request" and self.source_node:
                    if clicked and self.detector.nodes[clicked].type == NodeType.RESOURCE:
                        self.detector.add_request_edge(self.source_node, clicked)
                        self.detector.detect_deadlock()
                    self.mode = "normal"
                elif self.mode == "adding_allocation" and self.source_node:
                    if clicked and self.detector.nodes[clicked].type == NodeType.PROCESS:
                        res = self.detector.nodes[self.source_node]
                        if res.allocated < res.instances:
                            self.detector.add_allocation_edge(self.source_node, clicked)
                            self.detector.detect_deadlock()
                        else:
                            print("⚠️ Resource is FULL")
                            self.detector.add_allocation_edge(self.source_node, clicked)
                            self.detector.detect_deadlock()
                    self.mode = "normal"
                else:
                    if self.selected_node: self.detector.nodes[self.selected_node].selected = False
                    self.selected_node = clicked
                    if clicked:
                        self.detector.nodes[clicked].selected = True
                        self.dragging_node = clicked

            if event.type == MOUSEBUTTONUP: self.dragging_node = None
            if event.type == MOUSEMOTION and self.dragging_node:
                mx, my = event.pos
                node = self.detector.nodes[self.dragging_node]
                node.x = node.target_x = mx
                node.y = node.target_y = self.height - my
        return True

    def run(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            dt = clock.tick(60) / 1000.0
            running = self.handle_events()
            if not self.step_mode or self.step_trigger:
                self.detector.update_layout(dt)
                self.step_trigger = False
            self.render()
        pygame.quit()


if __name__ == "__main__":
    app = OpenGLRenderer()
    app.run()