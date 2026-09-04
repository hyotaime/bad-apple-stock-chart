import argparse
import random
import subprocess
import time
from blessed import Terminal
import cv2

term = Terminal()

class HTSBadApplePlayer:
    def __init__(self, video_path: str):
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

        self.code = "BAD_APPLE"
        self.current_price = 172.6
        self.base_price = 173.2
        self.total_ticks = 0
        self.recent_ticks = []
        self.frame_count = 0

    def get_mock_tick(self):
        self.total_ticks += 1
        delta = random.choice([-0.2, -0.1, 0.0, 0.1, 0.1, 0.3])
        self.current_price = max(1.0, self.current_price + delta)
        direction = 1 if delta > 0 else (-1 if delta < 0 else 0)
        vol = random.randrange(100, 3001, 100)
        trade_amt = self.current_price * vol
        now_str = time.strftime("%H:%M:%S")

        self.recent_ticks.insert(0, (now_str, self.current_price, vol, trade_amt, direction))
        if len(self.recent_ticks) > 5:
            self.recent_ticks.pop()

    def frame_to_ascii(self, frame, target_w, target_h):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, (target_w, target_h), interpolation=cv2.INTER_AREA)

        g_block = term.bold_green("█")
        g_wick = term.green("│")
        r_wick = term.red("│")
        r_block = term.bold_red("█")

        lines = []
        green_count = 0
        red_count = 0

        for row in resized:
            line_chars = []
            for pixel in row:
                if pixel > 200:
                    line_chars.append(g_block)
                    green_count += 1
                elif pixel > 140:
                    line_chars.append(g_wick)
                    green_count += 0.5  # Weight of tail = 0.5
                elif pixel > 90:
                    line_chars.append(" ")
                elif pixel > 40:
                    line_chars.append(r_wick)
                    red_count += 0.5
                else:
                    line_chars.append(r_block)
                    red_count += 1
            lines.append("".join(line_chars))

        return lines, green_count, red_count

    def update_tick_from_frame(self, green_count: float, red_count: float, total_pixels: int):
        """0.1x scaling to reduce delta"""
        self.total_ticks += 1

        # Net sentiment ratio (-1.0 to 1.0) based on candle color balance
        net_diff = (green_count - red_count) / max(1, total_pixels)
        # Scale down sensitivity: max price swing capped around ±0.3 JPY
        raw_delta = round(net_diff * 0.3, 1)
        self.current_price = max(1.0, round(self.current_price + raw_delta, 1))

        direction = 1 if raw_delta > 0 else (-1 if raw_delta < 0 else 0)

        # Dynamic volume scaled to sentiment momentum
        vol_base = int(abs(net_diff) * 100)
        vol = max(1, vol_base + random.randint(1, 20))
        trade_amt = self.current_price * vol
        now_str = time.strftime("%H:%M:%S")

        self.recent_ticks.insert(0, (now_str, self.current_price, vol, trade_amt, direction))
        if len(self.recent_ticks) > 5:
            self.recent_ticks.pop()

    def render(self, frame_ascii, current_sec):
        w = term.width
        h = term.height

        diff = self.current_price - self.base_price
        rate = (diff / self.base_price) * 100
        p_style = term.bold_green if diff >= 0 else term.bold_red
        p_sign = "▲" if diff >= 0 else "▼"

        lines = []

        raw_header = f" [JP] {self.code} │ {int(current_sec//60):02d}:{int(current_sec%60):02d} │ FRAME #{self.frame_count:05d} "
        pad_len = max(0, w - term.length(raw_header))
        header_line = term.black_on_white(raw_header + (" " * pad_len))
        lines.append(term.home + term.truncate(header_line, w))

        info_row = (
            f" Last Price: {p_style(f'¥{self.current_price:,.1f}')} {p_style(f'{p_sign}{abs(diff):.1f} ({rate:+.2f}%)')} "
            f"│ Prev Close: ¥{self.base_price:,.1f} "
            f"│ Trades: {self.total_ticks:,} "
            f"│ FPS: {self.fps:.1f}"
        )
        lines.append(term.clear_eol + term.truncate(info_row, w))
        lines.append(term.clear_eol + ("━" * w))

        video_h = len(frame_ascii)
        center_idx = video_h // 2  # mid row standard

        for idx, video_line in enumerate(frame_ascii):
            # distance delta
            diff_from_center = center_idx - idx

            if diff_from_center % 3 == 0:
                steps = diff_from_center // 3
                level_p = round(self.current_price + (steps * 0.1), 1)
                axis_str = f"¥{level_p:8.1f} ┤ "
            else:
                axis_str = "          │ "

            row_str = axis_str + video_line
            lines.append(term.clear_eol + term.truncate(row_str, w))

        # X Axis
        video_w = len(frame_ascii[0]) if frame_ascii else 0
        x_axis_line = " " * 10 + "└" + ("─" * min(video_w, w - 12))
        lines.append(term.clear_eol + term.truncate(x_axis_line, w))
        lines.append(term.clear_eol + ("─" * w))

        # bottom row
        whale_threshold = 500000.0
        formatted_ticks = []
        for t in self.recent_ticks:
            t_time, t_price, t_vol, t_amt, t_dir = t
            base_color = term.green if t_dir > 0 else (term.red if t_dir < 0 else term.white)
            price_str = f"¥{t_price:,.2f}"

            if t_amt >= whale_threshold:
                badge = term.black_on_yellow(f" ★{t_vol:,} shs")
                item_str = f"{t_time} {term.bold_yellow(price_str)} {badge}"
            elif t_vol >= 2500:
                badge = term.bold_yellow(f"⚡{t_vol:,} shs")
                item_str = f"{t_time} {base_color(price_str)} ({badge})"
            else:
                item_str = f"{t_time} {base_color(price_str)} ({t_vol} shs)"
            formatted_ticks.append(item_str)

        tick_summary = "   ".join(formatted_ticks)
        lines.append(term.clear_eol + term.truncate(f" [TRADES] {tick_summary if tick_summary else 'Waiting...'}", w))
        
        lines.append(term.clear_eol + term.darkgray(" [Ctrl+C: Quit | Auto-scales on window resize]"))

        print("\n".join(lines), end="", flush=True)

    def play(self):
        if not self.cap.isOpened():
            print(f"Can not open the video file: {self.video_path}")
            return

        # afplay
        audio_proc = None
        try:
            audio_proc = subprocess.Popen(
                ["afplay", self.video_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception:
            pass

        start_time = time.time()

        with term.fullscreen(), term.hidden_cursor():
            try:
                while self.cap.isOpened():
                    current_time = time.time() - start_time
                    target_frame = int(current_time * self.fps)

                    # audio sync
                    while self.frame_count < target_frame:
                        ret = self.cap.grab()
                        if not ret:
                            break
                        self.frame_count += 1

                    ret, frame = self.cap.read()
                    if not ret:
                        break
                    self.frame_count += 1

                    if self.frame_count % 3 == 0:
                        self.get_mock_tick()

                    chart_h = max(10, term.height - 7)
                    chart_w = min(term.width - 14, int(chart_h * 2.0))

                    # get frame and pixel cnt
                    frame_ascii, green_cnt, red_cnt = self.frame_to_ascii(frame, chart_w, chart_h)
                    
                    # Update price and tick with the radio of frame color once by 3 frame
                    if self.frame_count % 3 == 0:
                        total_px = chart_w * chart_h
                        self.update_tick_from_frame(green_cnt, red_cnt, total_px)

                    self.render(frame_ascii, current_time)

                    # wait
                    expected_time = self.frame_count / self.fps
                    sleep_time = expected_time - (time.time() - start_time)
                    if sleep_time > 0:
                        time.sleep(sleep_time)

            except KeyboardInterrupt:
                pass
            finally:
                if audio_proc:
                    audio_proc.terminate()
                    audio_proc.kill()
                self.cap.release()

def main():
    parser = argparse.ArgumentParser(description="Candle Chart Bad Apple")
    parser.add_argument(
        "-f", "--file",
        type=str,
        default="bad_apple.mp4",
        help="Video file path (Default: bad_apple.mp4)"
    )
    args = parser.parse_args()

    player = HTSBadApplePlayer(video_path=args.file)
    player.play()

if __name__ == "__main__":
    main()

