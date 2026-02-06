import time

EXPOSED_POINTS = {(0,1), (1,2), (3,9)}
GRID_SIZE = (5, 10)

# --- Piece Utilities ---
def rotate(piece):
    return [(y, -x) for (x, y) in piece]

def flip(piece):
    return [(x, -y) for (x, y) in piece]

def normalize(piece):
    min_x = min(x for x, y in piece)
    min_y = min(y for x, y in piece)
    return sorted([(x - min_x, y - min_y) for x, y in piece])

def all_orientations(piece):
    orientations = set()
    p = piece
    for _ in range(4):
        norm = tuple(normalize(p))
        orientations.add(norm)
        flipped = tuple(normalize(flip(p)))
        orientations.add(flipped)
        p = rotate(p)
    return [list(orientation) for orientation in orientations]

def visualize_piece(piece, symbol='#'):
    min_r = min(x for x, y in piece)
    min_c = min(y for x, y in piece)
    max_r = max(x for x, y in piece)
    max_c = max(y for x, y in piece)
    vis_rows = max_r - min_r + 1
    vis_cols = max_c - min_c + 1
    vis_grid = [['.' for _ in range(vis_cols)] for _ in range(vis_rows)]
    for x, y in piece:
        vis_grid[x - min_r][y - min_c] = symbol
    for row in vis_grid:
        print(' '.join(row))

