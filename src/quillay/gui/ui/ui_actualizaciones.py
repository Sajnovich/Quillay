# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'actualizaciones.ui'
##
## Created by: Qt User Interface Compiler version 6.12.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QHBoxLayout, QLabel,
    QPlainTextEdit, QProgressBar, QPushButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

class Ui_Actualizaciones(object):
    def setupUi(self, Actualizaciones):
        if not Actualizaciones.objectName():
            Actualizaciones.setObjectName(u"Actualizaciones")
        Actualizaciones.resize(760, 560)
        self.lay = QVBoxLayout(Actualizaciones)
        self.lay.setSpacing(10)
        self.lay.setObjectName(u"lay")
        self.lay.setContentsMargins(28, 24, 28, 24)
        self.titulo = QLabel(Actualizaciones)
        self.titulo.setObjectName(u"titulo")
        self.titulo.setProperty(u"rol", u"titulo")

        self.lay.addWidget(self.titulo)

        self.subtitulo = QLabel(Actualizaciones)
        self.subtitulo.setObjectName(u"subtitulo")
        self.subtitulo.setWordWrap(True)
        self.subtitulo.setProperty(u"muted", True)

        self.lay.addWidget(self.subtitulo)

        self.estado = QLabel(Actualizaciones)
        self.estado.setObjectName(u"estado")
        self.estado.setTextFormat(Qt.TextFormat.PlainText)
        self.estado.setWordWrap(True)

        self.lay.addWidget(self.estado)

        self.botones = QHBoxLayout()
        self.botones.setObjectName(u"botones")
        self.revisar_btn = QPushButton(Actualizaciones)
        self.revisar_btn.setObjectName(u"revisar_btn")
        self.revisar_btn.setProperty(u"rol", u"principal")

        self.botones.addWidget(self.revisar_btn)

        self.lo_btn = QPushButton(Actualizaciones)
        self.lo_btn.setObjectName(u"lo_btn")

        self.botones.addWidget(self.lo_btn)

        self.descargar_btn = QPushButton(Actualizaciones)
        self.descargar_btn.setObjectName(u"descargar_btn")
        self.descargar_btn.setVisible(False)

        self.botones.addWidget(self.descargar_btn)

        self.relleno_botones = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.botones.addItem(self.relleno_botones)


        self.lay.addLayout(self.botones)

        self.al_abrir = QCheckBox(Actualizaciones)
        self.al_abrir.setObjectName(u"al_abrir")

        self.lay.addWidget(self.al_abrir)

        self.nota = QLabel(Actualizaciones)
        self.nota.setObjectName(u"nota")
        self.nota.setWordWrap(True)
        self.nota.setProperty(u"muted", True)

        self.lay.addWidget(self.nota)

        self.bar = QProgressBar(Actualizaciones)
        self.bar.setObjectName(u"bar")
        self.bar.setVisible(False)

        self.lay.addWidget(self.bar)

        self.log = QPlainTextEdit(Actualizaciones)
        self.log.setObjectName(u"log")
        self.log.setReadOnly(True)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.log.sizePolicy().hasHeightForWidth())
        self.log.setSizePolicy(sizePolicy)

        self.lay.addWidget(self.log)


        self.retranslateUi(Actualizaciones)

        QMetaObject.connectSlotsByName(Actualizaciones)
    # setupUi

    def retranslateUi(self, Actualizaciones):
        Actualizaciones.setWindowTitle(QCoreApplication.translate("Actualizaciones", u"Actualizaciones", None))
        self.titulo.setText(QCoreApplication.translate("Actualizaciones", u"Actualizaciones", None))
        self.subtitulo.setText(QCoreApplication.translate("Actualizaciones", u"Mant\u00e9n Quillay y LibreOffice al d\u00eda: las versiones nuevas traen correcciones de seguridad.", None))
        self.estado.setText(QCoreApplication.translate("Actualizaciones", u"Quillay\n"
"LibreOffice", None))
        self.revisar_btn.setText(QCoreApplication.translate("Actualizaciones", u"Buscar actualizaciones", None))
        self.lo_btn.setText(QCoreApplication.translate("Actualizaciones", u"Instalar LibreOffice", None))
        self.descargar_btn.setText(QCoreApplication.translate("Actualizaciones", u"Descargar la nueva versi\u00f3n de Quillay", None))
        self.al_abrir.setText(QCoreApplication.translate("Actualizaciones", u"Revisar al abrir Quillay", None))
        self.nota.setText(QCoreApplication.translate("Actualizaciones", u"Quillay funciona sin internet. Solo se conecta cuando aprietas un bot\u00f3n de esta p\u00e1gina (o al abrir, si activas la casilla), y no env\u00eda nada tuyo: pregunta a GitHub y a LibreOffice cu\u00e1les son sus \u00faltimas versiones.", None))
    # retranslateUi

