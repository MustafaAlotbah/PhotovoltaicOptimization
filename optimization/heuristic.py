from utils import save_stats_and_cache
import numpy as np


def heuristic(fun, n, step=(1, 600), start_at=(2, 0), stop_after=6, tol=0.005, options=None, cost_func=None):
    if options is None:
        options = {}

    xs = np.array([])
    ys = np.array([])

    x, y = start_at
    step_x, step_y = step

    @save_stats_and_cache
    def f(x, y, *args):
        res = fun(x, y, *args, **options)
        return res*100

    fxs = np.array([f(x, y)])
    frames = [(x, y, f(x, y))]

    m = 0
    switch_one_dimensional = False
    for _ in range(1, n):
        m += 1

        current = f(x, y)

        above_right = f(x + step_x, y + step_y)

        dx = 0
        dy = 0

        if above_right < current:
            dx, dy = step_x, step_y
        else:
            right = f(x + step_x, y)
            left = f(x - step_x, y)
            above = f(x, y + step_y)

            if right <= current + 0.01:
                dx += step_x
            elif left <= current + 0.01:
                dx -= step_x

            if above < current + 0.01:
                dy = step_y

        if dx == 0 and dy == 0:
            break

        if (len(frames) >= stop_after and all(
                [
                    abs(frames[-i][2] - frames[-i - 1][2]) <= tol
                    for i in range(1, stop_after)]
        )):
            print("stopping...")
            break

        x = x + dx
        y = y + dy

        if cost_func is not None and cost_func(x) * 1000 < y:
            print("Constraints violation:", x, y, cost_func(x))
            switch_one_dimensional = True
            break

        xs = np.append(xs, x)
        ys = np.append(ys, y)
        fxs = np.append(fxs, f(x, y))

        frames.append((x, y, f(x, y)))

    if switch_one_dimensional:
        assert cost_func is not None
        for _ in range(m, n):
            m += 1

            y = ((cost_func(x) * 1000) // step_y) * step_y

            current = f(x, y)

            y_r = ((cost_func(x + step_x) * 1000) // step_y) * step_y
            right = f(x + step_x, y_r)

            y_l = ((cost_func(x - step_x) * 1000) // step_y) * step_y
            left = f(x - step_x, y_l)

            dx = 0
            if right <= current:
                dx = step_x
            elif left <= current:
                dx = -step_x

            if dx == 0:
                print("early stopping..", left, current, right, left <= current, right <= current)
                break

            if (len(frames) >= stop_after and all(
                    [
                        abs(frames[-i][2] - frames[-i - 1][2]) <= tol
                        for i in range(1, stop_after)]
            )):
                print("stopping...")
                break

            x = x + dx
            y = ((cost_func(x) * 1000) // step_y) * step_y

            if y != y_l and y != y_r:
                print("problem")

            frames.append((x, y, f(x, y)))

    if True:
        print(f"The minimum was found to be at {x, y} after {m} iterations with {f.calls} calls out of {f.all_calls}.")

    frames_sorted = sorted(frames, key=lambda x: x[2])
    return frames_sorted[0], frames, m, f.calls





