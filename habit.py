import curses
import json
import random
from datetime import date, timedelta
from pathlib import Path

DATA_DIR = Path.home() / ".local" / "share" / "nix-habit"
DATA_FILE = DATA_DIR / "habits.json"

QUOTES = [
    "Дисциплина — это решение делать то, чего очень не хочется делать, чтобы достичь того, чего очень хочется.",
    "Мы — то, что мы делаем постоянно. Совершенство, следовательно, не действие, а привычка. — Аристотель",
    "Сначала мы формируем привычки, затем привычки формируют нас.",
    "Маленькие ежедневные улучшения со временем приводят к ошеломляющим результатам.",
    "Не важно, как медленно ты идешь, главное — не останавливаться.",
    "Успех — это сумма небольших усилий, повторяющихся изо дня в день.",
    "Лучшее время посадить дерево было 20 лет назад. Следующее лучшее время — сегодня.",
]


def load_data():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_data(habits):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(habits, f, ensure_ascii=False, indent=2)


def calculate_streak(completed_dates):
    dates_set = set(completed_dates)
    today = date.today()
    yesterday = today - timedelta(days=1)

    if today.isoformat() in dates_set:
        curr = today
    elif yesterday.isoformat() in dates_set:
        curr = yesterday
    else:
        return 0

    streak = 0
    while curr.isoformat() in dates_set:
        streak += 1
        curr -= timedelta(days=1)
    return streak


