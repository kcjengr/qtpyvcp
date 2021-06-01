# coding=utf-8

from sqlalchemy import Column, String, Integer, Date, Table, ForeignKey, Float, Text
from sqlalchemy.orm import relationship

from base import Base


class Operations(Base):
    __tablename__ = 'operations_table'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    operations = relationship("Operation")


class Operation(Base):
    __tablename__ = 'operation_table'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    type = Column(String)
    operation_table_id = Column(Integer, ForeignKey('operation_table.id'))
    operation_table = relationship("Operations", back_populates="operation_table")


class Materials(Base):
    __tablename__ = 'materials_table'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    materials = relationship("Material")


class Material(Base):
    __tablename__ = 'material_table'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    thick = Column(Float)
    material_table_id = Column(Integer, ForeignKey('material_table.id'))
    material_table = relationship("Materials", back_populates="material_table")

