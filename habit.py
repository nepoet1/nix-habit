import curses
import json
import random
from datetime import date, datetime, timedelta
from pathlib import Path

DATA_DIR = Path.home() / ".local" / "share" / "nix-habit"
DATA_FILE = DATA_DIR / "habits.json"
NOTES_FILE = DATA_DIR / "notes.json"

QUOTES = [
    "Дисциплина — это решение делать то, чего очень не хочется делать, чтобы достичь того, чего очень хочется.",
    "Мы — то, что мы делаем постоянно. Совершенство, следовательно, не действие, а привычка. — Аристотель",
    "Сначала мы формируем привычки, затем привычки формируют нас.",
    "Маленькие ежедневные улучшения со временем приводят к ошеломляющим результатам.",
    "Не важно, как медленно ты идешь, главное — не останавливаться.",
    "Успех — это сумма небольших усилий, повторяющихся изо дня в день.",
    "Лучшее время посадить дерево было 20 лет назад. Следующее лучшее время — сегодня.",
]


def load_json(filepath):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not filepath.exists():
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_json(filepath, data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


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


def wrap_text(text, max_width):
    words = text.split()
    lines, curr_line = [], ""
    for word in words:
        if len(curr_line) + len(word) + 1 <= max_width:
            curr_line += (" " if curr_line else "") + word
        else:
            if curr_line:
                lines.append(curr_line)
            curr_line = word
    if curr_line:
        lines.append(curr_line)
    return lines if lines else [""]


def draw_splash(stdscr, quote):
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    title = "=== NIX-HABIT HUB v2.0 (ПРИВЫЧКИ + ЗАМЕТКИ) ==="
    hint = "[ Нажми любую клавишу, чтобы войти ]"

    lines = wrap_text(quote, max(20, w - 10))
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


def prompt_input(stdscr, prompt_text, initial_text=""):
    h, w = stdscr.getmaxyx()
    win_w = min(70, w - 4)
    win_h = 6
    win_y = max(0, (h - win_h) // 2)
    win_x = max(0, (w - win_w) // 2)

    win = curses.newwin(win_h, win_w, win_y, win_x)
    win.keypad(True)
    curses.curs_set(1)
    buf = list(initial_text)

    while True:
        win.erase()
        win.box()
        win.attron(curses.color_pair(1) | curses.A_BOLD)
        win.addstr(1, 2, prompt_text[: win_w - 4])
        win.attroff(curses.color_pair(1) | curses.A_BOLD)

        text = "".join(buf)
        display_text = text[-(win_w - 6) :]
        win.addstr(2, 2, display_text)
        win.addstr(4, 2, "Enter: сохранить | Esc: отмена", curses.A_DIM)
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


def view_note(stdscr, note):
    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()

        title = f" 📝 {note['title']} "
        meta = f"Создано: {note.get('date', 'Неизвестно')}"

        stdscr.attron(curses.color_pair(1) | curses.A_BOLD)
        stdscr.addstr(1, 2, title[: w - 4])
        stdscr.attroff(curses.color_pair(1) | curses.A_BOLD)
        stdscr.addstr(2, 2, meta[: w - 4], curses.A_DIM)
        stdscr.addstr(3, 2, "─" * min(60, w - 4), curses.A_DIM)

        lines = wrap_text(note.get("body", ""), max(20, w - 6))
        for i, line in enumerate(lines):
            if 5 + i < h - 2:
                stdscr.addstr(5 + i, 2, line[: w - 4])

        footer = " [E] Изменить текст | [Любая другая клавиша] Назад "
        stdscr.attron(curses.color_pair(3))
        stdscr.addstr(h - 1, 0, footer.ljust(w - 1)[: w - 1])
        stdscr.attroff(curses.color_pair(3))

        stdscr.refresh()
        ch = stdscr.get_wch()
        if ch in ("e", "E", "у", "У"):
            new_body = prompt_input(
                stdscr, "Текст заметки:", note.get("body", "")
            )
            if new_body:
                note["body"] = new_body
                return True
        else:
            break
    return False


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

        footer = " [Нажми любую клавишу для возврата] "
        stdscr.attron(curses.color_pair(3))
        stdscr.addstr(h - 1, 0, footer.ljust(w - 1)[: w - 1])
        stdscr.attroff(curses.color_pair(3))

        stdscr.refresh()
        stdscr.getch()
        break


def draw_tabs(stdscr, active_tab, today_str):
    h, w = stdscr.getmaxyx()
    tab1 = " [1] 🔥 Привычки "
    tab2 = " [2] 📝 Заметки "

    stdscr.move(1, 2)
    if active_tab == 0:
        stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
        stdscr.addstr(tab1)
        stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)
        stdscr.addstr("  ")
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(tab2)
        stdscr.attroff(curses.color_pair(1))
    else:
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(tab1)
        stdscr.attroff(curses.color_pair(1))
        stdscr.addstr("  ")
        stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
        stdscr.addstr(tab2)
        stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)

    date_label = f"| Сегодня: {today_str} (Tab — сменить вкладку)"
    if len(tab1) + len(tab2) + len(date_label) + 6 < w:
        stdscr.addstr("   " + date_label, curses.A_DIM)


def main(stdscr):
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN, -1)
    curses.init_pair(2, curses.COLOR_GREEN, -1)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(4, curses.COLOR_YELLOW, -1)

    habits = load_json(DATA_FILE)
    notes = load_json(NOTES_FILE)
    quote = random.choice(QUOTES)
    draw_splash(stdscr, quote)

    active_tab = 0
    sel_habit = 0
    sel_note = 0

    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        today_str = date.today().isoformat()

        draw_tabs(stdscr, active_tab, today_str)

        short_quote = f"«{quote}»"
        stdscr.addstr(2, 2, short_quote[: w - 4], curses.A_DIM)

        if active_tab == 0:
            if not habits:
                msg = "Список привычек пуст. Нажми 'A', чтобы добавить первую!"
                stdscr.addstr(5, 4, msg[: w - 6])
            else:
                sel_habit = max(0, min(sel_habit, len(habits) - 1))
                for idx, habit in enumerate(habits):
                    y = 5 + idx
                    if y >= h - 2:
                        break
                    done_today = today_str in habit.get("completed", [])
                    check = "[✓]" if done_today else "[ ]"
                    streak = calculate_streak(habit.get("completed", []))
                    streak_str = f"🔥 Серия: {streak} дн."

                    line = f" {check} {habit['name']}  ({streak_str}) "
                    if idx == sel_habit:
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
                " [1/2/Tab] Вкладки | [A] Добавить | [Space/Enter] Отметить | "
                "[G] График | [D] Удалить | [Q] Выход "
            )
        else:
            if not notes:
                msg = "Заметок пока нет. Нажми 'A', чтобы создать заметку!"
                stdscr.addstr(5, 4, msg[: w - 6])
            else:
                sel_note = max(0, min(sel_note, len(notes) - 1))
                for idx, note in enumerate(notes):
                    y = 5 + idx
                    if y >= h - 2:
                        break
                    preview = note.get("body", "")[:35]
                    if len(note.get("body", "")) > 35:
                        preview += "..."
                    line = f" 📝 {note['title']}  —  {preview} ({note.get('date', '')}) "
                    if idx == sel_note:
                        stdscr.attron(curses.A_REVERSE | curses.A_BOLD)
                        stdscr.addstr(y, 2, line[: w - 4])
                        stdscr.attroff(curses.A_REVERSE | curses.A_BOLD)
                    else:
                        stdscr.addstr(y, 2, line[: w - 4])

            help_bar = (
                " [1/2/Tab] Вкладки | [A] Новая заметка | [Enter] Читать | "
                "[E] Изменить | [D] Удалить | [Q] Выход "
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
        elif ch == "1":
            active_tab = 0
        elif ch == "2":
            active_tab = 1
        elif ch == chr(9):
            active_tab = 1 - active_tab
        elif ch in (curses.KEY_UP, "k", "K", "л", "Л"):
            if active_tab == 0 and habits:
                sel_habit = (sel_habit - 1) % len(habits)
            elif active_tab == 1 and notes:
                sel_note = (sel_note - 1) % len(notes)
        elif ch in (curses.KEY_DOWN, "j", "J", "о", "О"):
            if active_tab == 0 and habits:
                sel_habit = (sel_habit + 1) % len(habits)
            elif active_tab == 1 and notes:
                sel_note = (sel_note + 1) % len(notes)
        elif ch in ("a", "A", "ф", "Ф"):
            if active_tab == 0:
                name = prompt_input(stdscr, "Название новой привычки:")
                if name:
                    habits.append({"name": name, "completed": []})
                    save_json(DATA_FILE, habits)
                    sel_habit = len(habits) - 1
            else:
                title = prompt_input(stdscr, "Заголовок заметки:")
                if title:
                    body = prompt_input(stdscr, "Текст заметки:")
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                    notes.append({"title": title, "body": body, "date": now_str})
                    save_json(NOTES_FILE, notes)
                    sel_note = len(notes) - 1
        elif ch in ("d", "D", "в", "В"):
            if active_tab == 0 and habits:
                habits.pop(sel_habit)
                save_json(DATA_FILE, habits)
                if sel_habit >= len(habits) and sel_habit > 0:
                    sel_habit -= 1
            elif active_tab == 1 and notes:
                notes.pop(sel_note)
                save_json(NOTES_FILE, notes)
                if sel_note >= len(notes) and sel_note > 0:
                    sel_note -= 1
        elif ch in ("e", "E", "у", "У") and active_tab == 1:
            if notes:
                new_body = prompt_input(
                    stdscr, "Изменить текст:", notes[sel_note].get("body", "")
                )
                if new_body:
                    notes[sel_note]["body"] = new_body
                    save_json(NOTES_FILE, notes)
        elif ch in (" ", chr(10), chr(13), curses.KEY_ENTER):
            if active_tab == 0 and habits:
                comp = habits[sel_habit].setdefault("completed", [])
                if today_str in comp:
                    comp.remove(today_str)
                else:
                    comp.append(today_str)
                save_json(DATA_FILE, habits)
            elif active_tab == 1 and notes:
                if view_note(stdscr, notes[sel_note]):
                    save_json(NOTES_FILE, notes)
        elif ch in ("g", "G", "п", "П") and active_tab == 0:
            show_graph(stdscr, habits)


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
