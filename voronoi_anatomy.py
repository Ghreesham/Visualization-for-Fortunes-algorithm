import tkinter as tk
import math
import random
import numpy as np
from scipy.spatial import Voronoi

class VoronoiAnatomy:
    def __init__(self, root):
        self.root = root
        self.root.title("Voronoi Diagram Anatomy")
        
        self.width = 800
        self.height = 600
        
        self.state = 1
        
        # 5 real nodes
        self.nodes = []
        self.generate_nodes()
        
        # Dummy points far outside the canvas to guarantee bounded finite regions for our real nodes
        self.dummy_nodes = [
            [-2000, -2000], [2800, -2000], [2800, 2600], [-2000, 2600]
        ]
        
        self.dragging = None
        self.anim_t = 0.0
        self.anim_dir = 1.0
        
        self.setup_ui()
        self.update_voronoi()
        self.draw()
        self.animate()

    def generate_nodes(self):
        padding = 100
        self.nodes = []
        for _ in range(5):
            x = random.randint(padding, self.width - padding)
            y = random.randint(padding, self.height - padding)
            self.nodes.append([x, y])

    def setup_ui(self):
        self.canvas = tk.Canvas(self.root, width=self.width, height=self.height, bg="#1e1e2e")
        self.canvas.pack(padx=10, pady=10)
        
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        
        control_frame = tk.Frame(self.root, bg="#1e1e2e")
        control_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        btn_style = {"font": ("Helvetica", 11, "bold"), "fg": "white", "bg": "#313244", "activebackground": "#45475a", "activeforeground": "white", "relief": tk.FLAT, "padx": 10, "pady": 5}
        
        self.btn_state1 = tk.Button(control_frame, text="1. Regions", command=lambda: self.set_state(1), **btn_style)
        self.btn_state1.pack(side=tk.LEFT, padx=5)
        
        self.btn_state2 = tk.Button(control_frame, text="2. Edge Property", command=lambda: self.set_state(2), **btn_style)
        self.btn_state2.pack(side=tk.LEFT, padx=5)
        
        self.btn_state3 = tk.Button(control_frame, text="3. Vertex Property", command=lambda: self.set_state(3), **btn_style)
        self.btn_state3.pack(side=tk.LEFT, padx=5)
        
        self.btn_state4 = tk.Button(control_frame, text="4. Empty Circle", command=lambda: self.set_state(4), **btn_style)
        self.btn_state4.pack(side=tk.LEFT, padx=5)
        
        tk.Button(control_frame, text="Randomize Nodes", command=self.do_randomize, **btn_style).pack(side=tk.RIGHT, padx=5)
        
        self.update_buttons()

    def do_randomize(self):
        self.generate_nodes()
        self.update_voronoi()
        self.draw()

    def set_state(self, new_state):
        self.state = new_state
        self.update_buttons()
        self.draw()

    def update_buttons(self):
        active_bg = "#89b4fa"
        default_bg = "#313244"
        self.btn_state1.config(bg=active_bg if self.state == 1 else default_bg)
        self.btn_state2.config(bg=active_bg if self.state == 2 else default_bg)
        self.btn_state3.config(bg=active_bg if self.state == 3 else default_bg)
        self.btn_state4.config(bg=active_bg if self.state == 4 else default_bg)

    def dist(self, p1, p2):
        return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

    def update_voronoi(self):
        all_points = self.nodes + self.dummy_nodes
        self.vor = Voronoi(all_points)
        
        # Pre-calculate data for states
        self.real_regions = []
        for i in range(5):
            reg_idx = self.vor.point_region[i]
            reg_vertices = self.vor.regions[reg_idx]
            coords = []
            for v_idx in reg_vertices:
                if v_idx != -1:
                    coords.append(self.vor.vertices[v_idx])
            self.real_regions.append((i, coords))
            
        # Find a shared edge between two real nodes
        self.target_edge = None
        for i, ridge in enumerate(self.vor.ridge_points):
            p1, p2 = ridge
            if p1 < 5 and p2 < 5: # Both are real nodes
                v1_idx, v2_idx = self.vor.ridge_vertices[i]
                if v1_idx != -1 and v2_idx != -1:
                    v1 = self.vor.vertices[v1_idx]
                    v2 = self.vor.vertices[v2_idx]
                    self.target_edge = (p1, p2, v1, v2)
                    break
                    
        # Find a vertex shared by at least 3 real nodes
        vertex_to_nodes = {}
        for i in range(5):
            reg_idx = self.vor.point_region[i]
            for v_idx in self.vor.regions[reg_idx]:
                if v_idx != -1:
                    vertex_to_nodes.setdefault(v_idx, []).append(i)
                    
        self.target_vertex = None
        for v_idx, nodes in vertex_to_nodes.items():
            if len(nodes) >= 3:
                self.target_vertex = (self.vor.vertices[v_idx], nodes[:3])
                break

    def on_press(self, event):
        x, y = event.x, event.y
        for i, s in enumerate(self.nodes):
            if self.dist((x, y), s) < 15:
                self.dragging = i
                return

    def on_drag(self, event):
        if self.dragging is None:
            return
        x = max(0, min(self.width, event.x))
        y = max(0, min(self.height, event.y))
        self.nodes[self.dragging] = [x, y]
        self.update_voronoi()
        self.draw()

    def on_release(self, event):
        self.dragging = None

    def animate(self):
        # Update animation parameter
        self.anim_t += 0.02 * self.anim_dir
        if self.anim_t >= 1.0:
            self.anim_t = 1.0
            self.anim_dir = -1.0
        elif self.anim_t <= 0.0:
            self.anim_t = 0.0
            self.anim_dir = 1.0
            
        if self.state == 2:
            self.draw()
            
        self.root.after(30, self.animate)

    def draw(self):
        self.canvas.delete("all")
        
        color_node = "#a6e3a1"
        color_node_highlight = "#f9e2af"
        color_poly_line = "#585b70"
        color_poly_fill = "#313244"
        color_accent = "#cba6f7"
        color_accent2 = "#f38ba8"
        
        # 1. Draw Regions
        for idx, coords in self.real_regions:
            if len(coords) > 2:
                flat_coords = []
                for p in coords:
                    flat_coords.extend(p)
                self.canvas.create_polygon(flat_coords, outline=color_poly_line, fill=color_poly_fill, width=2)
                
        # 2. State Specific Overlays
        if self.state == 1:
            self.canvas.create_text(self.width//2, 30, text="", fill="white", font=("Helvetica", 14, "bold"))
            
        elif self.state == 2 and self.target_edge:
            p1_idx, p2_idx, v1, v2 = self.target_edge
            p1, p2 = self.nodes[p1_idx], self.nodes[p2_idx]
            
            # Highlight Edge
            self.canvas.create_line(v1[0], v1[1], v2[0], v2[1], fill=color_accent, width=5)
            
            # Moving point M
            mx = v1[0] + self.anim_t * (v2[0] - v1[0])
            my = v1[1] + self.anim_t * (v2[1] - v1[1])
            self.canvas.create_oval(mx-6, my-6, mx+6, my+6, fill="white")
            
            # Lines to adjacent nodes
            self.canvas.create_line(mx, my, p1[0], p1[1], fill=color_accent, dash=(5, 5), width=2)
            self.canvas.create_line(mx, my, p2[0], p2[1], fill=color_accent, dash=(5, 5), width=2)
            
            # Highlight the two nodes
            self.canvas.create_oval(p1[0]-12, p1[1]-12, p1[0]+12, p1[1]+12, outline=color_accent, width=3)
            self.canvas.create_oval(p2[0]-12, p2[1]-12, p2[0]+12, p2[1]+12, outline=color_accent, width=3)
            
            # Text
            d = self.dist((mx, my), p1)
            self.canvas.create_text(mx, my-20, text=f"d={d:.0f}", fill="white", font=("Helvetica", 12))
            self.canvas.create_text(self.width//2, 30, text=None, fill="white", font=("Helvetica", 14, "bold"))

        elif self.state in [3, 4] and self.target_vertex:
            vx, vy = self.target_vertex[0]
            nodes_idx = self.target_vertex[1]
            nodes = [self.nodes[i] for i in nodes_idx]
            
            # Highlight Vertex
            self.canvas.create_oval(vx-8, vy-8, vx+8, vy+8, fill=color_accent2, outline="white", width=2)
            
            for p in nodes:
                # Highlight the three nodes
                self.canvas.create_oval(p[0]-12, p[1]-12, p[0]+12, p[1]+12, outline=color_accent2, width=3)
                if self.state == 3:
                    self.canvas.create_line(vx, vy, p[0], p[1], fill=color_accent2, dash=(5, 5), width=2)
            
            if self.state == 3:
                self.canvas.create_text(self.width//2, 30, text=None, fill="white", font=("Helvetica", 14, "bold"))
            
            if self.state == 4:
                radius = self.dist((vx, vy), nodes[0])
                self.canvas.create_oval(vx-radius, vy-radius, vx+radius, vy+radius, outline=color_accent2, width=3)
                self.canvas.create_text(self.width//2, 30, text=None, fill="white", font=("Helvetica", 14, "bold"))
                
                # Fill circle with faint color
                self.canvas.create_oval(vx-radius, vy-radius, vx+radius, vy+radius, fill=color_accent2, stipple="gray25")

        # 3. Draw Nodes
        for i, (x, y) in enumerate(self.nodes):
            self.canvas.create_oval(x - 8, y - 8, x + 8, y + 8, fill=color_node, outline="white", width=2)
            self.canvas.create_text(x, y-20, text=f"p{i+1}", fill="white", font=("Helvetica", 10, "bold"))

if __name__ == "__main__":
    root = tk.Tk()
    root.configure(bg="#1e1e2e")
    app = VoronoiAnatomy(root)
    root.mainloop()
