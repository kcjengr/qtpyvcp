"""
Plasma Processes Plugin
--------------------

Plugin to provide data storage and exposure for plasma table processes.

Example entry into yaml config file:
data_plugins:
  plasmaprocesses:
    provider: qtpyvcp.plugins.plasma_processes:PlasmaProcesses
    kwargs:
        # valid db_type string is "sqlite" or any other text.
        db_type: "sqlite"
        # connection_string is only used for non sqlite DBs.
        # Use a string that is appropriate for the specific DB in use.
        connect_string: "mysql+pymysql://someuser:somepassword@somehostname/plasma_table"
"""

import os

from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.utilities.misc import normalizePath
from qtpyvcp.plugins import Plugin

from sqlalchemy import create_engine
from sqlalchemy import Column, ForeignKey
from sqlalchemy import Integer, String, Float, LargeBinary
from sqlalchemy import and_
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.session import sessionmaker
from requests.sessions import session

LOG = getLogger(__name__)
BASE = declarative_base()
IN_DESIGNER = os.getenv('DESIGNER', False)

class addMixin(object):
    @classmethod
    def create(cls, session,  **kw):
        obj = cls(**kw)
        session.add(obj)
        session.commit()

    @classmethod
    def update(cls, session, qry, **kw):
        for k in kw:
            setattr(qry, k, kw[k])
        session.commit()

class Gas(addMixin, BASE):
    __tablename__ = 'gas'
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    
    def __init__(self, name):
        self.name = name

    @classmethod
    def get_all(cls, session):
        return session.query(cls).order_by(cls.name).all()


class LeadIn(addMixin, BASE):
    __tablename__ = 'leadin'
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    
    def __init__(self, name):
        self.name = name

    @classmethod
    def get_all(cls, session):
        return session.query(cls).order_by(cls.name).all()

class Machine(addMixin, BASE):
    __tablename__ = 'machine'
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    service_height = Column(Integer)

    def __init__(self, name, service_height):
        self.name = name
        self.service_height = service_height

    @classmethod
    def get_all(cls, session):
        return session.query(cls).order_by(cls.name).all()

class Material(addMixin, BASE):
    __tablename__ = 'material'
    id = Column(Integer, primary_key=True)
    name = Column(String(100))

    def __init__(self, name):
        self.name = name

    @classmethod
    def get_all(cls, session):
        return session.query(cls).order_by(cls.name).all()

class Thickness(addMixin, BASE):
    __tablename__ = 'thickness'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    thickness = Column(Float)

    def __init__(self, name, thickness):
        self.name = name
        self.thickness = thickness

    @classmethod
    def get_all(cls, session):
        return session.query(cls).order_by(cls.thickness).all()


class LinearSystem(addMixin, BASE):
    __tablename__ = 'linearsystem'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    unit_per_inch = Column(Float)

    def __init__(self, name, unit_per_inch):
        self.name = name
        self.unit_per_inch = unit_per_inch

    @classmethod
    def get_all(cls, session):
        return session.query(cls).order_by(cls.name).all()


class PressureSystem(addMixin, BASE):
    __tablename__ = 'pressuresystem'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    unit_per_psi = Column(Float)

    def __init__(self, name, unit_per_psi):
        self.name = name
        self.unit_per_psi = unit_per_psi

    @classmethod
    def get_all(cls, session):
        return session.query(cls).order_by(cls.name).all()


class Operation(addMixin, BASE):
    __tablename__ = 'operation'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))

    def __init__(self, name):
        self.name = name

    @classmethod
    def get_all(cls, session):
        return session.query(cls).order_by(cls.name).all()


class Quality(addMixin, BASE):
    __tablename__ = 'quality'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))

    def __init__(self, name):
        self.name = name

    @classmethod
    def get_all(cls, session):
        return session.query(cls).order_by(cls.name).all()


class Consumable(addMixin, BASE):
    __tablename__ = 'consumable'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    image_path = Column(String(100))
    image_blob = Column(LargeBinary)

    def __init__(self, name, image_path):
        self.name = name
        self.image_path = image_path

    @classmethod
    def get_all(cls, session):
        return session.query(cls).order_by(cls.name).all()


class HoleCut(addMixin, BASE):
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



class Cutchart(addMixin,BASE):
    __tablename__ = 'cutchart'
    id = Column(Integer, primary_key=True)
    # Foreign keys
    linearsystemid = Column(Integer, ForeignKey('linearsystem.id'))
    pressuresystemid = Column(Integer, ForeignKey('pressuresystem.id'))
    machineid = Column(Integer, ForeignKey('machine.id'))
    consumableid = Column(Integer, ForeignKey('consumable.id'))
    materialid = Column(Integer, ForeignKey('material.id'))
    thickenssid = Column(Integer, ForeignKey('thickness.id'))
    operationid = Column(Integer, ForeignKey('operation.id'))
    gasid = Column(Integer, ForeignKey('gas.id'))
    qualityid = Column(Integer, ForeignKey('quality.id'))
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
    name = Column(String(100))
    pierce_height = Column(Float)
    pierce_delay = Column(Float)
    cut_height = Column(Float)
    cut_speed = Column(Float)
    volts = Column(Float)
    kerf_width = Column(Float)
    plunge_rate = Column(Float)
    puddle_height = Column(Float)
    puddle_delay = Column(Float)
    amps = Column(Float)
    pressure = Column(Float)
    pause_at_end = Column(Float)

    @classmethod
    def get_all(cls, session):
        return session.query(cls) \
            .order_by(cls.name) \
            .all()

    @classmethod
    def get_exact_cut(cls, session, ls=0, ps=0, mch=0, con=0, mat=0, thi=0, op=0, gas=0, qua=0):
        result_set = session.query(cls) \
            .filter(and_( \
                         cls.linearsystemid == ls, \
                         cls.pressuresystemid == ps, \
                         cls.machineid == mch, \
                         cls.consumableid == con, \
                         cls.materialid == mat, \
                         cls.thickenssid == thi, \
                         cls.operationid == op, \
                         cls.gasid == gas, \
                         cls.qualityid == qua\
                        )).all()
        return result_set

