# coding=utf-8
"""ORM models for the qtpyvcp tool database.

``Tool`` (+ ``ToolLathe``/``CustomFieldDef``/``CustomFieldValue``/``Meta``) map
schema v1 (frozen 2026-07-03, see ``migrations/001_initial.sql`` -- the
authoritative DDL; these Column definitions mirror it for ORM use, they do
not create it. ``VisibleColumn`` is schema v2 (``migrations/
002_ui_visible_columns.sql``); ``ToolMill`` is schema v3 (``migrations/
003_tool_mill.sql``). Use :func:`qtpyvcp.lib.db_tool.migrate.run_migrations`
to create/upgrade the actual tables.

``ToolTable``/``ToolModel`` are an unrelated, currently-unused stub for a
per-tool custom STL model file (mill VTK display, see
``widgets/display_widgets/vtk_backplot/tool_actor.py``); no code creates
``ToolModel`` rows today. Kept as-is, decoupled from ``Tool`` (which no
longer carries a ``tool_table_id`` FK per schema v1).
"""

from sqlalchemy import (Column, String, Integer, Table, ForeignKey, Float,
                         Text, Boolean, CheckConstraint)
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
    mill = relationship("ToolMill", uselist=False, back_populates="tool",
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
    holder_head_length = Column(Float)  # holder LH; protruding head --
                                       # the stickout that governs reach
    holder_oal = Column(Float)         # holder OAL; full physical length,
                                       # mostly clamped. Not a stickout.         # holder overall length

    # grooving / parting
    groove_width = Column(Float)       # cutting edge width
    max_depth_of_cut = Column(Float)   # groove insert usable depth (display length)

    # drills / taps (round tools; no holder rows apply)
    drill_point_angle = Column(Float)  # SIG, e.g. 118 / 135
    flute_length = Column(Float)       # LCF; fluted portion of a drill/tap
    length_below_holder = Column(Float)  # LB; protrusion from the holder --
                                         # what bounds how deep it can be driven
    overall_length = Column(Float)     # tool OAL (tap/drill; thread insert length)
    shaft_diameter = Column(Float)     # SFDM; tap/drill shank
    chamfer_threads = Column(Float)    # tap lead/chamfer threads (e.g. 2.5)

    # threading
    # A tap cuts one pitch (TP). A threading insert cuts a RANGE, bounded by
    # TPN/TPX -- and they really do differ: SIR-375-H11-11IRA60 exports
    # TPN 0.03 against TPX 0.0625. Collapsing all three into one column lost
    # the minimum and left a tap's pitch in a field called "max".
    thread_pitch = Column(Float)       # TP; the tap's fixed pitch
    # Pitch is the distance between threads, so a SMALL pitch is a fine
    # thread and a LARGE one is coarse. min/max therefore read the opposite
    # way round to "fine/coarse", which is worth stating rather than leaving
    # to be re-derived.
    thread_pitch_min = Column(Float)   # TPN; finest thread the insert cuts
    thread_pitch_max = Column(Float)   # TPX; coarsest thread the insert cuts
    thread_angle = Column(Float)       # profile angle, default 60
    thread_tip_type = Column(Text)     # point | flat | round  (radius accepted as a synonym)

    # feeds & speeds defaults (conversational autofill)
    surface_speed = Column(Float)      # SFM / SMM per meta.units
    feed_per_rev = Column(Float)
    depth_of_cut = Column(Float)

    notes = Column(Text, nullable=False, default='')


class ToolMill(Base):
    """Mill extras (schema v3): consumed by the mill UI and machine macros;
    never sent to LinuxCNC. A tool with no row here reads as the column
    defaults (rows appear lazily on first save)."""
    __tablename__ = 'tool_mill'

    tool_id = Column(Integer, ForeignKey('tool.id', ondelete='CASCADE'),
                      primary_key=True)
    tool = relationship("Tool", back_populates="mill")

    # storable in the ATC carousel: False = the tool does not physically fit
    # between carousel pockets (oversize) and the M6 remap must never
    # auto-stow it into, or auto-fetch it from, the carousel.
    atc = Column(Boolean, nullable=False, default=True, server_default='1')


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


class VisibleColumn(Base):
    """One row per tool-table column key currently checked visible (schema
    v2, plan §6 Phase 3 follow-up) -- core, extras, and custom columns
    alike. The whole table is replaced atomically on every visibility
    change (see DBToolTable.setVisibleColumns), so its rows are always
    exactly "whatever's checked right now," not an event log."""
    __tablename__ = 'ui_visible_column'

    column_key = Column(Text, primary_key=True)


class ToolModel(Base):
    """Per-tool custom STL model reference (mill VTK display). Unrelated to
    lathe schema v1; not created/queried anywhere today (dead stub)."""
    __tablename__ = 'tool_model'

    id = Column(Integer, primary_key=True)
    tool_no = Column(Integer)
    model = Column(Text)
    tool_table_id = Column(Integer, ForeignKey('tool_table.id'))
    tool_table = relationship("ToolTable", back_populates="tool_models")
