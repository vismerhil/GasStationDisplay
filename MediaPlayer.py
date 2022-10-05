#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import os
import shutil
from typing import List
from PyQt5.QtWidgets import QApplication, QGridLayout, QWidget, QLabel, QPushButton, QHBoxLayout, QSizePolicy
from PyQt5 import QtWidgets
from PyQt5.QtGui import QResizeEvent, QMoveEvent
from PyQt5.QtCore import Qt, QUrl, QTimer
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer, QMediaPlaylist
from PyQt5.QtMultimediaWidgets import QVideoWidget
import psutil
from Settings import WidgetPosition, BoolOption, StrOption
from lib import LoadJSON, UpdateJSON

path, _ = os.path.split(os.path.abspath(__file__))
os.chdir(path)

class MediaPlayer():

    ON_RUN = 'run'
    ON_SETTINGS = 'settings'
    SETTINGS_FILE_NAME = os.path.join(path, 'MediaPlayer.json')
    MEDIA_PATH = 'MediaPlayer'
    USER_HOME = '~'
    SETTINGS_SCREEN = 'Screen'
    SETTINGS_WIDTH = 'Width'
    SETTINGS_HEIGHT = 'Height'
    SETTINGS_USE_USB = 'UseUSB'
    SETTINGS_USB_PATH = 'USBPath'
    SETTINGS_MEDIA_PATH = 'MediaPath'
    SETTINGS_DISPLAY_POSITION = 'DisplayPosition'
    MEDIA_EXTENSIONS = ['.avi', '.mp4', '.wmv']
    DEFAULT_USB_PATH = os.sep + 'MediaPlayer'
    DEFAULT_DISPLAY_POSITION = {
        WidgetPosition.POSITION_LEFT: 0,
        WidgetPosition.POSITION_TOP: 0,
        WidgetPosition.POSITION_WIDTH: 100,
        WidgetPosition.POSITION_HEIGHT: 70
    }
    SETTINGS_WINDOW_CONSTRAINTS = {
        WidgetPosition.POSITION_WIDTH: 245,
        WidgetPosition.POSITION_HEIGHT: 300
    }
    SETTINGS_POSITION = 'SettingsPosition'
    SETTINGS_TITLE = 'MediaPlayer'
    BSAVE_CAPTION = 'Сохранить'
    CAPTION_NO_MEDIA_FILES = 'Нет медиа - файлов.'
    CAPTION_COPY_FILE = 'Копирование файлов из:\n%s\nСкопировано файлов %d из %d.'
    CAPDION_DELETE_FILE = 'Удаление файлов с диска %d / %d.'
    DISPLAY_CAPTION_STYLE = 'font-size: 24pt; color: green; background-color: black;'

    def LoadSettings(self):
        self.Settings = LoadJSON(self.SETTINGS_FILE_NAME)
        self.Settings[self.SETTINGS_SCREEN] = {
            self.SETTINGS_WIDTH: self.ScreenWidth,
            self.SETTINGS_HEIGHT: self.ScreenHeight
        }
        if self.SETTINGS_MEDIA_PATH not in self.Settings:
            self.Settings[self.SETTINGS_MEDIA_PATH] = os.path.expanduser(os.path.join(self.USER_HOME, self.MEDIA_PATH))
        if self.SETTINGS_USE_USB not in self.Settings:
            self.Settings[self.SETTINGS_USE_USB] = True
        if self.SETTINGS_USB_PATH not in self.Settings:
            self.Settings[self.SETTINGS_USB_PATH] = self.DEFAULT_USB_PATH
        if self.SETTINGS_DISPLAY_POSITION not in self.Settings:
            self.Settings[self.SETTINGS_DISPLAY_POSITION] = self.DEFAULT_DISPLAY_POSITION
        if self.SETTINGS_POSITION not in self.Settings:
            self.Settings[self.SETTINGS_POSITION] = {
                WidgetPosition.POSITION_LEFT: int(self.ScreenWidth / 4),
                WidgetPosition.POSITION_TOP: int(self.ScreenHeight / 4),
                WidgetPosition.POSITION_WIDTH: int(self.ScreenWidth / 2),
                WidgetPosition.POSITION_HEIGHT: int(self.ScreenHeight / 2)
            }

    def SetWidgetPosition(self, Widget: QWidget):
        Width = int(self.ScreenWidth * self.Settings[self.SETTINGS_DISPLAY_POSITION][WidgetPosition.POSITION_WIDTH] / 100)
        Height = int(self.ScreenHeight * self.Settings[self.SETTINGS_DISPLAY_POSITION][WidgetPosition.POSITION_HEIGHT] / 100)
        Left = int(self.ScreenWidth * self.Settings[self.SETTINGS_DISPLAY_POSITION][WidgetPosition.POSITION_LEFT] / 100)
        Top = int(self.ScreenHeight * self.Settings[self.SETTINGS_DISPLAY_POSITION][WidgetPosition.POSITION_TOP] / 100)
        Widget.setGeometry(Left, Top, Width, Height)
        Widget.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

    def StopPlay(self):
        self.MediaPlayer.stop()
        self.LCaptionMessage.setText('')
        self.MessageDisplay.show()
        self.VideoWidget.hide()

    def onMediaPlayerError(self, error):
        print("Error: " + self.MediaPlayer.errorString())

    def StartPlay(self):
        self.MediaPlayList.clear()
        self.MediaFiles = self.GetMediaFiles(self.Settings[self.SETTINGS_MEDIA_PATH], self.MEDIA_EXTENSIONS)
        for MediaFile in self.GetMediaFiles(self.Settings[self.SETTINGS_MEDIA_PATH], self.MEDIA_EXTENSIONS):
            self.MediaPlayList.addMedia(QMediaContent(QUrl.fromLocalFile(MediaFile)))
        self.MediaPlayer.setPlaylist(self.MediaPlayList)
        self.MediaPlayer.playlist().setCurrentIndex(0)
        self.MediaPlayList.setPlaybackMode(QMediaPlaylist.PlaybackMode.Loop)
        if len(self.MediaFiles):
            self.MessageDisplay.hide()
            self.MediaPlayer.play()
            self.VideoWidget.show()
            print(self.MediaPlayer.errorString())
        else:
            self.LCaptionMessage.setText(self.CAPTION_NO_MEDIA_FILES)
            self.VideoWidget.hide()
            self.MessageDisplay.show()

    #запуск воспроизведения
    def onRun(self):
        self.Terminated = False
        self.MediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.VideoWidget = QVideoWidget()
        self.MediaPlayList = QMediaPlaylist(self.MediaPlayer)
        self.MediaPlayer.setVideoOutput(self.VideoWidget)
        self.SetWidgetPosition(self.VideoWidget)
        self.InstallMediaThread = QTimer()
        self.oldDisks = self.GetMediaPaths()
        self.InstallMediaThread.timeout.connect(self.InstallMediaThreadRun)
        self.InstallMediaThread.start(5000)
        self.MessageDisplay = QWidget()                     # окно для показа сообщений, если нет медиа - файлов или происходит их загрузка
        hbox = QHBoxLayout()
        self.LCaptionMessage = QLabel(parent=self.MessageDisplay)
        self.LCaptionMessage.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.LCaptionMessage.setAlignment(Qt.AlignCenter)
        self.LCaptionMessage.setWordWrap(True)
        self.LCaptionMessage.setStyleSheet(self.DISPLAY_CAPTION_STYLE)
        hbox.addWidget(self.LCaptionMessage)
        self.SetWidgetPosition(self.MessageDisplay)
        self.MessageDisplay.setLayout(hbox)
        self.VideoWidget.closeEvent = self.onMediaPlayerClose
        self.StartPlay()

    def onMediaPlayerClose(self):
        self.Terminated = True
        self.InstallMediaThread.stop()

    def LoadMediaFromDisk(self, Path: str):
        MediaFiles = self.GetMediaFiles(Path, self.MEDIA_EXTENSIONS)
        for i in range(len(MediaFiles)):
            self.LCaptionMessage.setText(self.CAPTION_COPY_FILE % (Path, i + 1, len(MediaFiles)))
            self.app.processEvents()
            shutil.copy(MediaFiles[i], self.Settings[self.SETTINGS_MEDIA_PATH])

    def DeleteCurrentMediaFiles(self):
        MediaFiles = self.GetMediaFiles(self.Settings[self.SETTINGS_MEDIA_PATH], self.MEDIA_EXTENSIONS)
        self.MediaPlayList.clear()
        self.MediaPlayer.stop()
        self.MessageDisplay.show()
        for i in range(len(MediaFiles)):
            self.LCaptionMessage.setText(self.CAPDION_DELETE_FILE % (i + 1, len(MediaFiles)))
            self.app.processEvents()
            os.remove(MediaFiles[i])

    def GetMediaPaths(self) -> set[str]:
        disks = psutil.disk_partitions()
        points = [disk.mountpoint for disk in disks]
        res = []
        for point in points:
            if not point.endswith(os.sep):
                point += os.sep
            res.append(point + self.Settings[self.SETTINGS_USB_PATH].strip(os.sep) + os.sep)
        return set(res)

    def InstallMediaThreadRun(self):
        newDisks = self.GetMediaPaths()
        print(self.i, newDisks)
        Disks = newDisks - self.oldDisks
        if Disks:
            print('new disks1', Disks)
            Disks = [Disk for Disk in Disks if os.path.isdir(Disk)]
            if Disks:
                print('new disks2', Disks)
                self.StopPlay()
                self.app.processEvents()
                self.DeleteCurrentMediaFiles()
                for Disk in Disks:
                    self.LoadMediaFromDisk(Disk)
                self.StartPlay()
        self.oldDisks = newDisks

    def onUseUSBChanged(self, p: bool):
        self.USBPath.onSetEnable(self.UseUSB.GetValue())
        self.BSave.setEnabled(True)

    def onUSBPathChanged(self, text: str):
        self.BSave.setEnabled(True)

    def onPositionChanged(self, d: dict):
        self.BSave.setEnabled(True)

    #показ настроек
    def onSettings(self):
        self.Window = QWidget()
        self.Window.setWindowTitle(self.SETTINGS_TITLE)
        self.UseUSB = BoolOption(
            ID=self.SETTINGS_USE_USB,
            Caption='USB флешки: ',
            Value=self.Settings[self.SETTINGS_USE_USB],
            onChanged=self.onUseUSBChanged
        )
        self.USBPath = StrOption(
            ID=self.SETTINGS_USB_PATH,
            Caption='Папка на USB:',
            Value=self.Settings[self.SETTINGS_USB_PATH],
            onChanged=self.onUSBPathChanged
        )
        self.Position = WidgetPosition(
            ID=self.SETTINGS_DISPLAY_POSITION,
            Caption='Расположение на экране:',
            Value=self.Settings[self.SETTINGS_DISPLAY_POSITION],
            onChanged=self.onPositionChanged
        )
        self.Window.setMinimumSize(
            self.SETTINGS_WINDOW_CONSTRAINTS[WidgetPosition.POSITION_WIDTH],
            self.SETTINGS_WINDOW_CONSTRAINTS[WidgetPosition.POSITION_HEIGHT]
        )
        self.Window.setMaximumSize(
            self.SETTINGS_WINDOW_CONSTRAINTS[WidgetPosition.POSITION_WIDTH],
            self.SETTINGS_WINDOW_CONSTRAINTS[WidgetPosition.POSITION_HEIGHT]
        )
        self.Window.setGeometry(
            self.Settings[self.SETTINGS_POSITION][WidgetPosition.POSITION_LEFT],
            self.Settings[self.SETTINGS_POSITION][WidgetPosition.POSITION_TOP],
            self.Settings[self.SETTINGS_POSITION][WidgetPosition.POSITION_WIDTH],
            self.Settings[self.SETTINGS_POSITION][WidgetPosition.POSITION_HEIGHT]
        )
        self.Window.resizeEvent = self.onSettingsResize
        self.Window.moveEvent = self.onSettingsMove
        Grid = QGridLayout()
        self.UseUSB.ShowOption(Grid)
        self.USBPath.ShowOption(Grid)
        self.Position.ShowOption(Grid)
        self.Window.setLayout(Grid)
        self.LCaption = QLabel('')
        self.BSave = QPushButton(self.BSAVE_CAPTION)
        self.BSave.setEnabled(False)
        self.BSave.clicked.connect(self.onSave)
        self.USBPath.onSetEnable(self.UseUSB.GetValue())
        Grid.addWidget(self.LCaption, Grid.rowCount(), 0, 1, 2, alignment=Qt.AlignHCenter)
        Grid.addWidget(self.BSave, Grid.rowCount(), 0, 1, 2, alignment=Qt.AlignHCenter)
        self.Position.SetLCaption(self.LCaption)
        self.Window.closeEvent = self.onSettingsClose
        self.Window.show()

    def onSettingsClose(self, event):
        for window in QApplication.topLevelWidgets():
            window.close()

    def onSave(self):
        UpdateJSON(self.SETTINGS_FILE_NAME, self.SETTINGS_USE_USB, self.UseUSB.GetValue())
        UpdateJSON(self.SETTINGS_FILE_NAME, self.SETTINGS_USB_PATH, self.USBPath.GetValue())
        UpdateJSON(self.SETTINGS_FILE_NAME, self.SETTINGS_DISPLAY_POSITION, self.Position.GetValue())
        self.BSave.setEnabled(False)

    def onSettingsResize(self, e: QResizeEvent):
        self.Settings[self.SETTINGS_POSITION][WidgetPosition.POSITION_WIDTH] = e.size().width()
        self.Settings[self.SETTINGS_POSITION][WidgetPosition.POSITION_HEIGHT] = e.size().height()
        UpdateJSON(self.SETTINGS_FILE_NAME, self.SETTINGS_POSITION, self.Settings[self.SETTINGS_POSITION])

    def onSettingsMove(self, e: QMoveEvent):
        self.Settings[self.SETTINGS_POSITION][WidgetPosition.POSITION_LEFT] = e.pos().x()
        self.Settings[self.SETTINGS_POSITION][WidgetPosition.POSITION_TOP] = e.pos().y()
        UpdateJSON(self.SETTINGS_FILE_NAME, self.SETTINGS_POSITION, self.Settings[self.SETTINGS_POSITION])

    #получение списка медиа-файлов по папке и расширениям файлов
    def GetMediaFiles(self, MediaDir: str, MediaExtensions: List[str]):
        if not os.path.isdir(MediaDir):
            return []
        Files = os.listdir(MediaDir)
        MediaFiles = [MediaDir + os.sep + FileName for FileName in Files if True in [FileName.lower().endswith(Extension) for Extension in MediaExtensions]]
        return MediaFiles

    def __init__(self):
        super().__init__()
        self.i = 0
        self.app = QtWidgets.QApplication.instance()
        self.desktop = self.app.desktop()
        self.ScreenWidth = self.desktop.screenGeometry().width()
        self.ScreenHeight = self.desktop.screenGeometry().height()
        self.LoadSettings()
        self.WorkMode = {
            self.ON_RUN: self.ON_RUN in sys.argv,
            self.ON_SETTINGS: self.ON_SETTINGS in sys.argv
        }
        if not os.path.isdir(self.Settings[self.SETTINGS_MEDIA_PATH]):
            os.makedirs(self.Settings[self.SETTINGS_MEDIA_PATH])
        if self.WorkMode[self.ON_RUN] == self.WorkMode[self.ON_SETTINGS]:
            self.WorkMode[self.ON_SETTINGS] = True
            self.WorkMode[self.ON_RUN] = False
        if self.WorkMode[self.ON_RUN]:
            self.onRun()
        else:
            self.onSettings()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    MediaPlayer = MediaPlayer()
    sys.exit(app.exec_())
