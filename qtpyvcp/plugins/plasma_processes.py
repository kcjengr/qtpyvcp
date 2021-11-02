
from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.plugins import Plugin

from sqlalchemy import create_engine
from sqlalchemy import Column, ForeignKey
from sqlalchemy import Integer, String, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

LOG = getLogger(__name__)
ENGINE = create_engine('sqlite:///plasma_table.db', echo=True)
BASE = declarative_base()

class Gas(BASE):
    __tablename__ = 'gas'
    id = Column(Integer, primary_key=True)

    name = Column(String)

class LeadIn(BASE):
    __tablename__ = 'leadin'
    id = Column(Integer, primary_key=True)

    name = Column(String)

class Machine(BASE):
    __tablename__ = 'machine'
    id = Column(Integer, primary_key=True)

    name = Column(String)
    service_height = Column(Integer)

class Material(BASE):
    __tablename__ = 'material'
    id = Column(Integer, primary_key=True)

    name = Column(String)

class Thickness(BASE):
    __tablename__ = 'thickness'
    id = Column(Integer, primary_key=True)

    name = Column(String)
    thickness = Column(Float)

class LinearSystem(BASE):
    __tablename__ = 'linearsystem'
    id = Column(Integer, primary_key=True)

    name = Column(String)
    unit_per_inch = Column(Float)

class PressureSystem(BASE):
    __tablename__ = 'pressuresystem'
    id = Column(Integer, primary_key=True)

    name = Column(String)
    unit_per_psi = Column(Float)

class Operation(BASE):
    __tablename__ = 'operation'
    id = Column(Integer, primary_key=True)

    name = Column(String)

class Quality(BASE):
    __tablename__ = 'quality'
    id = Column(Integer, primary_key=True)

    name = Column(String)

class Consumable(BASE):
    __tablename__ = 'consumable'
    id = Column(Integer, primary_key=True)

    name = Column(String)
    image_path = Column(String)

class HoleCut(BASE):
    __tablename__ = 'holecut'
    id = Column(Integer, primary_key=True)
    # Foreign key relationship
    materialid = Column(Integer, ForeignKey('material.id'))
    thickenssid = Column(Integer, ForeignKey('thickness.id'))
    material = relationship('Material')
    thickness = relationship('Thickness')
    # hole base size that interperlation stems from
    base_hole = Column(Float)
    # hole base interperlation factor (i.e. scaling from base)
    scale = Column(Float)
    # hole size banding
    lower_size = Column(Float)
    upper_size = Column(Float)
    # cut data
    leadin_radius = Column(Float)
    kerf = Column(Float)
    cut_height = Column(Float)
    speed1 = Column(Float)
    speed2 = Column(Float)
    speed2_distance = Column(Float)
    plasma_off_distance = Column(Float)
    over_cut = Column(Float)


class Cutchart(BASE):
    __tablename__ = 'cutchart'
    id = Column(Integer, primary_key=True)

    # Foreign keys
    linearsystemid = Column(Integer, ForeignKey('linearsystem.id'))
    pressuresystemid = Column(Integer, ForeignKey('pressuresystem.id'))
    machineid = Column(Integer, ForeignKey('machine.id'))
    consumableid = Column(Integer, ForeignKey('consumable.id'))
    materialid = Column(Integer, ForeignKey('material.id'))
    thickenssid = Column(Integer, ForeignKey('thicknes.id'))
    operationid = Column(Integer, ForeignKey('operation.id'))
    gasid = Column(Integer, ForeignKey('gas.id'))
    qualityid = Column(Integer, ForeignKey('quality.id'))
    circleid = Column(Integer, ForeignKey('circlecut.id'))
    # Define relationships
    linearsystem = relationship('LinearSystem')
    pressuresystem = relationship('PressureSystem')
    machine = relationship('Machine')
    consumable = relationship('Consumable')
    material = relationship('Material')
    thickness = relationship('Thickness')
    operation = relationship('Operation')
    gas = relationship('Gas')
    quality = relationship('Quality')
    # values for this combination of foreign keys
    name = Column(String)
    pierce_height = Column(Float)
    pierce_delay = Column(Float)
    cut_height = Column(Float)
    cut_speed = Column(Float)
    volts = Column(Float)
    kerf_width = Column(Float)
    thc_delay = Column(Float)
    plunge_rate = Column(Float)
    puddle_height = Column(Float)
    amps = Column(Float)
    pressure = Column(Float)

class PlasmaProcesses(Plugin):
    def __init__(self, **kwargs):
        super(PlasmaProcesses, self).__init__()
    
    def initialise(self):
        LOG.debug('Initialising Plasma Processes plugin')
        self._initialized = True

    def terminate(self):
        return super().terminate()