class PlasmaProcesses(Plugin):
    def __init__(self, **kwargs):
        super(PlasmaProcesses, self).__init__()
        # determine what database to connect to.  Support types are:
        
        # stop data load processing if in designer
        if IN_DESIGNER:
            return
        
        if kwargs["db_type"] != "sqlite":
            self._engine = create_engine(kwargs["connect_string"], echo=True)
        else:
            self._persistence_file = normalizePath(path='plasma_table.db',
                                              base=os.getenv('CONFIG_DIR', '~/'))
            self._engine = create_engine('sqlite:///'+self._persistence_file, echo=True)


        # create the database for anything not already in place
        BASE.metadata.create_all(self._engine)
        # create and hold session for use of transactions
        self._session_maker = sessionmaker(bind=self._engine)
        self._session = self._session_maker()

    def gases(self):
        data = Gas.get_all(self._session)
        LOG.debug("Found Gases.")
        return data
    
    def addGas(self, gasname):
        Gas.create(self._session, name = gasname)
        LOG.debug(f"Add Gas {gasname}.")

    def leadins(self):
        data = LeadIn.get_all(self._session)
        LOG.debug("Found Leadins.")
        return data

    def machines(self):
        data = Machine.get_all(self._session)
        LOG.debug("Found Machines.")
        return data

    def materials(self):
        data = Material.get_all(self._session)
        LOG.debug("Found Materials.")
        return data
    
    def thicknesses(self):
        data = Thickness.get_all(self._session)
        LOG.debug("Found Thicknesses.")
        return data

    def linearsystems(self):
        data = LinearSystem.get_all(self._session)
        LOG.debug("Found Linear measurement systems.")
        return data

    def pressuresystems(self):
        data = PressureSystem.get_all(self._session)
        LOG.debug("Found pressure systems.")
        return data

    def operations(self):
        data = Operation.get_all(self._session)
        LOG.debug("Found Operations.")
        return data

    def qualities(self):
        data = Quality.get_all(self._session)
        LOG.debug("Found Quality list.")
        return data

    def consumables(self):
        data = Consumable.get_all(self._session)
        LOG.debug("Found Consumables.")
        return data

    def cut(self, arglst):
        # Order of params sent in.  Order matters for mapping to
        # arg list call. Not ideal 
        #  0 -> 'filter_gas',
        #  1 -> 'filter_machine',
        #  2 -> 'filter_material',
        #  3 -> 'filter_thickness',
        #  4 -> 'filter_distance_system',
        #  5 -> 'filter_pressure_system',
        #  6 -> 'filter_operation',
        #  7 -> 'filter_quality',
        #  8 -> 'filter_consumable'

        data = Cutchart.get_exact_cut(self._session, ls=arglst[4], ps=arglst[5], \
                                      mch=arglst[1], con=arglst[8], mat=arglst[2], \
                                      thi=arglst[3], op=arglst[6], gas=arglst[0], \
                                      qua=arglst[7])
        LOG.debug("Look for Cut data.")
        return data

    def addCut(self, **args):
        # build up forign keys. These are mandatory, we want things
        # to break if they are not dealt with.
        Cutchart.create(self._session, \
                        linearsystemid = args['linearsystems'], \
                        pressuresystemid = args['pressuresystems'], \
                        machineid = args['machines'], \
                        consumableid = args['consumables'], \
                        materialid = args['materials'], \
                        thickenssid = args['thicknesses'], \
                        operationid = args['operations'], \
                        gasid = args['gases'], \
                        qualityid = args['qualities'], \
                        name = args['name'], \
                        pierce_height = args['pierce_height'], \
                        pierce_delay = args['pierce_delay'], \
                        cut_height = args['cut_height'], 
                        cut_speed = args['cut_speed'], \
                        volts = args['volts'], \
                        kerf_width = args['kerf_width'], \
                        plunge_rate = args['plunge_rate'], \
                        puddle_height = args['puddle_height'], \
                        puddle_delay = args['puddle_delay'], \
                        amps = args['amps'], \
                        pressure = args['pressure'], \
                        pause_at_end = args['pause_at_end'])
        LOG.debug(f"Add cutchart: {args['name']}.")
    
    def updateCut(self, q, **args):
        Cutchart.update(self._session, q, \
                        pierce_height = args['pierce_height'], \
                        pierce_delay = args['pierce_delay'], \
                        cut_height = args['cut_height'], 
                        cut_speed = args['cut_speed'], \
                        volts = args['volts'], \
                        kerf_width = args['kerf_width'], \
                        plunge_rate = args['plunge_rate'], \
                        puddle_height = args['puddle_height'], \
                        puddle_delay = args['puddle_delay'], \
                        amps = args['amps'], \
                        pressure = args['pressure'], \
                        pause_at_end = args['pause_at_end'])
        LOG.debug(f"Update cutchart.")


    def initialise(self):
        LOG.debug('Initialising Plasma Processes plugin')
        self._initialized = True

    def terminate(self):
        self._session.close()
        return super().terminate()

if __name__ == "__main__":
    p = PlasmaProcesses(db_type='mysql', connect_string='mysql+pymysql://james:silk007@localhost/plasma_table')
    p.initialise()
    # ToDO: Possible initial load/import routines below here - for OEM type use
    