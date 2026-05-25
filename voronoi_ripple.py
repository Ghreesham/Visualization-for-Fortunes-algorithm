import pygame
import numpy as np
from scipy.spatial import Voronoi
import sys

# --- Configuration & Styling ---
WIDTH, HEIGHT = 800, 800
FPS = 60

# Colors
BG_COLOR = (20, 20, 25)
FUTURE_LINE_COLOR = (80, 80, 80)  # Faint grey for the full grid
REALTIME_LINE_COLOR = (255, 255, 255)  # Bright white for the colliding lines
TEXT_COLOR = (200, 200, 200)
POINT_COLORS = [
    (255, 153, 153),  # Red-ish
    (102, 179, 255),  # Blue-ish
    (153, 255, 153),  # Green-ish
    (255, 204, 153),  # Orange-ish
    (194, 194, 240)  # Purple-ish
]


def get_voronoi_data(points):
    """Calculates Voronoi edges and maps them to their seed points."""
    if len(points) < 2:
        return []
    # Dummy points far outside the screen to force closed regions
    dummies = np.array([[-5000, -5000], [5000, -5000], [5000, 5000], [-5000, 5000]])
    all_points = np.vstack([points, dummies])

    vor = Voronoi(all_points)
    edges = []

    for i, simplex in enumerate(vor.ridge_vertices):
        if -1 not in simplex:
            p1 = vor.vertices[simplex[0]]
            p2 = vor.vertices[simplex[1]]
            # Get one of the two seed points that generated this edge
            seed_idx = vor.ridge_points[i][0]
            seed = all_points[seed_idx]
            edges.append((p1, p2, seed))

    return edges


def get_active_segment(p1, p2, seed, r):
    """Calculates which part of the Voronoi edge is currently colliding with the ripples."""
    # Vector math to find the intersection of the line segment (p1 -> p2) and circle (seed, r)
    u = p1 - seed
    v = p2 - p1
    a = np.dot(v, v)

    if a == 0: return None

    b = 2 * np.dot(u, v)
    c = np.dot(u, u) - r ** 2

    discriminant = b ** 2 - 4 * a * c
    if discriminant < 0:
        return None  # The circles haven't touched this boundary line yet

    sqrt_d = np.sqrt(discriminant)
    t1 = (-b - sqrt_d) / (2 * a)
    t2 = (-b + sqrt_d) / (2 * a)

    # We only want the segment between p1 (t=0) and p2 (t=1)
    t_start = max(0.0, min(t1, t2))
    t_end = min(1.0, max(t1, t2))

    if t_start > t_end:
        return None

    start_pos = p1 + t_start * v
    end_pos = p1 + t_end * v
    return start_pos, end_pos


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Voronoi Expanding Ripples Simulation")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 16)

    # State variables
    points = [(300, 400), (500, 400)]  # Start with 2 points
    radius = 0.0
    playing = False
    show_future_lines = False
    expansion_speed = 3.0

    while True:
        # 1. Handle Input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    playing = not playing  # Pause / Play
                elif event.key == pygame.K_r:
                    radius = 0.0  # Restart ripples
                elif event.key == pygame.K_c:
                    points = []  # Clear all points
                    radius = 0.0
                elif event.key == pygame.K_v:
                    show_future_lines = not show_future_lines  # Toggle Voronoi grid

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    points.append(event.pos)

        # 2. Update Physics
        if playing:
            radius += expansion_speed

        # 3. Draw
        screen.fill(BG_COLOR)

        voronoi_edges = get_voronoi_data(points)

        # Draw the full Voronoi grid faintly (if toggled on)
        if show_future_lines:
            for p1, p2, _ in voronoi_edges:
                pygame.draw.aaline(screen, FUTURE_LINE_COLOR, p1, p2)

        # Draw real-time collision boundaries
        for p1, p2, seed in voronoi_edges:
            segment = get_active_segment(p1, p2, seed, radius)
            if segment:
                start_pos, end_pos = segment
                pygame.draw.line(screen, REALTIME_LINE_COLOR, start_pos, end_pos, 4)

        # Draw Expanding Circles & Points
        for i, pt in enumerate(points):
            color = POINT_COLORS[i % len(POINT_COLORS)]

            # Draw Ripple
            if radius > 0:
                pygame.draw.circle(screen, color, pt, int(radius), width=2)

            # Draw Seed Point
            pygame.draw.circle(screen, color, pt, 6)

        # Draw UI overlay
        ui_text = [
            "CONTROLS:",
            "[SPACE] Play/Pause",
            "[CLICK] Add Pebble",
            "[R]     Restart Ripples",
            "[C]     Clear Map",
            f"[V]     Toggle Future Grid: {'ON' if show_future_lines else 'OFF'}",
            f"Status: {'PLAYING' if playing else 'PAUSED'}"
        ]

        for i, text in enumerate(ui_text):
            text_surface = font.render(text, True, TEXT_COLOR)
            screen.blit(text_surface, (10, 10 + (i * 22)))

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()