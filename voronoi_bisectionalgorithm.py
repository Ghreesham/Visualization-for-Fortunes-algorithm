import tkinter as tk
import math
import random

class VoronoiAlgorithm:
    def __init__(self, root):
        self.root = root
        self.root.title("Voronoi Generation Algorithm")
        
        self.width = 800
        self.height = 600
        
        # 5 real nodes
        self.nodes = []
        self.generate_nodes()
        
        self.pad = 50
        self.initial_box = [
            (self.pad, self.pad),
            (self.width - self.pad, self.pad),
            (self.width - self.pad, self.height - self.pad),
            (self.pad, self.height - self.pad)
        ]
        
        self.reset_algorithm()
        self.setup_ui()
        self.draw()

    def generate_nodes(self):
        padding = 100
        self.nodes = []
        for _ in range(5):
            x = random.randint(padding, self.width - padding)
            y = random.randint(padding, self.height - padding)
            self.nodes.append((x, y))

    def reset_algorithm(self):
        self.current_i = 0
        self.current_j = 0
        self.substep = 1 # 1: Show Bisector, 2: Slice
        
        self.finished_cells = []
        self.current_cell = list(self.initial_box)
        
        self.next_cell = None
        self.discarded_cell = None
        self.bisector_line = None
        self.intersections = []

    def do_reset(self):
        self.reset_algorithm()
        self.draw()

    def do_randomize(self):
        self.generate_nodes()
        self.reset_algorithm()
        self.draw()

    def setup_ui(self):
        self.canvas = tk.Canvas(self.root, width=self.width, height=self.height, bg="#1e1e2e")
        self.canvas.pack(padx=10, pady=10)
        
        control_frame = tk.Frame(self.root, bg="#1e1e2e")
        control_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        btn_style = {"font": ("Helvetica", 11, "bold"), "fg": "white", "bg": "#313244", "activebackground": "#45475a", "activeforeground": "white", "relief": tk.FLAT, "padx": 10, "pady": 5}
        highlight_btn = {"font": ("Helvetica", 11, "bold"), "fg": "white", "bg": "#cba6f7", "activebackground": "#b4befe", "activeforeground": "white", "relief": tk.FLAT, "padx": 10, "pady": 5}
        
        tk.Button(control_frame, text="Next Step", command=self.step_forward, **highlight_btn).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="Reset Algorithm", command=self.do_reset, **btn_style).pack(side=tk.LEFT, padx=5)
        
        tk.Button(control_frame, text="Randomize Nodes", command=self.do_randomize, **btn_style).pack(side=tk.RIGHT, padx=5)

    def intersect_halfplane(self, poly, M, N):
        """Intersects a polygon with a half-plane. N points towards the inside."""
        new_poly = []
        if not poly: return []
        for i in range(len(poly)):
            A = poly[i]
            B = poly[(i+1) % len(poly)]
            
            valA = (A[0] - M[0]) * N[0] + (A[1] - M[1]) * N[1]
            valB = (B[0] - M[0]) * N[0] + (B[1] - M[1]) * N[1]
            
            insideA = valA >= -1e-9
            insideB = valB >= -1e-9
            
            if insideA:
                new_poly.append(A)
                
            if insideA != insideB:
                denom = (B[0] - A[0]) * N[0] + (B[1] - A[1]) * N[1]
                if abs(denom) > 1e-9:
                    t = -valA / denom
                    I = (A[0] + t * (B[0] - A[0]), A[1] + t * (B[1] - A[1]))
                    new_poly.append(I)
        return new_poly

    def step_forward(self):
        if self.current_i >= len(self.nodes):
            return # Done
            
        if self.substep == 1:
            # Skip self
            while self.current_j == self.current_i:
                self.current_j += 1
                
            if self.current_j >= len(self.nodes):
                # Finished this site's cell
                self.finished_cells.append(list(self.current_cell))
                self.current_i += 1
                self.current_j = 0
                if self.current_i < len(self.nodes):
                    self.current_cell = list(self.initial_box)
                    self.substep = 1
                    self.step_forward() # auto process to first j
                else:
                    self.draw()
                return

            # Compute intersection for rendering
            p_i = self.nodes[self.current_i]
            p_j = self.nodes[self.current_j]
            
            M = ((p_i[0] + p_j[0]) / 2, (p_i[1] + p_j[1]) / 2)
            N = (p_i[0] - p_j[0], p_i[1] - p_j[1])
            
            if N[0] != 0 or N[1] != 0:
                self.next_cell = self.intersect_halfplane(self.current_cell, M, N)
                # Discarded cell is the opposite half-plane
                N_opp = (-N[0], -N[1])
                self.discarded_cell = self.intersect_halfplane(self.current_cell, M, N_opp)
                
                # Bisector line for drawing (extend far out)
                perp = (-N[1], N[0])
                length = math.hypot(*perp)
                if length > 0:
                    px, py = perp[0]/length * 2000, perp[1]/length * 2000
                    self.bisector_line = ((M[0] - px, M[1] - py), (M[0] + px, M[1] + py))
                
                # Find the intersection points (t, u) between current_cell and bisector
                self.intersections = []
                for p in self.next_cell:
                    # Check if p is on the bisector line
                    val = (p[0] - M[0]) * N[0] + (p[1] - M[1]) * N[1]
                    if abs(val) < 1e-4:
                        self.intersections.append(p)
                        
            self.substep = 2
            
        elif self.substep == 2:
            # Commit the slice
            if self.next_cell is not None:
                self.current_cell = list(self.next_cell)
            self.current_j += 1
            self.substep = 1
            
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        
        color_node = "#a6e3a1"
        color_node_active = "#cba6f7"
        color_node_neighbor = "#f9e2af"
        
        color_poly_line = "#585b70"
        color_poly_fill = "#313244"
        color_poly_active_fill = "#45475a"
        color_poly_discard = "#f38ba8" # red for discarding
        
        # Draw finished cells
        for cell in self.finished_cells:
            if len(cell) > 2:
                coords = []
                for p in cell: coords.extend(p)
                self.canvas.create_polygon(coords, outline=color_poly_line, fill=color_poly_fill, width=2)
                
        # Draw initial box bound lightly to show boundary
        box_coords = []
        for p in self.initial_box: box_coords.extend(p)
        self.canvas.create_polygon(box_coords, outline="#1e1e2e", fill="", width=1, dash=(5, 5))

        if self.current_i < len(self.nodes):
            # Draw current active cell
            if len(self.current_cell) > 2:
                coords = []
                for p in self.current_cell: coords.extend(p)
                self.canvas.create_polygon(coords, outline=color_poly_line, fill=color_poly_active_fill, width=3)
                
            if self.substep == 2:
                # We are showing the bisector and discarded region
                p_i = self.nodes[self.current_i]
                p_j = self.nodes[self.current_j]
                
                # Draw discarded region in red
                if self.discarded_cell and len(self.discarded_cell) > 2:
                    coords = []
                    for p in self.discarded_cell: coords.extend(p)
                    self.canvas.create_polygon(coords, outline=color_poly_discard, fill=color_poly_discard, stipple="gray25", width=2)
                
                # Draw connecting line
                self.canvas.create_line(p_i[0], p_i[1], p_j[0], p_j[1], fill=color_node_neighbor, dash=(5, 5), width=2)
                
                # Draw bisector line
                if self.bisector_line:
                    l1, l2 = self.bisector_line
                    self.canvas.create_line(l1[0], l1[1], l2[0], l2[1], fill="#94e2d5", width=2)
                    
                # Draw intersection points (t, u)
                for ix, iy in self.intersections:
                    self.canvas.create_oval(ix-5, iy-5, ix+5, iy+5, fill="#94e2d5", outline="white")
                    self.canvas.create_text(ix+15, iy-15, text="t/u", fill="white", font=("Helvetica", 10, "bold"))
                    
            # Draw overlay text
            j_idx = self.current_j if self.substep == 2 else self.current_j - 1
            if j_idx < 0: j_idx = 0
            if j_idx == self.current_i: j_idx += 1
            
            if self.substep == 2:
                txt = f"Building cell for p{self.current_i+1} | Slicing with bisector of p{j_idx+1}"
            else:
                txt = f"Building cell for p{self.current_i+1} | Click Next Step"
            self.canvas.create_text(self.width//2, 20, text=txt, fill="white", font=("Helvetica", 14, "bold"))
        else:
            self.canvas.create_text(self.width//2, 20, text="Algorithm Complete!", fill="#a6e3a1", font=("Helvetica", 16, "bold"))

        # Draw nodes
        for i, (x, y) in enumerate(self.nodes):
            fill = color_node
            outline = "white"
            width = 2
            if i == self.current_i:
                fill = color_node_active
                width = 4
            elif self.substep == 2 and i == self.current_j:
                fill = color_node_neighbor
                width = 3
                
            self.canvas.create_oval(x - 8, y - 8, x + 8, y + 8, fill=fill, outline=outline, width=width)
            self.canvas.create_text(x, y-20, text=f"p{i+1}", fill="white", font=("Helvetica", 10, "bold"))

if __name__ == "__main__":
    root = tk.Tk()
    root.configure(bg="#1e1e2e")
    app = VoronoiAlgorithm(root)
    root.mainloop()
