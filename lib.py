#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import json
from typing import Any


def IsFloat(n) -> bool:
	try:
		n = float(n)
		return True
	except:
		return False


def LoadJSON(FileName: str) -> dict:
	if not os.path.isfile(FileName):
		return {}
	try:
		with open(FileName, 'r') as fp:
			return json.load(fp)
	except:
		return {}


def SaveJSON(FileName: str, d: dict) -> bool:
	try:
		with open(FileName, 'w') as fp:
			json.dump(d, fp, indent=4)
		return True
	except:
		return False


def UpdateJSON(FileName: str, FieldName: str, Field: Any):
	Settings = LoadJSON(FileName)
	Settings[FieldName] = Field
	SaveJSON(FileName, Settings)
