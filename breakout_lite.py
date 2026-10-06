"""breakout-lite —— 极简打砖块引擎。

纯标准库。无头物理核心可直接 import 测试；交互/演示都是文本模式。
"""

import argparse
import random
import sys

W, H = 40, 22          # 场地宽高（格）
PADDLE_W = 7           # 挡板宽度
ROWS, COLS = 4, 10     # 砖块行列
LIVES = 3


class Ball:
    def __init__(self, x, y, vx, vy):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)


class Game:
    """无头打砖块引擎。坐标：左上 (0,0)，x 右增，y 下增。"""

    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.paddle_x = (W - PADDLE_W) // 2  # 挡板左端
        self.paddle_y = H - 2
        self.lives = LIVES
        self.score = 0
        self.cleared = 0
        self.bricks = {}  # (cx, cy) -> hp
        for r in range(ROWS):
            for c in range(COLS):
                self.bricks[(c, 2 + r)] = 1 + (r == 0)  # 顶行 2 血
        self.total_bricks = len(self.bricks)
        self.reset_ball()
        self.over = False
        self.won = False

    def reset_ball(self):
        self.ball = Ball(W / 2, self.paddle_y - 1, self.rng.choice([-1, 1]), -1)

    def step(self, paddle_dir):
        """推进一帧。paddle_dir: -1 左 / 0 不动 / 1 右。"""
        if self.over:
            return
        self.paddle_x = max(0, min(W - PADDLE_W, self.paddle_x + paddle_dir * 2))
        b = self.ball
        b.x += b.vx
        b.y += b.vy

        # 左右墙
        if b.x < 0:
            b.x, b.vx = 0, -b.vx
        elif b.x >= W:
            b.x, b.vx = W - 0.001, -b.vx
        # 顶墙
        if b.y < 0:
            b.y, b.vy = 0, -b.vy

        bx, by = int(b.x), int(b.y)

        # 砖块碰撞
        key = (bx, by)
        if key in self.bricks:
            self.bricks[key] -= 1
            if self.bricks[key] <= 0:
                del self.bricks[key]
                self.cleared += 1
                self.score += 100
            else:
                self.score += 50
            b.vy = -b.vy
            if not self.bricks:
                self.won, self.over = True, True
                return

        # 挡板碰撞（球在挡板行且向下运动）
        if b.vy > 0 and by == self.paddle_y and self.paddle_x <= bx < self.paddle_x + PADDLE_W:
            hit = (bx - self.paddle_x) / PADDLE_W - 0.5  # -0.5..0.5
            b.vx = max(-1.5, min(1.5, hit * 3))
            b.vy = -abs(b.vy)

        # 掉出底线
        if b.y >= H:
            self.lives -= 1
            if self.lives <= 0:
                self.over = True
            else:
                self.reset_ball()

    def render(self):
        grid = [[" "] * W for _ in range(H)]
        for (cx, cy), hp in self.bricks.items():
            if 0 <= cy < H and 0 <= cx < W:
                grid[cy][cx] = "#" if hp > 1 else "="
        for i in range(PADDLE_W):
            grid[self.paddle_y][self.paddle_x + i] = "-"
        bx, by = int(self.ball.x), int(self.ball.y)
        if 0 <= by < H and 0 <= bx < W:
            grid[by][bx] = "o"
        return "\n".join("".join(row) for row in grid)


def auto_play(seed=None, frames=2000, verbose=False):
    """AI 演示：挡板追踪球的 x 位置。"""
    g = Game(seed)
    for f in range(frames):
        if g.over:
            break
        # 简单追踪：球在挡板左就左移，反之右移
        center = g.paddle_x + PADDLE_W / 2
        if g.ball.x < center - 1:
            d = -1
        elif g.ball.x > center + 1:
            d = 1
        else:
            d = 0
        g.step(d)
        if verbose and f % 200 == 0:
            print(f"--- 帧 {f} ---")
            print(g.render())
    return g


def play_interactive():
    if not sys.stdin.isatty():
        print("交互模式需要终端（tty）。可用 --auto 看无头演示。", file=sys.stderr)
        sys.exit(2)
    g = Game()
    print("打砖块：a 左移 / d 右移 / q 退出，每步回车。")
    while not g.over:
        print(f"\n生命 {g.lives}  得分 {g.score}  已清 {g.cleared}/{g.total_bricks}")
        print(g.render())
        try:
            cmd = input("> ").strip().lower()
        except EOFError:
            break
        if cmd == "q":
            break
        d = -1 if cmd == "a" else (1 if cmd == "d" else 0)
        g.step(d)
    print("🎉 全部清除！得分", g.score) if g.won else print("💀 游戏结束，得分", g.score)


def main(argv=None):
    ap = argparse.ArgumentParser(description="极简打砖块（纯标准库）")
    ap.add_argument("--auto", action="store_true", help="无头 AI 演示")
    ap.add_argument("--frames", type=int, default=2000, help="演示帧数上限")
    ap.add_argument("--seed", type=int, default=None, help="随机种子")
    ap.add_argument("--verbose", action="store_true", help="演示时打印棋盘")
    args = ap.parse_args(argv)

    if args.auto:
        g = auto_play(seed=args.seed, frames=args.frames, verbose=args.verbose)
        print(f"自动演示结束：得分 {g.score}，清除砖块 {g.cleared}/{g.total_bricks}，"
              f"剩余生命 {g.lives}，{'胜利' if g.won else '未通关'}。")
    else:
        play_interactive()


if __name__ == "__main__":
    main()