def draw_splash(stdscr, quote):
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    title = "=== ТРЕКЕР ПРИВЫЧЕК NIX-HABIT ==="
    hint = "[ Нажми любую клавишу, чтобы начать ]"

    max_len = max(20, w - 10)
    words = quote.split()
    lines, curr_line = [], ""
    for word in words:
        if len(curr_line) + len(word) + 1 <= max_len:
            curr_line += (" " if curr_line else "") + word
        else:
            lines.append(curr_line)
            curr_line = word
    if curr_line:
        lines.append(curr_line)

    start_y = max(1, h // 2 - len(lines) // 2 - 2)
    stdscr.attron(curses.color_pair(1) | curses.A_BOLD)
    stdscr.addstr(start_y, max(0, (w - len(title)) // 2), title[: w - 1])
    stdscr.attroff(curses.color_pair(1) | curses.A_BOLD)

    for i, line in enumerate(lines):
        y = start_y + 2 + i
        if y < h - 2:
            stdscr.addstr(
                y, max(0, (w - len(line)) // 2), line[: w - 1], curses.A_ITALIC
            )

    if start_y + 4 + len(lines) < h:
        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(
            start_y + 4 + len(lines),
            max(0, (w - len(hint)) // 2),
            hint[: w - 1],
        )
        stdscr.attroff(curses.color_pair(2))

    stdscr.refresh()
    stdscr.getch()


def prompt_input(stdscr, prompt_text):
    h, w = stdscr.getmaxyx()
    win_w = min(60, w - 4)
    win_h = 5
    win_y = max(0, (h - win_h) // 2)
    win_x = max(0, (w - win_w) // 2)

    win = curses.newwin(win_h, win_w, win_y, win_x)
    win.keypad(True)
    curses.curs_set(1)
    buf = []

    while True:
        win.erase()
        win.box()
        win.attron(curses.color_pair(1) | curses.A_BOLD)
        win.addstr(1, 2, prompt_text[: win_w - 4])
        win.attroff(curses.color_pair(1) | curses.A_BOLD)

        text = "".join(buf)
        display_text = text[-(win_w - 6) :]
        win.addstr(2, 2, display_text)
        win.addstr(3, 2, "Enter: сохранить | Esc: отмена", curses.A_DIM)
        win.move(2, 2 + len(display_text))
        win.refresh()

        ch = win.get_wch()
        if ch in (chr(10), chr(13), curses.KEY_ENTER):
            break
        elif ch == chr(27):
            buf = []
            break
        elif ch in (chr(8), chr(127), curses.KEY_BACKSPACE):
            if buf:
                buf.pop()
        elif isinstance(ch, str) and ch.isprintable():
            buf.append(ch)

    curses.curs_set(0)
    return "".join(buf).strip()


def show_graph(stdscr, habits):
    days_count = 14
    today = date.today()
    dates = [today - timedelta(days=i) for i in range(days_count - 1, -1, -1)]

    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()

        header = "=== ГРАФИК ВЫПОЛНЕНИЯ ЗА ПОСЛЕДНИЕ 14 ДНЕЙ ==="
        stdscr.attron(curses.color_pair(1) | curses.A_BOLD)
        stdscr.addstr(1, 2, header[: w - 3])
        stdscr.attroff(curses.color_pair(1) | curses.A_BOLD)

        if not habits:
            stdscr.addstr(
                3, 2, "Нет привычек для отображения. Сначала создайте их!"
            )
        else:
            days_str = " ".join(d.strftime("%d") for d in dates)
            date_header = "Привычка".ljust(22) + " | " + days_str + " | Успех"
            stdscr.addstr(3, 2, date_header[: w - 3], curses.A_UNDERLINE)

            for idx, habit in enumerate(habits):
                y = 4 + idx
                if y >= h - 3:
                    break
                name = habit["name"][:20].ljust(22)
                completed = set(habit.get("completed", []))

                row_marks = []
                done_count = 0
                for d in dates:
                    if d.isoformat() in completed:
                        row_marks.append("██")
                        done_count += 1
                    else:
                        row_marks.append("··")

                rate = int((done_count / days_count) * 100)
                bar_len = int(rate / 10)
                mini_bar = "▰" * bar_len + "▱" * (10 - bar_len)

                marks_str = " ".join(row_marks)
                line = f"{name} | {marks_str} | {mini_bar} {rate}%"
                stdscr.addstr(y, 2, line[: w - 3])

        footer = " [Нажми любую клавишу для возврата в список] "
        stdscr.attron(curses.color_pair(3))
        stdscr.addstr(h - 1, 0, footer.ljust(w - 1)[: w - 1])
        stdscr.attroff(curses.color_pair(3))

        stdscr.refresh()
        stdscr.getch()
        break


def main(stdscr):
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN, -1)
    curses.init_pair(2, curses.COLOR_GREEN, -1)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(4, curses.COLOR_YELLOW, -1)

    habits = load_data()
    quote = random.choice(QUOTES)
    draw_splash(stdscr, quote)

    selected = 0

    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        today_str = date.today().isoformat()

        title = f" ТРЕКЕР ПРИВЫЧЕК | Сегодня: {today_str} "
        stdscr.attron(curses.color_pair(1) | curses.A_BOLD)
        stdscr.addstr(1, 2, title[: w - 3])
        stdscr.attroff(curses.color_pair(1) | curses.A_BOLD)

        short_quote = f"«{quote}»"
        stdscr.addstr(2, 2, short_quote[: w - 4], curses.A_DIM)

        if not habits:
            msg = "Список пуст. Нажми 'A', чтобы добавить привычку!"
            stdscr.addstr(5, 4, msg[: w - 6])
        else:
            selected = max(0, min(selected, len(habits) - 1))
            for idx, habit in enumerate(habits):
                y = 5 + idx
                if y >= h - 2:
                    break
                done_today = today_str in habit.get("completed", [])
                check = "[✓]" if done_today else "[ ]"
                streak = calculate_streak(habit.get("completed", []))
                streak_str = f"🔥 Серия: {streak} дн."

                line = f" {check} {habit['name']}  ({streak_str}) "
                if idx == selected:
                    stdscr.attron(curses.A_REVERSE | curses.A_BOLD)
                    stdscr.addstr(y, 2, line[: w - 4])
                    stdscr.attroff(curses.A_REVERSE | curses.A_BOLD)
                else:
                    if done_today:
                        stdscr.attron(curses.color_pair(2))
                    stdscr.addstr(y, 2, line[: w - 4])
                    if done_today:
                        stdscr.attroff(curses.color_pair(2))

        help_bar = (
            " [A] Добавить | [Space/Enter] Отметить | "
            "[D] Удалить | [G] График | [Q] Выход "
        )
        stdscr.attron(curses.color_pair(3))
        stdscr.addstr(h - 1, 0, help_bar.ljust(w - 1)[: w - 1])
        stdscr.attroff(curses.color_pair(3))

        stdscr.refresh()

        try:
            ch = stdscr.get_wch()
        except curses.error:
            continue

        if ch in ("q", "Q", "й", "Й"):
            break
        elif ch in (curses.KEY_UP, "k", "K", "л", "Л"):
            if habits:
                selected = (selected - 1) % len(habits)
        elif ch in (curses.KEY_DOWN, "j", "J", "о", "О"):
            if habits:
                selected = (selected + 1) % len(habits)
        elif ch in ("a", "A", "ф", "Ф"):
            name = prompt_input(stdscr, "Введите название новой привычки:")
            if name:
                habits.append({"name": name, "completed": []})
                save_data(habits)
                selected = len(habits) - 1
        elif ch in ("d", "D", "в", "В"):
            if habits:
                habits.pop(selected)
                save_data(habits)
                if selected >= len(habits) and selected > 0:
                    selected -= 1
        elif ch in (" ", chr(10), chr(13), curses.KEY_ENTER):
            if habits:
                comp = habits[selected].setdefault("completed", [])
                if today_str in comp:
                    comp.remove(today_str)
                else:
                    comp.append(today_str)
                save_data(habits)
        elif ch in ("g", "G", "п", "П"):
            show_graph(stdscr, habits)


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
