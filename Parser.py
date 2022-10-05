#!/usr/bin/python3
# -*- coding: utf-8 -*-
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any
import json

@dataclass
class GasStationCommand():
	CMDType: int
	Side: int
	Nozzle: int
	Params: Any
	Bytes: bytearray


class Parser():

	CMDTYPE_DATA = 1
	DATA_PRICE = 'Price'
	DATA_AMOUNT = 'Amount'
	DATA_VOLUME = 'Quantity'

	@staticmethod
	@abstractmethod
	def GetName() -> str:
		pass

	@staticmethod
	@abstractmethod
	def GetID() -> str:
		pass

	@abstractmethod
	def Parse(self, Command: bytearray) -> GasStationCommand:
		pass

	@abstractmethod
	def GeAnswer(self, Command: GasStationCommand) -> bytearray:
		pass


class JSONParser(Parser):

	PARSER_NAME = 'Парсер json'
	FIELD_CMDTYPE = 'CMDType'
	FIELD_SIDE = 'Side'
	FIELD_NOZZLE = 'Nozzle'

	@staticmethod
	def GetID() -> str:
		return JSONParser.__class__.__name__

	@staticmethod
	def GetName() -> str:
		return JSONParser.PARSER_NAME

	def Parse(self, Command: bytearray) -> GasStationCommand:
		try:
			obj = json.loads(Command.decode())
			return GasStationCommand(
				CMDType=obj[self.FIELD_CMDTYPE] if self.FIELD_CMDTYPE in obj else None,
				Side=obj[self.FIELD_SIDE] if self.FIELD_SIDE in obj else -1,
				Nozzle=obj[self.FIELD_NOZZLE] if self.FIELD_NOZZLE in obj else -1,
				Params=obj,
				Bytes=Command
		)
		except:
			pass

	def GeAnswer(self, Command: GasStationCommand) -> bytearray:
		obj = {'Success': True}
		if self.FIELD_SIDE in Command.Params:
			obj[self.FIELD_SIDE] = Command.Side
		if self.FIELD_NOZZLE in Command.Params:
			obj[self.FIELD_NOZZLE] = Command.Nozzle
		return bytearray(json.dumps(obj).encode())


class BenchParser(Parser):

	PARSER_NAME = 'Парсер Bench'

	@staticmethod
	def GetID() -> str:
		return JSONParser.__class__.__name__

	@staticmethod
	def GetName() -> str:
		return BenchParser.PARSER_NAME

	def Parse(self, Command: bytearray) -> GasStationCommand:
		pass

	def GeAnswer(self, Command: GasStationCommand) -> bytearray:
		pass

