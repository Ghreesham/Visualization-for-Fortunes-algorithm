import pygame
import numpy as np
from scipy.spatial import Voronoi
import sys

# --- Configuration & Styling ---
WIDTH, HEIGHT = 800, 800
FPS = 60

# Colors
BG_COLOR = (20, 20, 25)
SWEEPLINE_COLOR = (255, 80, 80)  # Bright red
BEACHLINE_COLOR = (255, 204, 0)  # Bright yellow for the active front
VORONOI_COLOR = (255, 255, 255)  # White for the locked-in edges
TEXT_COLOR = (200, 200, 200)
POINT_COLORS = [
    (255, 153, 153), (102, 179, 255), (153, 255, 153),
    (255, 204, 153), (194, 194, 240)
]


def get_parabola_y(x, px, py, sweep_y):
    """Calculates the Y coordinate of a parabola."""
    if sweep_y <= py:
        return None
    return ((x - px) ** 2 + py ** 2 - sweep_y ** 2) / (2.0 * (py - sweep_y))


def get_voronoi_data(points):
    """Calculates final Voronoi edges to use as the trace path."""
    if len(points) < 2:
        return []
    dummies = np.array([[-5000, -5000], [5000, -5000], [5000, 5000], [-5000, 5000]])
    all_points = np.vstack([points, dummies])

    vor = Voronoi(all_points)
    edges = []

    for i, simplex in enumerate(vor.ridge_vertices):
        if -1 not in simplex:
            p1 = vor.vertices[simplex[0]]
            p2 = vor.vertices[simplex[1]]
            seed_idx = vor.ridge_points[i][0]
            seed = all_points[seed_idx]
            edges.append((np.array(p1), np.array(p2), np.array(seed)))

    return edges


def get_swept_segment(p1, p2, seed, sweep_y):
    """
    Determines how much of a Voronoi edge has been swept over.
    A point P is 'locked in' when: P.y + distance(P, seed) <= sweep_y
    """

    def v(pt):
        return pt[1] + np.linalg.norm(pt - seed)

    v1, v2 = v(p1), v(p2)

    # Both endpoints locked in -> draw full line
    if v1 <= sweep_y and v2 <= sweep_y:
        return p1, p2
    # Neither endpoint reached -> draw nothing
    if v1 > sweep_y and v2 > sweep_y:
        return None

    # One endpoint locked in -> binary search to find the exact cut point
    t_low, t_high = 0.0, 1.0
    swap = False

    # Ensure p1 is the 'locked in' side
    if v1 > sweep_y:
        p1, p2 = p2, p1
        swap = True

    for _ in range(10):  # 10 iterations is plenty for pixel accuracy
        t_mid = (t_low + t_high) / 2
        p_mid = p1 + t_mid * (p2 - p1)
        if v(p_mid) <= sweep_y:
            t_low = t_mid
        else:
            t_high = t_mid

    cut_point = p1 + t_low * (p2 - p1)

    if swap:
        return cut_point, p1
    else:
        return p1, cut_point


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Fortune's Algorithm: Complete Visualization")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 16)

    # State variables
    points = [(400, 200), (250, 350), (600, 450)]
    sweep_y = 0.0
    playing = False
    sweep_speed = 2.0
    show_full_parabolas = True

    x_coords = list(range(0, WIDTH + 1, 4))

    while True:
        # 1. Handle Input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    playing = not playing
                elif event.key == pygame.K_r:
                    sweep_y = 0.0
                elif event.key == pygame.K_c:
                    points = []
                    sweep_y = 0.0
                elif event.key == pygame.K_p:
                    show_full_parabolas = not show_full_parabolas

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    points.append(event.pos)

        # 2. Update Physics
        if playing:
            sweep_y += sweep_speed
            if sweep_y > HEIGHT + 200:
                sweep_y = 0.0

                # 3. Draw
        screen.fill(BG_COLOR)

        beachline_points = []

        # Calculate parabolas and beachline
        for x in x_coords:
            max_y = -float('inf')
            for pt in points:
                px, py = pt
                if sweep_y > py:
                    y = get_parabola_y(x, px, py, sweep_y)
                    if y is not None and y > max_y:
                        max_y = y
            if max_y > -float('inf'):
                beachline_points.append((x, max_y))

        # Draw full faint parabolas
        if show_full_parabolas:
            for i, pt in enumerate(points):
                px, py = pt
                if sweep_y > py:
                    color = POINT_COLORS[i % len(POINT_COLORS)]
                    curve = []
                    for x in x_coords:
                        y = get_parabola_y(x, px, py, sweep_y)
                        if y is not None and -200 < y < HEIGHT + 200:
                            curve.append((x, y))
                    if len(curve) > 2:
                        pygame.draw.aalines(screen, color, False, curve)

        # Draw the real-time Voronoi edges
        voronoi_edges = get_voronoi_data(points)
        for p1, p2, seed in voronoi_edges:
            segment = get_swept_segment(p1, p2, seed, sweep_y)
            if segment:
                start_pos, end_pos = segment
                pygame.draw.line(screen, VORONOI_COLOR, start_pos.astype(int), end_pos.astype(int), 3)

        # Draw the thick yellow Beach Line
        if len(beachline_points) > 2:
            pygame.draw.lines(screen, BEACHLINE_COLOR, False, beachline_points, 4)

        # Draw the Sweepline
        pygame.draw.line(screen, SWEEPLINE_COLOR, (0, sweep_y), (WIDTH, sweep_y), 2)

        # Draw Seed Points
        for i, pt in enumerate(points):
            color = POINT_COLORS[i % len(POINT_COLORS)]
            pygame.draw.circle(screen, color, pt, 6)

        # Draw UI overlay
        ui_text = [
            "CONTROLS:",
            "[SPACE] Play/Pause",
            "[CLICK] Add Seed Point",
            "[R]     Restart Sweepline",
            "[C]     Clear Map",
            f"[P]     Toggle Full Parabolas: {'ON' if show_full_parabolas else 'OFF'}"
        ]
        for i, text in enumerate(ui_text):
            text_surface = font.render(text, True, TEXT_COLOR)
            screen.blit(text_surface, (10, 10 + (i * 22)))

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()