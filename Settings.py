#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os.path
from abc import abstractmethod
from typing import Any, Callable, List
from dataclasses import dataclass
from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QCheckBox, QLineEdit, QPushButton, QDialog, QComboBox
from PyQt5 import QtWidgets
from lib import IsFloat
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QResizeEvent, QMoveEvent, QCloseEvent, QMouseEvent

@dataclass()
class ErrorDescription():
	ErrorCode: int = 0
	ErrorMessage: str = ''


ErrorDescriptionSuccess = ErrorDescription(ErrorCode=0, ErrorMessage='')


class Option():

	FORMAT_CAPTION = "%s:"

	def __init__(self, ID: str, Caption: str, Value: Any = None, onChanged: Callable[[Any], Any] = None):
		self.LCaption = None
		self.ID = ID
		self.Caption = Caption
		self.Value = Value
		self.Changed = False
		self.CurrentError = ErrorDescriptionSuccess
		self.onChanged = onChanged
		self.LCaption = None
		self.Validators = []

	def GetValue(self) -> Any:
		return self.Value

	def SetValue(self, NewValue: Any):
		self.Changed = True
		self.Value = NewValue

	def GetChanged(self) -> bool:
		return self.Changed

	def SetChanged(self, Changed: bool):
		self.Changed = Changed

	def GetID(self) -> str:
		return self.ID

	@abstractmethod
	def ShowOption(self, Grid: QGridLayout):
		pass

	@abstractmethod
	def onSetEnable(self, Enable: bool):
		pass

	@abstractmethod
	def onSetVisible(self, Visible: bool):
		pass

	@abstractmethod
	def GetWidgets(self) -> List[QWidget]:
		pass

	def SetParent(self, Parent: QWidget):
		for widget in self.GetWidgets():
			widget.setParent(Parent)

	def SetLCaption(self, LCaption: QLabel):
		self.LCaption = LCaption
		if self.CurrentError != ErrorDescriptionSuccess and self.LCaption:
			self.LCaption.setText(self.CurrentError.ErrorMessage)

	def ShowCurrentError(self):
		if not self.LCaption:
			return
		if self.LCaption:
			self.LCaption.setText(self.CurrentError.ErrorMessage)
		else:
			self.LCaption.clear()

	def Check(self) -> ErrorDescription:
		if not self.Validators:
			return ErrorDescriptionSuccess
		for validator in self.Validators:
			res = validator(self.GetValue())
			if res != ErrorDescriptionSuccess:
				self.CurrentError = res
				self.ShowCurrentError()
				return res
		return ErrorDescriptionSuccess

class BoolOption(Option):

	def __init__(self, ID: str, Caption: str, Value: bool = None, onChanged: Callable[[bool], Any] = None):
		super().__init__(ID, Caption, Value)
		self.Value = bool(Value)
		self.onChanged = onChanged

	def SetValue(self, NewValue: bool):
		super().SetValue(NewValue)
		if self.onChanged:
			self.onChanged(NewValue)

	def onStateChanged(self, newState):
		self.SetValue(self.cb.isChecked())

	def ShowOption(self, Grid: QGridLayout):
		self.Grid = Grid
		self.index = Grid.rowCount()
		self.label = QLabel(self.FORMAT_CAPTION % self.Caption)
		self.label.setObjectName('%s%s' % ('Label', self.ID))
		self.cb = QCheckBox()
		self.cb.setObjectName('%s%s' % ('CheckBox', self.ID))
		self.cb.setChecked(self.Value)
		self.cb.stateChanged.connect(self.onStateChanged)
		self.Grid.addWidget(self.label, self.index, 0)
		self.Grid.addWidget(self.cb, self.index, 1)

	def GetWidgets(self) -> List[QWidget]:
		return [self.label, self.cb]

	def onSetEnable(self, Enable: bool):
		for widget in self.GetWidgets():
			widget.setEnabled(Enable)

	def onSetVisible(self, Visible: bool):
		for widget in self.GetWidgets():
			widget.setVisible(Visible)

