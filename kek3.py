import sys
from PyQt6.QtWidgets import QApplication, QWidget, QMessageBox
from PyQt6.QtGui import QPainter, QColor, QBrush
from PyQt6.QtCore import Qt, QRectF, QPointF


class Checkers(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Шашки?")
        self.setFixedSize(640, 640)

        self.cell_size = 80
        self.board_size = 8

        self.checkers = []
        self.init_checkers()

        self.selected_checker = None
        self.offset = QPointF(0, 0)
        self.original_pos = None
        self.current_turn = "black"  # чёрные начинают
        self.must_continue = False  # остаётся ли ход у той же шашки после взятия

    # ----------------------------------------------------------------
    # Инициализация
    # ----------------------------------------------------------------
    def init_checkers(self):
        """Создаёт шашки в начальной позиции"""
        self.checkers.clear()
        for row in range(3):  # чёрные сверху
            for col in range(self.board_size):
                if (row + col) % 2 == 1:
                    self.checkers.append({
                        "color": "black",
                        "pos": QPointF(col, row),
                        "king": False
                    })
        for row in range(5, 8):  # белые снизу
            for col in range(self.board_size):
                if (row + col) % 2 == 1:
                    self.checkers.append({
                        "color": "white",
                        "pos": QPointF(col, row),
                        "king": False
                    })

    # ----------------------------------------------------------------
    # Отрисовка
    # ----------------------------------------------------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        size = self.cell_size

        # Рисуем доску
        for row in range(self.board_size):
            for col in range(self.board_size):
                color = QColor(240, 217, 181) if (row + col) % 2 == 0 else QColor(181, 136, 99)
                painter.setBrush(QBrush(color))
                painter.drawRect(col * size, row * size, size, size)

        # Рисуем шашки
        for checker in self.checkers:
            pos = checker["pos"]
            cx = pos.x() * size + size / 2
            cy = pos.y() * size + size / 2

            color = QColor("white") if checker["color"] == "white" else QColor("black")
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(cx - 30, cy - 30, 60, 60))

            # Дамка — жёлтая окантовка
            if checker["king"]:
                painter.setPen(QColor("gold"))
                painter.drawEllipse(QRectF(cx - 25, cy - 25, 50, 50))

            if checker is self.selected_checker and checker['king']:
                painter.setPen(QColor("red"))
                painter.drawEllipse(QRectF(cx - 32, cy - 32, 64, 64))
                painter.setPen(QColor("gold"))
                painter.drawEllipse(QRectF(cx - 25, cy - 25, 50, 50))

            # Подсветка выбранной шашки
            elif checker is self.selected_checker:
                painter.setPen(QColor("red"))
                painter.drawEllipse(QRectF(cx - 32, cy - 32, 64, 64))

        # Текущий ход
        painter.setPen(Qt.GlobalColor.darkBlue)
        painter.drawText(10, 20, f"Ход: {'Чёрные' if self.current_turn == 'black' else 'Белые'}")


    # ----------------------------------------------------------------
    # Управление мышью
    # ----------------------------------------------------------------
    def mousePressEvent(self, event):
        """Выбор шашки"""
        x, y = event.position().x(), event.position().y()
        size = self.cell_size
        for checker in reversed(self.checkers):
            cx = checker["pos"].x() * size + size / 2
            cy = checker["pos"].y() * size + size / 2
            if (x - cx) ** 2 + (y - cy) ** 2 <= 30 ** 2:
                # Ходить можно только шашке своего цвета
                if checker["color"] == self.current_turn:
                    self.selected_checker = checker
                    self.original_pos = QPointF(checker["pos"])
                    self.offset = QPointF(x - cx, y - cy)
                    self.update()
                return

    def mouseMoveEvent(self, event):
        """Перетаскивание шашки"""
        if self.selected_checker:
            x, y = event.position().x(), event.position().y()
            size = self.cell_size
            new_x = (x - self.offset.x() - size / 2) / size
            new_y = (y - self.offset.y() - size / 2) / size
            self.selected_checker["pos"] = QPointF(new_x, new_y)
            self.update()

    def mouseReleaseEvent(self, event):
        """Отпускание — проверка корректности хода"""
        if not self.selected_checker:
            return

        size = self.cell_size
        pos = self.selected_checker["pos"]

        col = int(round(pos.x()))
        row = int(round(pos.y()))

        # ограничиваем в пределах доски
        col = max(0, min(self.board_size - 1, col))
        row = max(0, min(self.board_size - 1, row))

        # если целевая клетка занята — нельзя
        if self.is_cell_occupied(col, row):
            self.selected_checker["pos"] = QPointF(self.original_pos)
        else:
            # проверяем, допустим ли ход
            if self.is_valid_move(col, row, self.selected_checker):
                was_capture = self.try_capture(col, row, self.selected_checker)
                self.selected_checker["pos"] = QPointF(col, row)
                self.promote_to_king(self.selected_checker)
                self.check_winner()

                # если был удар и есть возможность снова бить — не меняем ход
                if was_capture and self.can_continue_capture(self.selected_checker):
                    self.must_continue = True
                else:
                    self.must_continue = False
                    self.switch_turn()
            else:
                self.selected_checker["pos"] = QPointF(self.original_pos)  

        self.selected_checker["pos"].setX(int(round(self.selected_checker["pos"].x())))
        self.selected_checker["pos"].setY(int(round(self.selected_checker["pos"].y())))

        self.selected_checker = None
        self.update()

    # ----------------------------------------------------------------
    # Проверка ходов
    # ----------------------------------------------------------------
    def is_valid_move(self, col, row, checker):
        """Вызывает нужную функцию"""
        if checker["king"]:
            return self.is_valid_move_king(col, row, checker)
        if checker["color"] == "black":
            return self.is_valid_move_black(col, row, checker)
        else:
            return self.is_valid_move_white(col, row, checker)

    def is_valid_move_black(self, col, row, checker):
        """Чёрные: 1 клетка вперёд, рубка на 2 клетки в любую сторону (только если враг есть)"""
        old_x, old_y = int(self.original_pos.x()), int(self.original_pos.y())
        dx = abs(col - old_x)
        dy = abs(row - old_y)

        # обычный ход (вниз)
        if dx == 1 and dy == 1 and row > old_y:
            return True

        # рубка (пешка): ровно 2 клетки и между — враг
        if dx == 2 and dy == 2:
            return self.has_enemy_between(old_x, old_y, col, row, checker["color"])

        return False

    def is_valid_move_white(self, col, row, checker):
        """Белые: 1 клетка вперёд, рубка на 2 клетки в любую сторону (только если враг есть)"""
        old_x, old_y = int(self.original_pos.x()), int(self.original_pos.y())
        dx = abs(col - old_x)
        dy = abs(row - old_y)

        # обычный ход (вверх)
        if dx == 1 and dy == 1 and row < old_y:
            return True

        # рубка (пешка): ровно 2 клетки и между — враг
        if dx == 2 and dy == 2:
            return self.has_enemy_between(old_x, old_y, col, row, checker["color"])

        return False

    def is_valid_move_king(self, col, row, checker):
        """
        Дамка (летящая):
        - Обычный ход: по диагонали на любое количество клеток, все клетки между пусты.
        - Взятие: по диагонали, на пути ровно одна вражеская шашка, остальные клетки пусты; приземление
          может быть на любую пустую клетку за вражеской шашкой по той же диагонали.
        """
        old_x, old_y = int(self.original_pos.x()), int(self.original_pos.y())
        dx = col - old_x
        dy = row - old_y

        if abs(dx) != abs(dy) or dx == 0:
            return False  # не по диагонали

        step_x = 1 if dx > 0 else -1
        step_y = 1 if dy > 0 else -1

        x, y = old_x + step_x, old_y + step_y
        enemy_count = 0
        blocked = False
        while (x != col + step_x) and (y != row + step_y):
            # если на пути есть фигура
            occ = self.get_checker_at(x, y)
            if occ is not None:
                if occ["color"] == checker["color"]:
                    blocked = True
                    break
                else:
                    enemy_count += 1
            x += step_x
            y += step_y

        if blocked:
            return False

        # обычный перелёт (ни одной шашки на пути)
        if enemy_count == 0:
            return True

        # захват допустим только если ровно одна вражеская шашка на пути
        if enemy_count == 1:
            return True

        return False

    def get_checker_at(self, col, row):
        """Возвращает объект шашки в клетке или None"""
        for c in self.checkers:
            pos = c["pos"]
            if int(pos.x()) == col and int(pos.y()) == row:
                return c
        return None

    def has_enemy_between(self, old_x, old_y, col, row, color):
        """Возвращает True если между (old_x, old_y) и (col, row) есть шашка противника (и не более)"""
        step_x = 1 if col > old_x else -1
        step_y = 1 if row > old_y else -1
        x, y = old_x + step_x, old_y + step_y
        found_enemy = False
        while x != col or y != row:
            occ = self.get_checker_at(x, y)
            if occ is not None:
                if occ["color"] == color:
                    return False
                if found_enemy:
                    return False  # больше одной вражеской
                found_enemy = True
            x += step_x
            y += step_y
        return found_enemy

    # ----------------------------------------------------------------
    # Проверка и удаление при взятии
    # ----------------------------------------------------------------
    def is_cell_occupied(self, col, row):
        return self.get_checker_at(col, row) is not None

    def try_capture(self, col, row, checker):
        """
        Выполняет взятие, если это было захватывающим ходом.
        Возвращает True, если было удаление (захват).
        Поддерживает пешечные захваты (через 2 клетки) и дамочные:
        - для дамки — ищем вражеские шашки на диагонали между старой и новой позицией;
          если ровно одна — удаляем её.
        """
        old_x, old_y = int(self.original_pos.x()), int(self.original_pos.y())
        dx = col - old_x
        dy = row - old_y

        # пешечное взятие (ровно 2 клетки)
        if abs(dx) == 2 and abs(dy) == 2 and not checker["king"]:
            middle_x = old_x + dx // 2
            middle_y = old_y + dy // 2
            middle = self.get_checker_at(middle_x, middle_y)
            if middle is not None and middle["color"] != checker["color"]:
                self.checkers.remove(middle)
                return True
            return False

        # дамка: на диагонали между старой и новой позицией ровно одна вражеская шашка -> удаляем её
        if checker["king"]:
            if abs(dx) != abs(dy) or dx == 0:
                return False
            step_x = 1 if dx > 0 else -1
            step_y = 1 if dy > 0 else -1
            x, y = old_x + step_x, old_y + step_y
            enemies = []
            while x != col or y != row:
                occ = self.get_checker_at(x, y)
                if occ is not None:
                    if occ["color"] == checker["color"]:
                        # блокировка своим — не захват
                        return False
                    enemies.append(occ)
                x += step_x
                y += step_y
            if len(enemies) == 1:
                # удаляем вражескую шашку
                self.checkers.remove(enemies[0])
                return True
            return False

        # иначе — не захват
        return False

    # ----------------------------------------------------------------
    # Дополнительные функции
    # ----------------------------------------------------------------
    def promote_to_king(self, checker):
        """Делает шашку дамкой при достижении противоположного края"""
        if checker["color"] == "black" and int(checker["pos"].y()) == 7:
            checker["king"] = True
        elif checker["color"] == "white" and int(checker["pos"].y()) == 0:
            checker["king"] = True

    def can_continue_capture(self, checker):
        """Проверяет, может ли шашка после взятия снова бить"""
        x0, y0 = int(checker["pos"].x()), int(checker["pos"].y())
        color = checker["color"]

        # пешечные варианты (как раньше)
        if not checker["king"]:
            directions = [(-2, -2), (-2, 2), (2, -2), (2, 2)]
            for dx, dy in directions:
                nx, ny = x0 + dx, y0 + dy
                if 0 <= nx < self.board_size and 0 <= ny < self.board_size:
                    if not self.is_cell_occupied(nx, ny) and self.has_enemy_between(x0, y0, nx, ny, color):
                        return True
            return False

        # дамка: по каждой диагонали смотрим, есть ли вражеская шашка, за которой есть пустая клетка
        dirs = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        for sx, sy in dirs:
            x, y = x0 + sx, y0 + sy
            found_enemy = None
            while 0 <= x < self.board_size and 0 <= y < self.board_size:
                occ = self.get_checker_at(x, y)
                if occ is None:
                    if found_enemy is not None:
                        # есть пустая клетка за найденным врагом -> можно приземлиться сюда
                        return True
                else:
                    if occ["color"] == color:
                        break  # блокировка своим
                    if found_enemy is None:
                        found_enemy = occ
                    else:
                        break  # больше одного врага на пути -> нельзя захватить этой диагональю
                x += sx
                y += sy
        return False

    def switch_turn(self):
        """Меняет очередь хода"""
        self.current_turn = "white" if self.current_turn == "black" else "black"

    # ----------------------------------------------------------------
    # Проверка победителя
    # ----------------------------------------------------------------
    def check_winner(self):
        colors = [checker["color"] for checker in self.checkers]
        if "black" not in colors:
            self.show_winner("Белые")
        elif "white" not in colors:
            self.show_winner("Чёрные")

    def show_winner(self, winner_color):
        msg = QMessageBox(self)
        msg.setWindowTitle("Победа!")
        msg.setText(f"Победили {winner_color} шашки!")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()
        # Перезапуск игры
        self.init_checkers()
        self.current_turn = "black"
        self.update()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Checkers()
    window.show()
    sys.exit(app.exec())
