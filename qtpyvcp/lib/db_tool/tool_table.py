# coding=utf-8

from sqlalchemy import Column, String, Integer, Date, Table, ForeignKey, Float, Text
from sqlalchemy.orm import relationship

from .base import Base


class ToolTable(Base):
    __tablename__ = 'tool_table'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    tools = relationship("Tool")
    tool_models = relationship("ToolModel")

        
class Tool(Base):
    __tablename__ = 'tool'
    
    id = Column(Integer, primary_key=True)
    
    remark = Column(Text)
    tool_no = Column(Integer)
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
    
    model = relationship("ToolModel")
    
    tool_table_id = Column(Integer, ForeignKey('tool_table.id'))
    tool_table = relationship("ToolTable", back_populates="tools")

class ToolModel(Base):
    __tablename__ = 'tool_model'
    
    id = Column(Integer, primary_key=True)
    tool_no = Column(Integer, ForeignKey('tool.tool_no'))
    model = Column(Text)
    tool_table_id = Column(Integer, ForeignKey('tool_table.id'))
    tool_table = relationship("ToolTable", back_populates="tool_models")
