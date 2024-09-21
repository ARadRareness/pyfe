from PySide6.QtWidgets import QStyledItemDelegate, QStyle


class NoHighlightDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        if option.state & QStyle.State_MouseOver:
            option.state &= ~QStyle.State_MouseOver
        super().paint(painter, option, index)