class StrOption(Option):

	def __init__(self, ID: str, Caption: str, Value: str = '', onChanged: Callable[[str], Any] = None, Validators: List[Callable[[str], ErrorDescription]] = None):
		super().__init__(ID, Caption, Value)
		self.Value = str(Value)
		self.onChanged = onChanged
		self.Validators = Validators
		self.CurrentError = self.CheckNewValue(self.Value)

	def CheckNewValue(self, Value: str) -> ErrorDescription:
		if not self.Validators:
			return ErrorDescriptionSuccess
		for validator in self.Validators:
			res = validator(Value)
			if res != ErrorDescriptionSuccess:
				return res
		return ErrorDescriptionSuccess

	def SetValue(self, NewValue: str):
		self.CurrentError = self.CheckNewValue(NewValue)
		if not self.CurrentError == ErrorDescriptionSuccess:
			self.ShowCurrentError()
			return
		self.ShowCurrentError()
		super().SetValue(NewValue)
		if self.onChanged:
			self.onChanged(NewValue)

	def onTextChange(self, text):
		self.SetValue(text)

	def ShowOption(self, Grid: QGridLayout):
		self.Grid = Grid
		self.index = Grid.rowCount()
		self.label = QLabel(self.FORMAT_CAPTION % self.Caption)
		self.label.setObjectName('%s%s' % ('Label', self.ID))
		self.edit = QLineEdit()
		self.edit.setObjectName('%s%s' % ('LineEdit', self.ID))
		self.edit.setText(self.Value)
		self.Grid.addWidget(self.label, self.index, 0)
		self.Grid.addWidget(self.edit, self.index, 1)
		self.edit.textChanged.connect(self.onTextChange)

	def GetWidgets(self) -> List[QWidget]:
		return [self.label, self.edit]

	def onSetEnable(self, Enable: bool):
		for widget in self.GetWidgets():
			widget.setEnabled(Enable)

	def onSetVisible(self, Visible: bool):
		for widget in self.GetWidgets():
			widget.setVisible(Visible)


class ComboBoxValue:

	def __init__(self, Value: Any, Name: str = None):
		self.Value = Value
		self.Name = Name
		if self.Name is None:
			self.Name = str(self.Value)


class ComboBoxOption(Option):

	def __init__(self, ID: str, Caption: str, Values: List[ComboBoxValue], onChanged: Callable[[Any], Any] = None, DefaultIndex: int = -1, Validators: List[Callable[[Any], ErrorDescription]] = None):
		if DefaultIndex == -1:
			Value = None
		else:
			Value = Values[DefaultIndex].Value
		super().__init__(ID, Caption, Value)
		self.Value = Value
		self.CurrentIndex = DefaultIndex
		self.Values = Values
		self.onChanged = onChanged
		self.Validators = Validators
		self.CurrentError = self.CheckNewValue(self.Value)

	def ShowCurrentError(self):
		if not self.LCaption:
			return
		if self.LCaption:
			self.LCaption.setText(self.CurrentError.ErrorMessage)
		else:
			self.LCaption.clear()

	def SetValue(self, NewValue: Any):
		self.CurrentError = self.CheckNewValue(NewValue)
		if not self.CurrentError == ErrorDescriptionSuccess:
			self.ShowCurrentError()
			return
		self.ShowCurrentError()
		super().SetValue(NewValue)
		if self.onChanged:
			self.onChanged(NewValue)

	def CheckNewValue(self, Value: Any):
		if not self.Validators:
			return ErrorDescriptionSuccess
		for validator in self.Validators:
			res = validator(Value)
			if res != ErrorDescriptionSuccess:
				return res
		return ErrorDescriptionSuccess

	def ShowOption(self, Grid: QGridLayout):
		self.Grid = Grid
		self.index = Grid.rowCount()
		self.label = QLabel(self.FORMAT_CAPTION % self.Caption)
		self.label.setObjectName('%s%s' % ('Label', self.ID))
		self.ComboBox = QComboBox()
		self.ComboBox.setObjectName('%s%s' % ('ComboBox', self.ID))
		for value in self.Values:
			self.ComboBox.addItem(value.Name, userData=value.Value)
		self.ComboBox.setCurrentIndex(self.CurrentIndex)
		self.Grid.addWidget(self.label, self.index, 0)
		self.Grid.addWidget(self.ComboBox, self.index, 1)
		self.ComboBox.currentIndexChanged.connect(self.onCurrentIndexChange)

	def onCurrentIndexChange(self, NewIndex):
		self.CurrentIndex = NewIndex
		self.SetValue(self.Values[self.CurrentIndex].Value)

	def GetWidgets(self) -> List[QWidget]:
		return [self.label, self.ComboBox]

	def onSetEnable(self, Enable: bool):
		for widget in self.GetWidgets():
			widget.setEnabled(Enable)

	def onSetVisible(self, Visible: bool):
		for widget in self.GetWidgets():
			widget.setVisible(Visible)

