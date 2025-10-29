import sys
from PyQt6.QtWidgets import QApplication, QWidget, QMessageBox
from PyQt6.QtGui import QPainter, QColor, QBrush
from PyQt6.QtCore import Qt, QRectF, QPointF


class Checkers(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Шашки — взятие назад только при рубке")
        self.setFixedSize(640, 640)

        self.cell_size = 80
        self.board_size = 8

        self.checkers = []
        self.init_checkers()

        self.selected_checker = None
        self.offset = QPointF(0, 0)
        self.original_pos = None

    def init_checkers(self):
        """Создаёт шашки в начальной позиции"""
        for row in range(3):  # чёрные сверху
            for col in range(self.board_size):
                if (row + col) % 2 == 1:
                    self.checkers.append({
                        "color": "black",
                        "pos": QPointF(col, row)
                    })
        for row in range(5, 8):  # белые снизу
            for col in range(self.board_size):
                if (row + col) % 2 == 1:
                    self.checkers.append({
                        "color": "white",
                        "pos": QPointF(col, row)
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

            # Подсветка выбранной шашки
            if checker is self.selected_checker:
                painter.setPen(QColor("red"))
                painter.drawEllipse(QRectF(cx - 32, cy - 32, 64, 64))

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
        if self.selected_checker:
            size = self.cell_size
            pos = self.selected_checker["pos"]

            # округляем до ближайшей клетки
            col = int(round(pos.x()))
            row = int(round(pos.y()))

            # ограничиваем в пределах доски
            col = max(0, min(self.board_size - 1, col))
            row = max(0, min(self.board_size - 1, row))

            # если целевая клетка занята — нельзя поставиться
            if self.is_cell_occupied(col, row):
                self.selected_checker["pos"] = QPointF(self.original_pos)
            else:
                # проверяем, корректен ли ход
                if self.is_valid_move(col, row, self.selected_checker):
                    # если это взятие — try_capture удалит среднюю шашку
                    self.try_capture(col, row, self.selected_checker)
                    self.selected_checker["pos"] = QPointF(col, row)
                    self.check_winner()
                else:
                    # если ход неправильный — возвращаем обратно
                    self.selected_checker["pos"] = QPointF(self.original_pos)

            self.selected_checker = None
            self.update()

    # ----------------------------------------------------------------
    # Проверка ходов
    # ----------------------------------------------------------------
    def is_valid_move(self, col, row, checker):
        """Вызывает нужную функцию в зависимости от цвета"""
        if checker["color"] == "black":
            return self.is_valid_move_black(col, row, checker)
        else:
            return self.is_valid_move_white(col, row, checker)

    def is_valid_move_black(self, col, row, checker):
        """
        Чёрные:
        - Обычный ход: на 1 клетку по диагонали ВНИЗ (row > old_y)
        - Взятие: на 2 клетки по диагонали в любую сторону, но только если в середине стоит вражеская шашка
        """
        old_x, old_y = int(self.original_pos.x()), int(self.original_pos.y())
        dx = abs(col - old_x)
        dy = abs(row - old_y)

        # обычный ход (вниз)
        if dx == 1 and dy == 1 and row > old_y:
            return True

        # попытка взятия через 2 клетки — разрешаем в любом направлении, но только если есть вражеская шашка между
        if dx == 2 and dy == 2:
            return self.has_enemy_between(old_x, old_y, col, row, checker["color"])

        return False

    def is_valid_move_white(self, col, row, checker):
        """
        Белые:
        - Обычный ход: на 1 клетку по диагонали ВВЕРХ (row < old_y)
        - Взятие: на 2 клетки по диагонали в любую сторону, но только если в середине стоит вражеская шашка
        """
        old_x, old_y = int(self.original_pos.x()), int(self.original_pos.y())
        dx = abs(col - old_x)
        dy = abs(row - old_y)

        # обычный ход (вверх)
        if dx == 1 and dy == 1 and row < old_y:
            return True

        # попытка взятия через 2 клетки — разрешаем в любом направлении, но только если есть вражеская шашка между
        if dx == 2 and dy == 2:
            return self.has_enemy_between(old_x, old_y, col, row, checker["color"])

        return False

    def has_enemy_between(self, old_x, old_y, col, row, color):
        """
        Возвращает True если на промежуточной клетке между (old_x, old_y) и (col, row)
        есть шашка противоположного цвета.
        """
        mid_x = old_x + (col - old_x) // 2
        mid_y = old_y + (row - old_y) // 2
        for other in self.checkers:
            pos = other["pos"]
            if int(pos.x()) == mid_x and int(pos.y()) == mid_y:
                return other["color"] != color
        return False

    # ----------------------------------------------------------------
    # Проверка занятости и взятие
    # ----------------------------------------------------------------
    def is_cell_occupied(self, col, row):
        """Проверяет, занята ли клетка"""
        for checker in self.checkers:
            pos = checker["pos"]
            if int(pos.x()) == col and int(pos.y()) == row:
                return True
        return False

    def try_capture(self, col, row, checker):
        """Если ход через 2 клетки и между ними враг — удаляет его"""
        old_x, old_y = int(self.original_pos.x()), int(self.original_pos.y())
        dx = col - old_x
        dy = row - old_y

        if abs(dx) == 2 and abs(dy) == 2:
            middle_x = old_x + dx // 2
            middle_y = old_y + dy // 2
            for other in self.checkers[:]:
                if other is checker:
                    continue
                pos = other["pos"]
                if int(pos.x()) == middle_x and int(pos.y()) == middle_y:
                    if other["color"] != checker["color"]:
                        self.checkers.remove(other)
                        return True
        return False

    # ----------------------------------------------------------------
    # Проверка победителя
    # ----------------------------------------------------------------
    def check_winner(self):
        """Проверяет, остались ли шашки обоих цветов"""
        colors = [checker["color"] for checker in self.checkers]
        if "black" not in colors:
            self.show_winner("Белые")
        elif "white" not in colors:
            self.show_winner("Чёрные")

    def show_winner(self, winner_color):
        """Выводит сообщение о победителе"""
        msg = QMessageBox(self)
        msg.setWindowTitle("Победа!")
        msg.setText(f"Победили {winner_color} шашки!")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Checkers()
    window.show()
    sys.exit(app.exec())
