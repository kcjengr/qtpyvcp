# coding=utf-8
import os
import linuxcnc

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


INI_FILE = linuxcnc.ini(os.getenv("INI_FILE_NAME"))
DB_URI= INI_FILE.find("EMCIO", "DB_URI") or "sqlite:///db.sqlite"


engine = create_engine(DB_URI, echo=False)
Session = sessionmaker(bind=engine)

Base = declarative_base()