def print_and_save_solution(solution, grid_size=GRID_SIZE, exposed_points=EXPOSED_POINTS, filename="solution.txt", state=None):
    print("Solution found!")
    print(f"Exposed points: {sorted(exposed_points)}")
    rows, cols = grid_size
    grid_vis = [['.' for _ in range(cols)] for _ in range(rows)]
    for idx, (piece_idx, orientation, (base_r, base_c)) in enumerate(solution):
        symbol = str((piece_idx+1)%10)
        for dr, dc in orientation:
            r, c = base_r + dr, base_c + dc
            if 0 <= r < rows and 0 <= c < cols:
                grid_vis[r][c] = symbol
    for (r, c) in exposed_points:
        grid_vis[r][c] = 'X'
    import os
    base, ext = os.path.splitext(filename)
    new_filename = filename
    counter = 1
    while os.path.exists(new_filename):
        new_filename = f"{base}_{counter}{ext}"
        counter += 1
    # Get stats from solve_tiling state
    from inspect import currentframe
    frame = currentframe()
    iter_nodes = None
    elapsed_time = None
    if frame is not None:
        outer = frame.f_back
        if outer is not None and 'state' in outer.f_locals:
            state = outer.f_locals['state']
            iter_nodes = state.get('calls')
            elapsed_time = time.time() - state.get('start', time.time())
    with open(new_filename, "w") as f:
        points = sorted(exposed_points)
        header = "visualization of the solution to "
        header += "(" + ", ".join(str(p) for p in points) + "):" + "\n"
        f.write(header)
        for row in grid_vis:
            f.write(' '.join(row) + '\n')
        # Save stats
        if iter_nodes is not None and elapsed_time is not None:
            f.write(f"\nFinal nodes iterated: {iter_nodes}\n")
            f.write(f"Elapsed time: {elapsed_time:.2f} seconds\n")
        if state is not None:
            total = state.get('total', 0)
            calls = state.get('calls', 0)
            start = state.get('start', time.time())
            elapsed = time.time() - start
            percent = 100.0 * calls / total if total > 0 else 0
            bar_length = 40
            filled_length = int(bar_length * percent // 100)
            bar = '=' * filled_length + '-' * (bar_length - filled_length)
            progress_str = f"[{bar}] {percent:.4f}% | {calls} nodes | elapsed: {elapsed:.1f}s"
            f.write(f"Final progress: {progress_str}\n")
    print(f"Solution saved to {new_filename}")
    print("\nSolution visualization:")
    for row in grid_vis:
        print(' '.join(row))

# --- Solver ---
def solve_tiling(grid_size=GRID_SIZE, exposed_points=EXPOSED_POINTS, debug=True):
    rows, cols = grid_size
    all_cells = {(r, c) for r in range(rows) for c in range(cols)}
    to_cover = all_cells - exposed_points
    all_piece_orientations = [all_orientations(piece) for piece in lego_pieces]
    total_iterations = 1
    for orientations in all_piece_orientations:
        piece_max = 0
        for orient in orientations:
            min_r = min(x for x, y in orient)
            min_c = min(y for x, y in orient)
            max_r = max(x for x, y in orient)
            max_c = max(y for x, y in orient)
            count = max(0, (rows - (max_r - min_r))) * max(0, (cols - (max_c - min_c)))
            piece_max += count
        total_iterations *= piece_max if piece_max > 0 else 1
    state = {
        'calls': 0,
        'start': time.time(),
        'last_print': time.time(),
        'total': total_iterations,
        'progress_width': 0,
    }

    def can_place(covered, orientation, base_r, base_c):
        positions = []
        for dr, dc in orientation:
            r, c = base_r + dr, base_c + dc
            if (r, c) in exposed_points:
                return None
            if not (0 <= r < rows and 0 <= c < cols):
                return None
            if (r, c) in covered:
                return None
            positions.append((r, c))
        return positions

    import sys
    def print_progress(piece_idx, placements, covered):
        elapsed = time.time() - state['start']
        percent = 100.0 * state['calls'] / state['total'] if state['total'] > 0 else 0
        bar_length = 40
        filled_length = int(bar_length * percent // 100)
        bar = '=' * filled_length + '-' * (bar_length - filled_length)
        progress_str = f"[{bar}] {percent:.4f}% | {state['calls']} nodes | elapsed: {elapsed:.1f}s"
        state['progress_width'] = max(state['progress_width'], len(progress_str))
        padded_progress = progress_str.ljust(state['progress_width'])
        sys.stdout.write(f"\r\033[K{padded_progress}")
        sys.stdout.flush()

    def backtrack(piece_idx, covered, placements):
        state['calls'] += 1
        if debug and state['calls'] % 1000 == 0:
            now = time.time()
            if now - state['last_print'] > 1:
                print_progress(piece_idx, placements, covered)
                state['last_print'] = now
        if piece_idx == len(lego_pieces):
            if covered == to_cover:
                print_progress(piece_idx, placements, covered)
                return placements
            return None
        for orientation in all_piece_orientations[piece_idx]:
            min_r = min(x for x, y in orientation)
            min_c = min(y for x, y in orientation)
            max_r = max(x for x, y in orientation)
            max_c = max(y for x, y in orientation)
            for base_r in range(rows - (max_r - min_r)):
                for base_c in range(cols - (max_c - min_c)):
                    pos = can_place(covered, orientation, base_r, base_c)
                    if pos is not None:
                        result = backtrack(piece_idx + 1, covered | set(pos), placements + [(piece_idx, orientation, (base_r, base_c))])
                        if result is not None:
                            return result
        return None

    solution = backtrack(0, set(), [])
    return solution, state


# --- Lego Pieces ---
lego_pieces = [
    [(0,0), (1,0), (1,1), (2,1), (3,1)],
    [(0,0), (1,0), (1,1), (1,2), (2,2)],
    [(0,0), (1,0), (1,1), (2,0), (3,0)],
    [(0,0), (1,0), (1,1), (1,2), (2,1), (2,2)],
    [(0,0), (1,0), (1,1), (1,2), (1,3)],
    [(0,0), (1,0), (1,1), (1,2), (0,2)],
    [(0,0), (1,0), (2,0), (2,1), (2,2)],
    [(0,0), (0,1), (1,0), (1,1), (1,2)],
    [(0,0), (0,1), (0,2), (1,0), (1,1), (1,2)],
]

# --- Main ---
def main():
    rows, cols = GRID_SIZE
    print(f"Grid ({rows}x{cols}):")
    for row in [[0 for _ in range(cols)] for _ in range(rows)]:
        print(row)
    print("\nLego Pieces and their unique orientations:")
    for idx, piece in enumerate(lego_pieces, 1):
        orientations = all_orientations(piece)
        print(f"Piece {idx} has {len(orientations)} unique orientations:")
        if orientations:
            print(f"Visualization of first orientation of Piece {idx}:")
            visualize_piece(orientations[0])
        for o in orientations:
            min_r = min(x for x, y in o)
            min_c = min(y for x, y in o)
            max_r = max(x for x, y in o)
            max_c = max(y for x, y in o)
            count = max(0, (rows - (max_r - min_r))) * max(0, (cols - (max_c - min_c)))
            print(f"  {o} | valid positions: {count}")

    # Calculate and print total estimated nodes
    all_piece_orientations = [all_orientations(piece) for piece in lego_pieces]
    total_iterations = 1
    for orientations in all_piece_orientations:
        piece_max = 0
        for orient in orientations:
            min_r = min(x for x, y in orient)
            min_c = min(y for x, y in orient)
            max_r = max(x for x, y in orient)
            max_c = max(y for x, y in orient)
            count = max(0, (rows - (max_r - min_r))) * max(0, (cols - (max_c - min_c)))
            piece_max += count
        total_iterations *= piece_max if piece_max > 0 else 1
    print(f"\nTotal estimated nodes: {total_iterations}")

    print("\nSolving the tiling puzzle...")
    solution, state = solve_tiling()
    if solution:
        print_and_save_solution(solution, state=state)
    else:
        print("No solution found.")

if __name__ == "__main__":
    main()