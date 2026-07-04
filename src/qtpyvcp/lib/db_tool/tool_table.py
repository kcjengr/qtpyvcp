# coding=utf-8
"""ORM models for the qtpyvcp tool database.

``Tool`` (+ ``ToolLathe``/``CustomFieldDef``/``CustomFieldValue``/``Meta``) map
schema v1 (frozen 2026-07-03, see ``migrations/001_initial.sql`` -- the
authoritative DDL; these Column definitions mirror it for ORM use, they do
not create it. Use :func:`qtpyvcp.lib.db_tool.migrate.run_migrations` to
create/upgrade the actual tables.

``ToolTable``/``ToolModel`` are an unrelated, currently-unused stub for a
per-tool custom STL model file (mill VTK display, see
``widgets/display_widgets/vtk_backplot/tool_actor.py``); no code creates
``ToolModel`` rows today. Kept as-is, decoupled from ``Tool`` (which no
longer carries a ``tool_table_id`` FK per schema v1).
"""

from sqlalchemy import (Column, String, Integer, Table, ForeignKey, Float,
                         Text, CheckConstraint)
from sqlalchemy.orm import relationship

from .base import Base


class ToolTable(Base):
    __tablename__ = 'tool_table'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    tool_models = relationship("ToolModel", back_populates="tool_table")


class Meta(Base):
    __tablename__ = 'meta'

    schema_version = Column(Integer, primary_key=True)
    units = Column(Text, CheckConstraint("units IN ('inch','mm')"), nullable=False)


class Tool(Base):
    __tablename__ = 'tool'

    id = Column(Integer, primary_key=True)

    # unique: tool_no is the join key everywhere (T0 = "no tool" is a
    # synthesized in-memory placeholder, never a DB row -- see
    # DBToolTable.saveToolTable/loadToolTable -- so tool_no > 0 always holds).
    tool_no = Column(Integer, unique=True, nullable=False)
    pocket = Column(Integer, nullable=False, default=-1)

    x_offset = Column(Float, nullable=False, default=0.0)
    y_offset = Column(Float, nullable=False, default=0.0)
    z_offset = Column(Float, nullable=False, default=0.0)
    a_offset = Column(Float, nullable=False, default=0.0)
    b_offset = Column(Float, nullable=False, default=0.0)
    c_offset = Column(Float, nullable=False, default=0.0)
    u_offset = Column(Float, nullable=False, default=0.0)
    v_offset = Column(Float, nullable=False, default=0.0)
    w_offset = Column(Float, nullable=False, default=0.0)

    diameter = Column(Float, nullable=False, default=0.0)       # D, §5.1
    front_angle = Column(Float, nullable=False, default=0.0)    # I
    back_angle = Column(Float, nullable=False, default=0.0)     # J
    orientation = Column(Integer, nullable=False, default=0)    # Q, 0..9
    remark = Column(Text, nullable=False, default='')           # R
    in_use = Column(Integer, nullable=False, default=0)         # maintained by l/u

    lathe = relationship("ToolLathe", uselist=False, back_populates="tool",
                          cascade="all, delete-orphan")
    custom_values = relationship("CustomFieldValue", cascade="all, delete-orphan")


class ToolLathe(Base):
    """Lathe extras: consumed by the UI, VTK insert display, and the
    conversational add-on; never sent to LinuxCNC."""
    __tablename__ = 'tool_lathe'

    tool_id = Column(Integer, ForeignKey('tool.id', ondelete='CASCADE'),
                      primary_key=True)
    tool = relationship("Tool", back_populates="lathe")

    type = Column(Text)  # turning|boring|grooving|parting|threading|drill|tap|custom

    # insert identity (ISO turning inserts; VTK profile inputs)
    insert_shape = Column(Text)        # ISO shape letter: C,D,V,W,T,R,S,...
    insert_size_mode = Column(Text)    # IC | edge_length
    insert_size = Column(Float)        # IC diameter or edge length per size_mode
    insert_thickness = Column(Float)   # S

    # holder (ISO turning/boring/grooving holders)
    holder_style = Column(Text)        # full ISO code, e.g. SCLCR; THSC letter derived
    holder_hand = Column(Text)         # R | L
    holder_shank_width = Column(Float) # W
    holder_cut_width = Column(Float)   # CW; internal-groove max depth = CW - W/2
    holder_oal = Column(Float)         # holder overall length

    # grooving / parting
    groove_width = Column(Float)       # cutting edge width
    max_depth_of_cut = Column(Float)   # groove insert usable depth (display length)

    # drills / taps (round tools; no holder rows apply)
    drill_point_angle = Column(Float)  # SIG, e.g. 118 / 135
    flute_length = Column(Float)       # LCF/LB; drill body & tap flute display length
    overall_length = Column(Float)     # tool OAL (tap/drill; thread insert length)
    shaft_diameter = Column(Float)     # SFDM; tap/drill shank
    chamfer_threads = Column(Float)    # tap lead/chamfer threads (e.g. 2.5)

    # threading
    thread_pitch_max = Column(Float)   # TPX/TP; tap pitch reuses this column
    thread_angle = Column(Float)       # profile angle, default 60
    thread_tip_type = Column(Text)     # point | flat | radius

    # feeds & speeds defaults (conversational autofill)
    surface_speed = Column(Float)      # SFM / SMM per meta.units
    feed_per_rev = Column(Float)
    depth_of_cut = Column(Float)

    notes = Column(Text, nullable=False, default='')


class CustomFieldDef(Base):
    """User-defined custom column definition (plan §5.7)."""
    __tablename__ = 'custom_field_def'

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True, nullable=False)   # machine-readable key
    label = Column(Text, nullable=False)               # column header in the UI
    value_type = Column(Text, nullable=False)          # float|int|text|bool
    unit = Column(Text)
    default_value = Column(Text)
    display_order = Column(Integer)


class CustomFieldValue(Base):
    __tablename__ = 'custom_field_value'

    tool_id = Column(Integer, ForeignKey('tool.id', ondelete='CASCADE'),
                      primary_key=True)
    field_id = Column(Integer, ForeignKey('custom_field_def.id', ondelete='CASCADE'),
                       primary_key=True)
    value = Column(Text)

    field = relationship("CustomFieldDef")


class ToolModel(Base):
    """Per-tool custom STL model reference (mill VTK display). Unrelated to
    lathe schema v1; not created/queried anywhere today (dead stub)."""
    __tablename__ = 'tool_model'

    id = Column(Integer, primary_key=True)
    tool_no = Column(Integer)
    model = Column(Text)
    tool_table_id = Column(Integer, ForeignKey('tool_table.id'))
    tool_table = relationship("ToolTable", back_populates="tool_models")
