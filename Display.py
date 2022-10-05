#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import os
from typing import List, Callable, Any
from threading import Lock, Thread
from PyQt5.QtWidgets import QApplication, QGridLayout, QWidget, QLabel, QPushButton, QHBoxLayout, QSizePolicy, QDialog, \
	QVBoxLayout, QLineEdit, QGroupBox
from PyQt5 import QtWidgets
from PyQt5.QtGui import QResizeEvent, QMoveEvent, QPixmap
from PyQt5.QtCore import Qt, QTimer
from serial import Serial
import serial.tools.list_ports
from serial.serialutil import SerialBase, PARITY_EVEN, STOPBITS_ONE
from Settings import WidgetPosition, ComboBoxValue, ComboBoxOption, StrOption, ErrorDescription, \
	ErrorDescriptionSuccess, Option
from lib import LoadJSON, UpdateJSON
from Parser import JSONParser, BenchParser, Parser, GasStationCommand


path, _ = os.path.split(os.path.abspath(__file__))
os.chdir(path)


class GasStationDisplay():

	SETTINGS_TITLE = 'Display'
	ON_RUN = 'run'
	ON_SETTINGS = 'settings'
	SETTINGS_FILE_NAME = os.path.join(path, 'GasStationDisplay.json')
	DIR_IMAGES = os.path.join(path, 'Images')
	DIR_STYLES = os.path.join(path, 'QSS')
	ID_BAUDRATE = 'baudrate'
	ID_BYTESIZE = 'bytesize'
	ID_PARITY = 'parity'
	ID_STOPBIT = 'stopbit'
	ID_COM_PORT = 'COMPort'
	ID_PARSER = 'Parser'
	ID_POSITION = 'DisplayPosition'
	ID_CAPTION_PRICE = 'CaptionPrice'
	ID_CAPTION_VOLUME = 'CaptionVolume'
	ID_CAPTION_AMOUNT = 'CaptionAmount'
	ID_FORMAT_PRICE = 'FormatPrice'
	ID_FORMAT_VOLUME = 'FormatVolume'
	ID_FORMAT_AMOUNT = 'FormatAmount'
	ID_IMAGE = 'Image'
	ID_STYLE = 'Style'
	EXTENSIONS_IMAGES = ['.png']
	EXTENSION_STYLE = ['.qss']
	DEFAULT_BAUDRATE = 9600
	DEFAULT_BYTESIZE = 8
	DEFAULT_PARITY = PARITY_EVEN
	DEFAULT_STOPBIT = STOPBITS_ONE
	GB_CAPTION_COMPORT = 'Настройки порта'
	GB_CAPTION_POSITION = 'Положение дисплея'
	GB_CAPTION_FORMAT = 'Формат значений'
	GB_CAPTION_STYLE = 'Стили'
	SETTINGS_POSITION = 'SettingsPosition'
	BSAVE_CAPTION = 'Сохранить'
	DEFAULT_CAPTION_PRICE = 'Цена, руб/лит'
	DEFAULT_CAPTION_VOLUME = 'Объём,\nлит'
	DEFAULT_CAPTION_AMOUNT = 'Сумма,\nруб'
	DEFAULT_FORMAT_PRICE = '%0.2f'
	DEFAULT_FORMAT_VOLUME = '%0.2f'
	DEFAULT_FORMAT_AMOUNT = '%0.2f'
	DEFAULT_DISPLAY_POSITION = {
		WidgetPosition.POSITION_LEFT: 0,
		WidgetPosition.POSITION_TOP: 70,
		WidgetPosition.POSITION_WIDTH: 100,
		WidgetPosition.POSITION_HEIGHT: 30
	}
	SETTINGS_WINDOW_CONSTRAINTS = {
		WidgetPosition.POSITION_WIDTH: 720,
		WidgetPosition.POSITION_HEIGHT: 300
	}
	OBJECT_NAME_LABEL_PRICE = 'ONLabelPrice'
	OBJECT_NAME_EDIT_PRICE = 'ONEditPrice'
	OBJECT_NAME_LABEL_LOGO = 'ONLabelLogo'
	OBJECT_NAME_LABEL_AMOUNT = 'ONLabelAmount'
	OBJECT_NAME_EDIT_AMOUNT = 'ONEditAmount'
	OBJECT_NAME_LABEL_VOLUME = 'ONLabelVolume'
	OBJECT_NAME_EDIT_VOLUME = 'ONEditVolume'
	OBJECT_NAME_DISPLAY = 'ONDisplay'
	TIMEOUNT_COM_PORT = 0.1
	UPDATE_PERIOD = 250

	def GetDefault(self, ID: str, DefaultValue: Any) -> Any:
		return self.Settings[ID] if ID in self.Settings else DefaultValue

	def onOptionChanged(self, Value: Any):
		for option in self.Options:
			if option.Check() != ErrorDescriptionSuccess:
				return
		self.BSave.setEnabled(True)

	def onChangeParser(self, ParserID: str):
		self.onOptionChanged(ParserID)

	def CheckRequaredOption(self, Name: str) -> Callable[[Any], ErrorDescription]:

		def Check(Value: Any) -> ErrorDescription:
			if Value is None:
				return ErrorDescription(ErrorCode=1, ErrorMessage='Необходимо выбрать "%s"' % Name)
			return ErrorDescriptionSuccess

		return Check

	def GetCOMPortNames(self) -> List[str]:
		return [port.device for port in serial.tools.list_ports.comports()]

	def LoadSettings(self):
		if not os.path.isdir(self.DIR_STYLES):
			os.mkdir(self.DIR_STYLES)
		if not os.path.isdir(self.DIR_IMAGES):
			os.mkdir(self.DIR_IMAGES)
		self.Settings = LoadJSON(self.SETTINGS_FILE_NAME)
		self.Logo: QLabel = None
		if self.ID_POSITION not in self.Settings:
			self.Settings[self.ID_POSITION] = self.DEFAULT_DISPLAY_POSITION
		if self.SETTINGS_POSITION not in self.Settings:
			self.Settings[self.SETTINGS_POSITION] = {
				WidgetPosition.POSITION_LEFT: int(self.ScreenWidth / 4),
				WidgetPosition.POSITION_TOP: int(self.ScreenHeight / 4),
				WidgetPosition.POSITION_WIDTH: int(self.ScreenWidth / 2),
				WidgetPosition.POSITION_HEIGHT: int(self.ScreenHeight / 2)
			}
		COMPorts = self.GetCOMPortNames()
		COMPortIndex = -1
		if self.ID_COM_PORT in self.Settings and self.Settings[self.ID_COM_PORT] in COMPorts:
			COMPortIndex = COMPorts.index(self.Settings[self.ID_COM_PORT])
		ParserIndex = -1
		ParserIDS = [cls.GetID() for cls in self.ParserClasses]
		if self.ID_PARSER in self.Settings and self.Settings[self.ID_PARSER] in ParserIDS:
			ParserIndex = ParserIDS.index(self.Settings[self.ID_PARSER])
		self.Images = self.GetFiles(self.DIR_IMAGES, self.EXTENSIONS_IMAGES)
		ImageIndex = -1
		if self.ID_IMAGE in self.Settings and self.Settings[self.ID_IMAGE] in self.Images:
			ImageIndex = self.Images.index(self.Settings[self.ID_IMAGE])
		self.Styles = self.GetFiles(self.DIR_STYLES, self.EXTENSION_STYLE)
		StyleIndex = -1
		if self.ID_STYLE in self.Settings and self.Settings[self.ID_STYLE] in self.Styles:
			StyleIndex = self.Styles.index(self.Settings[self.ID_STYLE])
		self.COMPort = ComboBoxOption(
			ID=self.ID_COM_PORT,
			Caption='COM порт',
			Values=[ComboBoxValue(Value=port) for port in COMPorts],
			onChanged=self.onOptionChanged,
			DefaultIndex=COMPortIndex,
			Validators=[self.CheckRequaredOption('COM порт')]
		)
		self.BaudRate = ComboBoxOption(
			ID=self.ID_BAUDRATE,
			Caption='Скорость',
			Values=[ComboBoxValue(Value=baudrate) for baudrate in SerialBase.BAUDRATES],
			onChanged=self.onOptionChanged,
			DefaultIndex=SerialBase.BAUDRATES.index(self.GetDefault(self.ID_BAUDRATE, self.DEFAULT_BAUDRATE))
		)
		self.ByteSize =	ComboBoxOption(
			ID=self.ID_BYTESIZE,
			Caption='Бит в байте',
			Values=[ComboBoxValue(Value=bytesize) for bytesize in SerialBase.BYTESIZES],
			onChanged=self.onOptionChanged,
			DefaultIndex=SerialBase.BYTESIZES.index(self.GetDefault(self.ID_BYTESIZE, self.DEFAULT_BYTESIZE))
		)
		self.Parity = ComboBoxOption(
			ID=self.ID_PARITY,
			Caption='Бит чётности',
			Values=[ComboBoxValue(Value=parity) for parity in SerialBase.PARITIES],
			onChanged=self.onOptionChanged,
			DefaultIndex=SerialBase.PARITIES.index(self.GetDefault(self.ID_PARITY, self.DEFAULT_PARITY))
		)
		self.StopBit = ComboBoxOption(
			ID=self.ID_STOPBIT,
			Caption='Стоповый бит',
			Values=[ComboBoxValue(Value=stopbit) for stopbit in SerialBase.STOPBITS],
			onChanged=self.onOptionChanged,
			DefaultIndex=SerialBase.STOPBITS.index(self.GetDefault(self.ID_STOPBIT, self.DEFAULT_STOPBIT))
		)
		self.Parser = ComboBoxOption(
			ID=self.ID_PARSER,
			Caption='Протокол',
			Values=[ComboBoxValue(Value=cls.GetID(), Name=cls.GetName()) for cls in self.ParserClasses],
			onChanged=self.onChangeParser,
			DefaultIndex=ParserIndex,
			Validators=[self.CheckRequaredOption('Протокол')]
		)
		self.Position = WidgetPosition(
			ID=self.ID_POSITION,
			Caption='Расположение на экране',
			Value=self.Settings[self.ID_POSITION],
			onChanged=self.onOptionChanged
		)
		self.CaptionPrice = StrOption(
			ID=self.ID_CAPTION_PRICE,
			Caption='Надпись, цена',
			Value=self.GetDefault(self.ID_CAPTION_PRICE, self.DEFAULT_CAPTION_PRICE),
			onChanged=self.onOptionChanged
		)
		self.CaptionVolume = StrOption(
			ID=self.ID_CAPTION_VOLUME,
			Caption='Надпись, объём',
			Value=self.GetDefault(self.ID_CAPTION_VOLUME, self.DEFAULT_CAPTION_VOLUME),
			onChanged=self.onOptionChanged
		)
		self.CaptionAmount = StrOption(
			ID=self.ID_CAPTION_AMOUNT,
			Caption='Надпись, сумма',
			Value=self.GetDefault(self.ID_CAPTION_AMOUNT, self.DEFAULT_CAPTION_AMOUNT),
			onChanged=self.onOptionChanged
		)
		self.FormatPrice = StrOption(
			ID=self.ID_FORMAT_PRICE,
			Caption='Формат, цена',
			Value=self.GetDefault(self.ID_FORMAT_PRICE, self.DEFAULT_FORMAT_PRICE),
			onChanged=self.onOptionChanged,
			Validators=[self.CheckFloatFormat]
		)
		self.FormatVolume = StrOption(
			ID=self.ID_FORMAT_VOLUME,
			Caption='Формат, объём',
			Value=self.GetDefault(self.ID_FORMAT_VOLUME, self.DEFAULT_FORMAT_VOLUME),
			onChanged=self.onOptionChanged,
			Validators=[self.CheckFloatFormat]
		)
		self.FormatAmount = StrOption(
			ID=self.ID_FORMAT_AMOUNT,
			Caption='Формат, сумма',
			Value=self.GetDefault(self.ID_FORMAT_AMOUNT, self.DEFAULT_FORMAT_AMOUNT),
			onChanged=self.onOptionChanged,
			Validators=[self.CheckFloatFormat]
		)
		self.Image = ComboBoxOption(
			ID=self.ID_IMAGE,
			Caption='Логотип',
			Values=[ComboBoxValue(Value=image) for image in self.Images],
			onChanged=self.onChangeImage,
			DefaultIndex=ImageIndex,
			Validators=[self.CheckRequaredOption('Логотип')]
		)
		self.Style = ComboBoxOption(
			ID=self.ID_STYLE,
			Caption='Стили',
			Values=[ComboBoxValue(Value=style) for style in self.Styles],
			onChanged=self.onChangeStyle,
			DefaultIndex=StyleIndex,
			Validators=[self.CheckRequaredOption('Стили')]
		)
		self.LabelImage = QLabel()
		self.LabelImage.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
		self.Options = [
			self.COMPort, self.BaudRate, self.ByteSize, self.Parity,
			self.StopBit, self.Parser, self.Position, self.CaptionPrice,
			self.CaptionVolume, self.CaptionAmount, self.FormatPrice, self.FormatVolume,
			self.FormatAmount, self.Image, self.Style
		]

	def onChangeStyle(self, FileName: str):
		self.Position.UpdateStyles(self.DIR_STYLES + os.sep + FileName)
		self.onOptionChanged(FileName)

	def SetLogo(self, FileName: str, Label: QLabel):
		self.Pixmap = QPixmap(self.DIR_IMAGES + os.sep + FileName)
		self.Pixmap = self.Pixmap.scaled(
			Label.geometry().width(),
			Label.geometry().height(),
			Qt.KeepAspectRatio
		)
		Label.setPixmap(self.Pixmap)
		Label.setStyleSheet('')

	def SetLogoOnDisplay(self, FileName: str):
		if self.Logo and FileName:
			self.Logo.setStyleSheet('background-image: url(%s/%s);' % (self.DIR_IMAGES.split(os.sep)[-1], FileName))

	def onChangeImage(self, FileName: str):
		self.SetLogo(FileName, self.LabelImage)
		self.SetLogoOnDisplay(FileName)
		self.onOptionChanged(FileName)

	def GetFiles(self, Dir: str, Extensions: List[str]):
		if not os.path.isdir(Dir):
			return []
		Files = os.listdir(Dir)
		Files = [FileName for FileName in Files if True in [FileName.lower().endswith(Extension) for Extension in Extensions]]
		return Files

	def CheckFloatFormat(self, Format: str) -> ErrorDescription:
		try:
			s = Format % 1.25
			return ErrorDescriptionSuccess
		except:
			return ErrorDescription(ErrorCode=1, ErrorMessage='Неверный формат (%s) для дробного числа.' % Format)

	def SetDisplayStyle(self, Widget: QWidget, FileName: str):
		if not FileName:
			return
		FileName = os.path.join(self.DIR_STYLES, FileName)
		if not os.path.isfile(FileName):
			return
		with open(FileName, 'r') as fp:
			styles = fp.read()
		Widget.setStyleSheet(styles)

	def CheckSettings(self) ->bool:
		return self.COMPort.GetValue() in self.GetCOMPortNames() and self.Parser.GetValue()

	def onRun(self):
		if not self.CheckSettings():
			self.onSettings()
			return
		self.Serial = Serial(
			baudrate=self.BaudRate.GetValue(),
			bytesize=self.ByteSize.GetValue(),
			parity=self.Parity.GetValue(),
			stopbits=self.StopBit.GetValue(),
			timeout=self.TIMEOUNT_COM_PORT
		)
		self.Serial.port = self.COMPort.GetValue()
		self.ThreadLock = Lock()
		self.CurrentPrice = ''
		self.CurrentVolume = ''
		self.CurrentAmount = ''
		self.Timer = QTimer()
		self.Timer.timeout.connect(self.UpdateData)
		self.Timer.start(self.UPDATE_PERIOD)
		self.ParserObj: Parser = self.ParserClasses[[cls.GetID() for cls in self.ParserClasses].index(self.Parser.GetValue())]()
		self.Widget = QWidget()
		self.Widget.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.CustomizeWindowHint | Qt.WindowStaysOnTopHint)
		self.Position.SetGeometry(self.Widget)
		self.InitDisplay(self.Widget)
		self.SetDisplayStyle(self.Widget, self.Style.GetValue())
		self.RunThread = Thread(target=self.WorkThread, name='WorkThread')
		self.Terminate = False
		self.Widget.closeEvent = self.onWorkEnd
		self.Widget.show()
		self.RunThread.start()

	def UpdateData(self):
		with self.ThreadLock:
			self.EditPrice.setText(self.CurrentPrice)
			self.EditVolume.setText(self.CurrentVolume)
			self.EditAmount.setText(self.CurrentAmount)

	def onWorkEnd(self, event):
		self.Terminate = True
		self.RunThread.join()

	def onCommand(self, Command: GasStationCommand):
		if Command.CMDType == Parser.CMDTYPE_DATA:
			with self.ThreadLock:
				self.CurrentPrice = self.FormatPrice.GetValue() % Command.Params[Parser.DATA_PRICE]
				self.CurrentVolume = self.FormatVolume.GetValue() % Command.Params[Parser.DATA_VOLUME]
				self.CurrentAmount = self.FormatAmount.GetValue() % Command.Params[Parser.DATA_AMOUNT]

	def WorkThread(self):
		while not self.Terminate:
			try:
				self.Serial.open()
				while not self.Terminate:
					self.Serial.timeout = 1
					Command = bytearray(self.Serial.read(1))
					self.Serial.timeout = self.TIMEOUNT_COM_PORT
					try:
						Command += bytearray(self.Serial.read(999))
					except:
						pass
					Command = self.ParserObj.Parse(Command)
					if Command:
						self.onCommand(Command)
			except Exception as err:
				print(err)
				if self.Serial.is_open:
					self.Serial.close()
		if self.Serial.is_open:
			self.Serial.close()

	def onSettings(self):
		self.Window = QWidget()
		self.Window.setWindowTitle(self.SETTINGS_TITLE)
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
		self.VLayout = QVBoxLayout()
		self.HLayout = QHBoxLayout()
		self.COMPortGroupBox = QGroupBox(self.GB_CAPTION_COMPORT)
		self.PositionGroupBox = QGroupBox(self.GB_CAPTION_POSITION)
		self.StringsGroupBox = QGroupBox(self.GB_CAPTION_FORMAT)
		self.StyleGroupBox = QGroupBox(self.GB_CAPTION_STYLE)
		self.COMPortGrid = QGridLayout()
		self.PositionGrid = QGridLayout()
		self.StringsGrid = QGridLayout()
		self.StyleGrid = QGridLayout()
		for option in [self.COMPort, self.BaudRate, self.ByteSize, self.Parity, self.StopBit, self.Parser]:
			option.ShowOption(self.COMPortGrid)
		self.Position.ShowOption(self.PositionGrid)
		for option in [self.CaptionPrice, self.CaptionVolume, self.CaptionAmount, self.FormatPrice, self.FormatVolume, self.FormatAmount]:
			option.ShowOption(self.StringsGrid)
		for option in [self.Style, self.Image]:
			option.ShowOption(self.StyleGrid)
		self.StyleGrid.addWidget(self.LabelImage, self.StyleGrid.rowCount(), 0, 1, 2)
		self.COMPortGroupBox.setLayout(self.COMPortGrid)
		self.PositionGroupBox.setLayout(self.PositionGrid)
		self.StringsGroupBox.setLayout(self.StringsGrid)
		self.StyleGroupBox.setLayout(self.StyleGrid)
		self.HLayout.addWidget(self.COMPortGroupBox)
		self.HLayout.addWidget(self.PositionGroupBox)
		self.HLayout.addWidget(self.StringsGroupBox)
		self.HLayout.addWidget(self.StyleGroupBox)
		self.LCaption = QLabel('')
		self.LCaption.setWordWrap(True)
		self.LCaption.setAlignment(Qt.AlignCenter)
		self.BSave = QPushButton(self.BSAVE_CAPTION)
		self.BSave.setEnabled(False)
		self.BSave.clicked.connect(self.onSave)
		self.Position.SetInitDisplayFunction(self.InitDisplay)
		self.Position.SetLCaption(self.LCaption)
		self.COMPort.SetLCaption(self.LCaption)
		self.Parser.SetLCaption(self.LCaption)
		self.Image.SetLCaption(self.LCaption)
		self.Style.SetLCaption(self.LCaption)
		self.VLayout.addLayout(self.HLayout)
		self.VLayout.addWidget(self.LCaption)
		self.VLayout.addWidget(self.BSave)
		self.Window.setLayout(self.VLayout)
		self.Window.closeEvent = self.onSettingsClose
		self.Window.show()
		if self.Image.GetValue() and os.path.isfile(self.DIR_IMAGES + os.sep + self.Image.GetValue()):
			self.SetLogo(self.Image.GetValue(), self.LabelImage)
		if self.Style.GetValue() and os.path.isfile(self.DIR_STYLES + os.sep + self.Style.GetValue()):
			self.onChangeStyle(self.Style.GetValue())

	def InitDisplay(self, Widget: QWidget):
		Widget.setObjectName(self.OBJECT_NAME_DISPLAY)
		self.Grid = QGridLayout()
		self.LeftVLayout = QVBoxLayout()
		self.LabelPrice = QLabel(self.CaptionPrice.GetValue())
		self.LabelPrice.setAlignment(Qt.AlignCenter)
		self.LabelPrice.setObjectName(self.OBJECT_NAME_LABEL_PRICE)
		self.EditPrice = QLineEdit(self.FormatPrice.GetValue() % 0)
		self.EditPrice.setObjectName(self.OBJECT_NAME_EDIT_PRICE)
		self.EditPrice.setAlignment(Qt.AlignRight)
		self.Logo = QLabel()
		self.Logo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
		self.Logo.setObjectName(self.OBJECT_NAME_LABEL_LOGO)
		self.LeftVLayout.addWidget(self.LabelPrice)
		self.LeftVLayout.addWidget(self.EditPrice)
		self.LeftVLayout.addWidget(self.Logo)
		self.HLayoutTop = QHBoxLayout()
		self.LabelAmount = QLabel(self.CaptionAmount.GetValue())
		self.LabelPrice.setObjectName(self.OBJECT_NAME_LABEL_AMOUNT)
		self.LabelAmount.setAlignment(Qt.AlignCenter)
		self.EditAmount = QLineEdit(self.FormatAmount.GetValue() % 0)
		self.EditAmount.setObjectName(self.OBJECT_NAME_EDIT_AMOUNT)
		self.EditAmount.setAlignment(Qt.AlignRight)
		self.HLayoutTop.addWidget(self.LabelAmount)
		self.HLayoutTop.addWidget(self.EditAmount)
		self.HLayoutBottom = QHBoxLayout()
		self.LabelVolume = QLabel(self.CaptionVolume.GetValue())
		self.LabelVolume.setObjectName(self.OBJECT_NAME_LABEL_VOLUME)
		self.LabelVolume.setAlignment(Qt.AlignCenter)
		self.EditVolume = QLineEdit(self.FormatVolume.GetValue() % 0)
		self.EditVolume.setObjectName(self.OBJECT_NAME_EDIT_VOLUME)
		self.EditVolume.setAlignment(Qt.AlignRight)
		self.HLayoutBottom.addWidget(self.LabelVolume)
		self.HLayoutBottom.addWidget(self.EditVolume)
		self.Grid.addLayout(self.LeftVLayout, 0, 0, 2, 1)
		self.Grid.addLayout(self.HLayoutTop, 0, 1)
		self.Grid.addLayout(self.HLayoutBottom, 1, 1)
		Widget.setLayout(self.Grid)
		self.SetLogoOnDisplay(self.Image.GetValue())

	def onSettingsClose(self, event):
		for window in QApplication.topLevelWidgets():
			window.close()

	def onSave(self):
		for option in self.Options:
			UpdateJSON(self.SETTINGS_FILE_NAME, option.GetID(), option.GetValue())
		self.BSave.setEnabled(False)

	def onSettingsResize(self, e: QResizeEvent):
		self.Settings[self.SETTINGS_POSITION][WidgetPosition.POSITION_WIDTH] = e.size().width()
		self.Settings[self.SETTINGS_POSITION][WidgetPosition.POSITION_HEIGHT] = e.size().height()
		UpdateJSON(self.SETTINGS_FILE_NAME, self.SETTINGS_POSITION, self.Settings[self.SETTINGS_POSITION])

	def onSettingsMove(self, e: QMoveEvent):
		self.Settings[self.SETTINGS_POSITION][WidgetPosition.POSITION_LEFT] = e.pos().x()
		self.Settings[self.SETTINGS_POSITION][WidgetPosition.POSITION_TOP] = e.pos().y()
		UpdateJSON(self.SETTINGS_FILE_NAME, self.SETTINGS_POSITION, self.Settings[self.SETTINGS_POSITION])

	def __init__(self):
		super().__init__()
		self.i = 0
		self.app = QtWidgets.QApplication.instance()
		self.desktop = self.app.desktop()
		self.ScreenWidth = self.desktop.screenGeometry().width()
		self.ScreenHeight = self.desktop.screenGeometry().height()
		self.ParserClasses: List[Parser] = [JSONParser, BenchParser]
		self.Options: List[Option] = []
		self.LoadSettings()
		self.WorkMode = {
			self.ON_RUN: self.ON_RUN in sys.argv,
			self.ON_SETTINGS: self.ON_SETTINGS in sys.argv
		}
		if self.WorkMode[self.ON_RUN] == self.WorkMode[self.ON_SETTINGS]:
			self.WorkMode[self.ON_SETTINGS] = True
			self.WorkMode[self.ON_RUN] = False
		#self.onRun()
		#return
		if self.WorkMode[self.ON_RUN]:
			self.onRun()
		else:
			self.onSettings()


if __name__ == '__main__':
	app = QApplication(sys.argv)
	MediaPlayer = GasStationDisplay()
	sys.exit(app.exec_())