class WidgetPosition(Option):

	POSITION_LEFT = 'Left'
	POSITION_TOP = 'Top'
	POSITION_WIDTH = 'Width'
	POSITION_HEIGHT = 'Height'
	DISPLAY_CAPTION = 'Сектор экрана'
	DEFAULT_VALUE = {
		POSITION_TOP: 0,
		POSITION_LEFT: 0,
		POSITION_WIDTH: 100,
		POSITION_HEIGHT: 100
	}
	FIELD_UNDEFINED = 'Поле %s не указано.'
	FIELD_TYPE_ERROR = 'Поле %s должно быть числом от 0 до 100%%.'
	FIELDS_SUM_LARGE = 'Сумма полей %s и %s должна быть меньше 100%%.'
	BSHOW_DISPLAY_CAPTION = 'Показать дисплей'
	BHIDE_DISPLAY_CAPTION = 'Скрыть дисплей'

	def UpdateStyles(self, FileName: str):
		self.StylesFileName = FileName
		if self.Display and os.path.isfile(FileName):
			with open(FileName, 'r') as fp:
				styles = fp.read()
			self.Display.setStyleSheet(styles)

	def Get(self, Dimension: str) -> float:
		return float(self.GetValue()[Dimension])

	def __init__(self, ID: str, Caption: str, Value: dict = {}, onChanged: Callable[[dict], Any] = None, Validators: List[Callable[[dict], ErrorDescription]] = None):
		super().__init__(ID, Caption, Value)
		self.Display: QWidget = None
		self.Dimensions = [self.POSITION_TOP, self.POSITION_LEFT, self.POSITION_WIDTH, self.POSITION_HEIGHT]
		self.Value = Value
		self.onChanged = onChanged
		self.Validators = Validators
		self.app = QtWidgets.QApplication.instance()
		self.desktop = self.app.desktop()
		self.ScreenWidth = self.desktop.screenGeometry().width()
		self.ScreenHeight = self.desktop.screenGeometry().height()
		self.CurrentError = self.CheckNewValue(self.Value)
		self.InitDisplayFunction = None
		self.StylesFileName = None
		if self.CurrentError != ErrorDescriptionSuccess:
			self.Value = self.DEFAULT_VALUE
			self.CurrentError = ErrorDescriptionSuccess

	def CheckNewValue(self, NewValue: dict):
		if self.POSITION_HEIGHT not in NewValue:
			return ErrorDescription(1, self.FIELD_UNDEFINED % self.POSITION_HEIGHT)
		if self.POSITION_WIDTH not in NewValue:
			return ErrorDescription(1, self.FIELD_UNDEFINED % self.POSITION_WIDTH)
		if self.POSITION_LEFT not in NewValue:
			return ErrorDescription(1, self.FIELD_UNDEFINED % self.POSITION_LEFT)
		if self.POSITION_TOP not in NewValue:
			return ErrorDescription(1, self.FIELD_UNDEFINED % self.POSITION_TOP)
		if not IsFloat(NewValue[self.POSITION_WIDTH]) or not 0 <= float(NewValue[self.POSITION_WIDTH]) <= 100:
			return ErrorDescription(1, self.FIELD_TYPE_ERROR % self.POSITION_WIDTH)
		if not IsFloat(NewValue[self.POSITION_HEIGHT]) or not 0 <= float(NewValue[self.POSITION_HEIGHT]) <= 100:
			return ErrorDescription(1, self.FIELD_TYPE_ERROR % self.POSITION_HEIGHT)
		if not IsFloat(NewValue[self.POSITION_LEFT]) or not 0 <= float(NewValue[self.POSITION_LEFT]) <= 100:
			return ErrorDescription(1, self.FIELD_TYPE_ERROR % self.POSITION_LEFT)
		if not IsFloat(NewValue[self.POSITION_TOP]) or not 0 <= float(NewValue[self.POSITION_TOP]) <= 100:
			return ErrorDescription(1, self.FIELD_TYPE_ERROR % self.POSITION_TOP)
		if float(NewValue[self.POSITION_TOP]) + float(NewValue[self.POSITION_HEIGHT]) > 100:
			return ErrorDescription(1, self.FIELDS_SUM_LARGE % (self.POSITION_TOP, self.POSITION_HEIGHT))
		if float(NewValue[self.POSITION_LEFT]) + float(NewValue[self.POSITION_WIDTH]) > 100:
			return ErrorDescription(1, self.FIELDS_SUM_LARGE % (self.POSITION_LEFT, self.POSITION_WIDTH))
		return ErrorDescriptionSuccess

	def ShowCurrentError(self):
		if not self.LCaption:
			return
		if self.LCaption:
			self.LCaption.setText(self.CurrentError.ErrorMessage)
		else:
			self.LCaption.clear()

	def SetValue(self, NewValue: dict):
		self.CurrentError = self.CheckNewValue(NewValue)
		if self.CurrentError != ErrorDescriptionSuccess:
			self.ShowCurrentError()
			return
		self.ShowCurrentError()
		NewValue = {k: float(NewValue[k]) for k in self.Dimensions}
		super().SetValue(NewValue)
		if self.onChanged:
			self.onChanged(NewValue)

	def onPositionChanged(self, text):
		NewPosition = {
			self.POSITION_TOP: self.editTop.text(),
			self.POSITION_LEFT: self.editLeft.text(),
			self.POSITION_WIDTH: self.editWidth.text(),
			self.POSITION_HEIGHT: self.editHeight.text()
		}
		self.SetValue(NewPosition)

	def onDisplayMove(self, e: QMoveEvent):
		self.editLeft.setText("%g" % max(min((round(e.pos().x() / self.ScreenWidth * 100 * 2) / 2), 100), 0))
		self.editTop.setText("%g" % max(min((round(e.pos().y() / self.ScreenHeight * 100 * 2) / 2), 100), 0))

	def onDisplayResize(self, e: QResizeEvent):
		self.editWidth.setText("%g" % max(min((round(e.size().width() / self.ScreenWidth * 100 * 2) / 2), 100), 0))
		self.editHeight.setText("%g" % max(min((round(e.size().height() / self.ScreenHeight * 100 * 2) / 2), 100), 0))

	def onDisplayClose(self, event: QCloseEvent):
		self.onSetEnable(True)

	def onMousePress(self, event: QMouseEvent):
		if event.button() == Qt.LeftButton:
			self.Display.oldPos = self.Display.pos()
			self.oldPos = event.globalPos()

	def onMouseMove(self, event: QMouseEvent):
		if not self.oldPos:
			return
		delta = event.globalPos() - self.oldPos
		self.Display.move(self.Display.oldPos + delta)

	def onMouseRelease(self, event: QMouseEvent):
		if event.button() == Qt.LeftButton:
			self.oldPos = None

	def SetInitDisplayFunction(self, InitDisplayFunction: Callable[[QDialog], Any] = None):
		self.InitDisplayFunction = InitDisplayFunction

	def SetGeometry(self, Widget: QWidget):
		Width = int(self.ScreenWidth * self.Get(self.POSITION_WIDTH) / 100)
		Height = int(self.ScreenHeight * self.Get(self.POSITION_HEIGHT) / 100)
		Left = int(self.ScreenWidth * self.Get(self.POSITION_LEFT) / 100)
		Top = int(self.ScreenHeight * self.Get(self.POSITION_TOP) / 100)
		Widget.setGeometry(Left, Top, Width, Height)

	def onShowDisplay(self):
		if not self.Display:
			self.Display = QDialog()
		if self.Display.isVisible():
			self.Display.hide()
			self.BShowDisplay.setText(self.BSHOW_DISPLAY_CAPTION)
			self.onSetEnable(True)
			return
		self.SetGeometry(self.Display)
		self.Display.closeEvent = self.onDisplayClose
		self.onSetEnable(False)
		self.Display.setWindowTitle(self.DISPLAY_CAPTION)
		self.Display.setWindowFlags(Qt.Tool | Qt.CustomizeWindowHint | Qt.WindowStaysOnTopHint)
		self.Display.mousePressEvent = self.onMousePress
		self.Display.mouseMoveEvent = self.onMouseMove
		self.Display.mouseReleaseEvent = self.onMouseRelease
		self.Display.moveEvent = self.onDisplayMove
		self.Display.resizeEvent = self.onDisplayResize
		self.BShowDisplay.setText(self.BHIDE_DISPLAY_CAPTION)
		self.Display.show()
		if self.InitDisplayFunction:
			self.InitDisplayFunction(self.Display)
		if self.StylesFileName:
			self.UpdateStyles(self.StylesFileName)

	def ShowOption(self, Grid: QGridLayout):
		self.Grid = Grid
		self.index = Grid.rowCount()
		self.offset = self.index
		if self.Caption:
			self.label = QLabel(self.Caption)
			self.label.setObjectName('%s%s' % ('Label', self.ID))
			self.Grid.addWidget(self.label, self.index, 0, 1, 2, alignment=Qt.AlignHCenter)
			self.offset = self.index + 1
		self.labelLeft = QLabel('%s, %%:' % self.POSITION_LEFT)
		self.labelTop = QLabel('%s, %%:' % self.POSITION_TOP)
		self.labelWidth = QLabel('%s, %%:' % self.POSITION_WIDTH)
		self.labelHeight = QLabel('%s, %%:' % self.POSITION_HEIGHT)
		self.editLeft = QLineEdit('%g' % self.Value[self.POSITION_LEFT])
		self.editTop = QLineEdit('%g' % self.Value[self.POSITION_TOP])
		self.editWidth = QLineEdit('%g' % self.Value[self.POSITION_WIDTH])
		self.editHeight = QLineEdit('%g' % self.Value[self.POSITION_HEIGHT])
		self.BShowDisplay = QPushButton(self.BSHOW_DISPLAY_CAPTION)
		self.BShowDisplay.clicked.connect(self.onShowDisplay)
		self.Grid.addWidget(self.labelLeft, self.offset, 0)
		self.Grid.addWidget(self.labelTop, self.offset + 1, 0)
		self.Grid.addWidget(self.labelWidth, self.offset + 2, 0)
		self.Grid.addWidget(self.labelHeight, self.offset + 3, 0)
		self.Grid.addWidget(self.editLeft, self.offset, 1)
		self.Grid.addWidget(self.editTop, self.offset + 1, 1)
		self.Grid.addWidget(self.editWidth, self.offset + 2, 1)
		self.Grid.addWidget(self.editHeight, self.offset + 3, 1)
		self.Grid.addWidget(self.BShowDisplay, self.offset + 4, 0, 1, 2, alignment=Qt.AlignHCenter, )
		self.Grid.setRowStretch(self.Grid.rowCount(), 1)
		self.editLeft.textChanged.connect(self.onPositionChanged)
		self.editTop.textChanged.connect(self.onPositionChanged)
		self.editWidth.textChanged.connect(self.onPositionChanged)
		self.editHeight.textChanged.connect(self.onPositionChanged)

	def GetWidgets(self) -> List[QWidget]:
		return [
			self.label,
			self.labelLeft, self.labelTop, self.labelWidth, self.labelHeight,
			self.editLeft, self.editTop, self.editWidth, self.editHeight]

	def onSetEnable(self, Enable: bool):
		for widget in self.GetWidgets():
			widget.setEnabled(Enable)

	def onSetVisible(self, Visible: bool):
		for widget in self.GetWidgets():
			widget.setVisible(Visible)
