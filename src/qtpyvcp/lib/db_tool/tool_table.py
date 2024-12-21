# coding=utf-8

from sqlalchemy import Column, String, Integer, Date, Table, ForeignKey, Float, Text
from sqlalchemy.orm import relationship

from .base import Base


class ToolTable(Base):
    __tablename__ = 'tool_table'

    id = Column(Integer, primary_key=True)
    name = Column(Text)
    
    tools = relationship("Tool")
    tool_properties = relationship("ToolProperties")

        
class Tool(Base):
    __tablename__ = 'tool'
    
    
    tool_no = Column(Integer, primary_key=True, autoincrement=False)
    in_use = Column(Integer)
    pocket = Column(Integer)
    
    x_offset = Column(Float)
    y_offset = Column(Float)
    z_offset = Column(Float)
    a_offset = Column(Float)
    b_offset = Column(Float)
    c_offset = Column(Float)
    i_offset = Column(Float)
    j_offset = Column(Float)
    q_offset = Column(Float)
    u_offset = Column(Float)
    v_offset = Column(Float)
    w_offset = Column(Float)
    diameter = Column(Float)
    
    remark = Column(Text)
    
    tool_properties = relationship("ToolProperties", back_populates="tool")    
    tool_table_id = Column(Integer, ForeignKey('tool_table.id'))
    tool_table = relationship("ToolTable", back_populates="tools")

    
class ToolProperties(Base):
    __tablename__ = 'tool_properties'
    
    tool_no = Column(Integer, ForeignKey('tool.tool_no'), primary_key=True, autoincrement=False)
    max_rpm = Column(Integer)
    wear_factor= Column(Float)
    bullnose_radious = Column(Float)
    model = Column(Text)
    atc = Column(Float)
    
    tool_table_id = Column(Integer, ForeignKey('tool_table.id'))
    tool_table = relationship("ToolTable", back_populates="tool_properties")
    tool = relationship("Tool", back_populates="tool_properties")
