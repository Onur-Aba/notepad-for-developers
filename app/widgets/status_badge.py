from __future__ import annotations

from PySide6.QtWidgets import QApplication, QLabel

from app.models import ReviewStatus


_LABELS_EN = {
    ReviewStatus.CURRENT: "✓ Current",
    ReviewStatus.NEEDS_REVIEW: "⚠ Needs Review",
    ReviewStatus.NOT_REVIEWED: "○ Not Reviewed",
    ReviewStatus.CANNOT_COMPARE: "! Cannot Compare",
}
_LABELS_TR = {
    ReviewStatus.CURRENT: "✓ Güncel",
    ReviewStatus.NEEDS_REVIEW: "⚠ İncelenecek",
    ReviewStatus.NOT_REVIEWED: "○ Kontrol edilmedi",
    ReviewStatus.CANNOT_COMPARE: "! Karşılaştırılamıyor",
}


class StatusBadge(QLabel):
    def __init__(self, status: ReviewStatus = ReviewStatus.NOT_REVIEWED, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("statusBadge")
        self.set_status(status)

    def set_status(self, status: ReviewStatus | str) -> None:
        try:
            normalized = status if isinstance(status, ReviewStatus) else ReviewStatus(status)
        except ValueError:
            normalized = ReviewStatus.CANNOT_COMPARE
        self.status = normalized
        self.setProperty("reviewStatus", normalized.value)
        app = QApplication.instance()
        tr = bool(app is not None and app.property("devnestLanguage") == "tr")
        labels = _LABELS_TR if tr else _LABELS_EN
        self.setText(labels[normalized])
        tips = ({
            ReviewStatus.CURRENT: "Bağlı kod, son kontrol noktasından sonra değişmedi.",
            ReviewStatus.NEEDS_REVIEW: "Bağlı kod, bu bilgi son kontrol edildikten sonra değişti. Bilginin yanlış olduğu anlamına gelmez; tekrar bakmanız gerektiğini söyler.",
            ReviewStatus.NOT_REVIEWED: "Bu bilgi için henüz bir kontrol noktası oluşturulmadı.",
            ReviewStatus.CANNOT_COMPARE: "DevNest kayıtlı kontrol noktasıyla depo geçmişini şu anda karşılaştıramıyor.",
        } if tr else {
            ReviewStatus.CURRENT: "Linked code has not changed since the last review baseline.",
            ReviewStatus.NEEDS_REVIEW: "Linked code changed after this knowledge was last reviewed. This does not mean the knowledge is wrong; it means you should check it again.",
            ReviewStatus.NOT_REVIEWED: "This linked knowledge does not have a review baseline yet.",
            ReviewStatus.CANNOT_COMPARE: "Repository history cannot currently be compared with the stored baseline.",
        })
        self.setToolTip(tips[normalized])
        self.style().unpolish(self)
        self.style().polish(self)
