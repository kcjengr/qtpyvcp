import os
import tempfile
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Must be set before importing plasma_processes (which reads it at module level)
os.environ['DESIGNER'] = '1'

from qtpyvcp.plugins.plasma_processes import (
    Gas, Machine, Material, LinearSystem, Thickness,
    PressureSystem, Operation, Quality, Consumable, HoleCut, Cutchart,
    crudMixin, BASE
)


@pytest.fixture()
def engine():
    e = create_engine('sqlite:///:memory:')
    BASE.metadata.create_all(e)
    yield e
    BASE.metadata.drop_all(e)


@pytest.fixture()
def session(engine):
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()


# ─── crudMixin ──────────────────────────────────────────────────────

class TestCrudMixinCreate:
    def test_create_gas(self, session):
        id_ = Gas.create(session, name='Air')
        assert isinstance(id_, int)
        g = session.query(Gas).get(id_)
        assert g is not None
        assert g.name == 'Air'

    def test_create_machine(self, session):
        id_ = Machine.create(session, name='MyMachine', service_height=100)
        m = session.query(Machine).get(id_)
        assert m.name == 'MyMachine'
        assert m.service_height == 100

    def test_create_material(self, session):
        id_ = Material.create(session, name='Mild Steel', code='ms')
        mat = session.query(Material).get(id_)
        assert mat.name == 'Mild Steel'
        assert mat.code == 'ms'

    def test_returns_int_id(self, session):
        id_ = Gas.create(session, name='Oxygen')
        assert isinstance(id_, int)


class TestCrudMixinUpdate:
    def test_update_gas_name(self, session):
        id_ = Gas.create(session, name='OldName')
        g = session.query(Gas).get(id_)
        Gas.update(session, (g,), name='NewName')
        assert g.name == 'NewName'

    def test_update_multiple_fields(self, session):
        id_ = Machine.create(session, name='A', service_height=50)
        m = session.query(Machine).get(id_)
        Machine.update(session, (m,), name='B', service_height=200)
        assert m.name == 'B'
        assert m.service_height == 200


class TestCrudMixinDelete:
    def test_delete_gas(self, session):
        id_ = Gas.create(session, name='ToDelete')
        g = session.query(Gas).get(id_)
        crudMixin.delete(session, g)
        result = session.query(Gas).filter_by(id=id_).first()
        assert result is None


class TestCrudMixinGetAll:
    def test_get_all_gases(self, session):
        Gas.create(session, name='Gas1')
        Gas.create(session, name='Gas2')
        all_gases = Gas.get_all(session)
        assert len(all_gases) == 2
        # Ordered by name
        assert all_gases[0].name < all_gases[1].name

    def test_get_all_empty(self, session):
        result = Gas.get_all(session)
        assert result == []


class TestCrudMixinGetByKey:
    def test_get_by_key_returns_list(self, session):
        Gas.create(session, name='Air')
        Gas.create(session, name='Nitrogen')
        result = Gas.get_by_key(session, 'name', 'Air')
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].name == 'Air'

    def test_get_by_key_no_match(self, session):
        result = Gas.get_by_key(session, 'name', 'Nonexistent')
        assert result == []

    def test_get_by_key_invalid_key_returns_none(self, session):
        result = Gas.get_by_key(session, 'nonexistent_field', 'x')
        assert result is None


# ─── Model classes: simple CRUD ─────────────────────────────────────

class TestGasModel:
    def test_table_name(self):
        assert Gas.__tablename__ == 'gas'

    def test_id_is_primary_key(self, session):
        id_ = Gas.create(session, name='Test')
        g = session.query(Gas).get(id_)
        assert g.id == id_

    def test_name_column(self, session):
        id_ = Gas.create(session, name='Argon')
        g = session.query(Gas).get(id_)
        assert g.name == 'Argon'


class TestMachineModel:
    def test_table_name(self):
        assert Machine.__tablename__ == 'machine'

    def test_service_height_column(self, session):
        id_ = Machine.create(session, name='CNC-Plasma', service_height=150)
        m = session.query(Machine).get(id_)
        assert m.service_height == 150


class TestMaterialModel:
    def test_table_name(self):
        assert Material.__tablename__ == 'material'

    def test_code_column(self, session):
        id_ = Material.create(session, name='Aluminium', code='al')
        mat = session.query(Material).get(id_)
        assert mat.code == 'al'


class TestLinearSystemModel:
    def test_table_name(self):
        assert LinearSystem.__tablename__ == 'linearsystem'

    def test_unit_per_inch_column(self, session):
        id_ = LinearSystem.create(session, name='mm', unit_per_inch=24.5)
        ls = session.query(LinearSystem).get(id_)
        assert ls.unit_per_inch == 24.5


class TestThicknessModel:
    def test_table_name(self):
        assert Thickness.__tablename__ == 'thickness'

    def test_thickness_column(self, session):
        mm_id = LinearSystem.create(session, name='mm', unit_per_inch=24.5)
        id_ = Thickness.create(session, name='3mm', thickness=3.0, linearsystemid=mm_id)
        t = session.query(Thickness).get(id_)
        assert t.thickness == 3.0

    def test_relationship_to_linear_system(self, session):
        mm_id = LinearSystem.create(session, name='mm', unit_per_inch=24.5)
        id_ = Thickness.create(session, name='3mm', thickness=3.0, linearsystemid=mm_id)
        t = session.query(Thickness).get(id_)
        assert t.linearsystem is not None
        assert t.linearsystem.name == 'mm'

    def test_get_all_without_filter(self, session):
        mm_id = LinearSystem.create(session, name='mm', unit_per_inch=24.5)
        Thickness.create(session, name='1mm', thickness=1.0, linearsystemid=mm_id)
        Thickness.create(session, name='3mm', thickness=3.0, linearsystemid=mm_id)
        result = Thickness.get_all(session)
        assert len(result) == 2

    def test_get_all_with_linear_filter(self, session):
        mm_id = LinearSystem.create(session, name='mm', unit_per_inch=24.5)
        inch_id = LinearSystem.create(session, name='inch', unit_per_inch=1.0)
        Thickness.create(session, name='3mm', thickness=3.0, linearsystemid=mm_id)
        Thickness.create(session, name='1/4in', thickness=0.25, linearsystemid=inch_id)
        result = Thickness.get_all(session, linear=mm_id)
        assert len(result) == 1
        assert result[0].name == '3mm'


class TestPressureSystemModel:
    def test_table_name(self):
        assert PressureSystem.__tablename__ == 'pressuresystem'

    def test_unit_per_psi_column(self, session):
        id_ = PressureSystem.create(session, name='psi', unit_per_psi=1.0)
        ps = session.query(PressureSystem).get(id_)
        assert ps.unit_per_psi == 1.0


class TestOperationModel:
    def test_table_name(self):
        assert Operation.__tablename__ == 'operation'

    def test_name_column(self, session):
        id_ = Operation.create(session, name='Cut')
        op = session.query(Operation).get(id_)
        assert op.name == 'Cut'


class TestQualityModel:
    def test_table_name(self):
        assert Quality.__tablename__ == 'quality'

    def test_name_column(self, session):
        id_ = Quality.create(session, name='Production')
        q = session.query(Quality).get(id_)
        assert q.name == 'Production'


class TestConsumableModel:
    def test_table_name(self):
        assert Consumable.__tablename__ == 'consumable'

    def test_image_path_column(self, session):
        id_ = Consumable.create(session, name='Shielded', image_path='/path/to/img')
        c = session.query(Consumable).get(id_)
        assert c.image_path == '/path/to/img'


# ─── HoleCut ────────────────────────────────────────────────────────

class TestHoleCutModel:
    def test_table_name(self):
        assert HoleCut.__tablename__ == 'holecut'

    def test_foreign_keys(self, session):
        m = Machine.create(session, name='M1', service_height=100)
        mat = Material.create(session, name='MS', code='ms')
        mm_id = LinearSystem.create(session, name='mm', unit_per_inch=24.5)
        t = Thickness.create(session, name='3mm', thickness=3.0, linearsystemid=mm_id)
        g = Gas.create(session, name='Air')

        hc = HoleCut.create(session,
            machineid=m, materialid=mat, thicknessid=t, gas2id=g,
            amps=100.0, hole_size=10.0, leadin_radius=5.0, kerf=1.0,
            cut_height=4.0, leadin_speed=500.0, speed1=300.0,
            speed2=250.0, speed3=200.0, overburn_speed=100.0,
            overburn_adjust=1.0, straight_leadin=True)

        hc_obj = session.query(HoleCut).get(hc)
        assert hc_obj.machine is not None
        assert hc_obj.material is not None
        assert hc_obj.thickness is not None
        assert hc_obj.gas2 is not None

    def test_get_holes(self, session):
        m = Machine.create(session, name='M1', service_height=100)
        mat = Material.create(session, name='MS', code='ms')
        mm_id = LinearSystem.create(session, name='mm', unit_per_inch=24.5)
        t = Thickness.create(session, name='3mm', thickness=3.0, linearsystemid=mm_id)
        g = Gas.create(session, name='Air')

        HoleCut.create(session, machineid=m, materialid=mat, thicknessid=t, gas2id=g,
            hole_size=15.0, amps=100.0, leadin_radius=5.0, kerf=1.0, cut_height=4.0,
            leadin_speed=500.0, speed1=300.0, speed2=250.0, speed3=200.0,
            overburn_speed=100.0, overburn_adjust=1.0, straight_leadin=True)

        holes = HoleCut.get_holes(session, mch=m, mat=mat, thi=t)
        assert len(holes) == 1
        assert holes[0].hole_size == 15.0


# ─── Cutchart ───────────────────────────────────────────────────────

class TestCutchartModel:
    def test_table_name(self):
        assert Cutchart.__tablename__ == 'cutchart'

    def _setup_cutchart(self, session, tool_number=1):
        ls = LinearSystem.create(session, name='mm', unit_per_inch=24.5)
        ps = PressureSystem.create(session, name='psi', unit_per_psi=1.0)
        m = Machine.create(session, name='M1', service_height=100)
        con = Consumable.create(session, name='Shielded', image_path='/img')
        mat = Material.create(session, name='MS', code='ms')
        t = Thickness.create(session, name='3mm', thickness=3.0, linearsystemid=ls)
        op = Operation.create(session, name='Cut')
        g = Gas.create(session, name='Air')
        q = Quality.create(session, name='Production')

        return Cutchart.create(session,
            linearsystemid=ls, pressuresystemid=ps, machineid=m,
            consumableid=con, materialid=mat, thicknessid=t,
            operationid=op, gasid=g, qualityid=q,
            tool_number=tool_number, name='TestCut', pierce_height=5.0,
            pierce_delay=1.0, cut_height=4.0, cut_speed=300.0,
            volts=100.0, kerf_width=1.0, plunge_rate=10.0,
            puddle_height=3.0, puddle_delay=0.5, amps=100.0,
            pressure=15.0, pause_at_end=2.0, smallest_hole=3.0)

    def test_foreign_keys(self, session):
        id_ = self._setup_cutchart(session)
        cc = session.query(Cutchart).get(id_)
        assert cc.linearsystem is not None
        assert cc.pressuresystem is not None
        assert cc.machine is not None
        assert cc.consumable is not None
        assert cc.material is not None
        assert cc.thickness is not None
        assert cc.operation is not None
        assert cc.gas is not None
        assert cc.quality is not None

    def test_get_exact_cut(self, session):
        ls = LinearSystem.create(session, name='mm', unit_per_inch=24.5)
        ps = PressureSystem.create(session, name='psi', unit_per_psi=1.0)
        m = Machine.create(session, name='M1', service_height=100)
        con = Consumable.create(session, name='Shielded', image_path='/img')
        mat = Material.create(session, name='MS', code='ms')
        t = Thickness.create(session, name='3mm', thickness=3.0, linearsystemid=ls)
        op = Operation.create(session, name='Cut')
        g = Gas.create(session, name='Air')
        q = Quality.create(session, name='Production')

        Cutchart.create(session,
            linearsystemid=ls, pressuresystemid=ps, machineid=m,
            consumableid=con, materialid=mat, thicknessid=t,
            operationid=op, gasid=g, qualityid=q,
            tool_number=1, name='Cut1', pierce_height=5.0, pierce_delay=1.0,
            cut_height=4.0, cut_speed=300.0, volts=100.0, kerf_width=1.0,
            plunge_rate=10.0, puddle_height=3.0, puddle_delay=0.5,
            amps=100.0, pressure=15.0, pause_at_end=2.0)

        results = Cutchart.get_exact_cut(session, ls=ls, ps=ps, mch=m,
                                         con=con, mat=mat, thi=t, op=op, gas=g, qua=q)
        assert len(results) == 1
        assert results[0].name == 'Cut1'

    def test_tool_number_column(self, session):
        id_ = self._setup_cutchart(session, tool_number=42)
        cc = session.query(Cutchart).get(id_)
        assert cc.tool_number == 42

    def test_smallest_hole_column(self, session):
        ls = LinearSystem.create(session, name='mm', unit_per_inch=24.5)
        ps = PressureSystem.create(session, name='psi', unit_per_psi=1.0)
        m = Machine.create(session, name='M1', service_height=100)
        con = Consumable.create(session, name='Shielded', image_path='/img')
        mat = Material.create(session, name='MS', code='ms')
        t = Thickness.create(session, name='3mm', thickness=3.0, linearsystemid=ls)
        op = Operation.create(session, name='Cut')
        g = Gas.create(session, name='Air')
        q = Quality.create(session, name='Production')

        id_ = Cutchart.create(session,
            linearsystemid=ls, pressuresystemid=ps, machineid=m,
            consumableid=con, materialid=mat, thicknessid=t,
            operationid=op, gasid=g, qualityid=q,
            tool_number=1, name='SmallHole', pierce_height=5.0, pierce_delay=1.0,
            cut_height=4.0, cut_speed=300.0, volts=100.0, kerf_width=1.0,
            plunge_rate=10.0, puddle_height=3.0, puddle_delay=0.5,
            amps=100.0, pressure=15.0, pause_at_end=2.0, smallest_hole=2.5)
        cc = session.query(Cutchart).get(id_)
        assert cc.smallest_hole == 2.5


# ─── PlasmaProcesses plugin ────────────────────────────────────────

class TestPlasmaProcessesPlugin:
    def setup_method(self):
        self.engine = create_engine('sqlite:///:memory:')
        BASE.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def teardown_method(self):
        self.session.close()
        BASE.metadata.drop_all(self.engine)

    def _make_plugin(self):
        from qtpyvcp.plugins.plasma_processes import PlasmaProcesses
        p = PlasmaProcesses(db_type='sqlite')
        p._engine = self.engine
        p._session = self.session
        return p

    def test_drop_all_and_build_all(self):
        p = self._make_plugin()
        Gas.create(self.session, name='Air')
        assert len(Gas.get_all(self.session)) == 1
        p.drop_all()
        p.build_all()
        assert len(Gas.get_all(self.session)) == 0

    def test_gases_method(self):
        p = self._make_plugin()
        Gas.create(self.session, name='Air')
        Gas.create(self.session, name='Nitrogen')
        result = p.gases()
        assert len(result) == 2

    def test_add_gas(self):
        p = self._make_plugin()
        id_ = p.add_gas('Oxygen')
        g = self.session.query(Gas).get(id_)
        assert g.name == 'Oxygen'

    def test_machines_method(self):
        p = self._make_plugin()
        Machine.create(self.session, name='M1', service_height=100)
        result = p.machines()
        assert len(result) == 1

    def test_add_machine(self):
        p = self._make_plugin()
        id_ = p.add_machine('MyPlasma', 150)
        m = self.session.query(Machine).get(id_)
        assert m.name == 'MyPlasma'
        assert m.service_height == 150

    def test_materials_method(self):
        p = self._make_plugin()
        Material.create(self.session, name='Mild Steel', code='ms')
        result = p.materials()
        assert len(result) == 1

    def test_add_materials(self):
        p = self._make_plugin()
        id_ = p.add_materials('Aluminium', 'al')
        mat = self.session.query(Material).get(id_)
        assert mat.name == 'Aluminium'
        assert mat.code == 'al'

    def test_thicknesses_method(self):
        p = self._make_plugin()
        mm_id = LinearSystem.create(self.session, name='mm', unit_per_inch=24.5)
        Thickness.create(self.session, name='3mm', thickness=3.0, linearsystemid=mm_id)
        result = p.thicknesses()
        assert len(result) == 1

    def test_add_thickness(self):
        p = self._make_plugin()
        mm_id = LinearSystem.create(self.session, name='mm', unit_per_inch=24.5)
        id_ = p.add_thickness('6mm', 6.0, mm_id)
        t = self.session.query(Thickness).get(id_)
        assert t.name == '6mm'
        assert t.thickness == 6.0

    def test_linearsystems_method(self):
        p = self._make_plugin()
        LinearSystem.create(self.session, name='mm', unit_per_inch=24.5)
        result = p.linearsystems()
        assert len(result) == 1

    def test_add_linearsystems(self):
        p = self._make_plugin()
        id_ = p.add_linearsystems('inch', 1.0)
        ls = self.session.query(LinearSystem).get(id_)
        assert ls.name == 'inch'
        assert ls.unit_per_inch == 1.0

    def test_pressuresystems_method(self):
        p = self._make_plugin()
        PressureSystem.create(self.session, name='psi', unit_per_psi=1.0)
        result = p.pressuresystems()
        assert len(result) == 1

    def test_add_pressuresystems(self):
        p = self._make_plugin()
        id_ = p.add_pressuresystems('bar', 0.0689476)
        ps = self.session.query(PressureSystem).get(id_)
        assert ps.name == 'bar'
        assert ps.unit_per_psi == 0.0689476

    def test_operations_method(self):
        p = self._make_plugin()
        Operation.create(self.session, name='Cut')
        result = p.operations()
        assert len(result) == 1

    def test_add_operations(self):
        p = self._make_plugin()
        id_ = p.add_operations('Mark/Spot')
        op = self.session.query(Operation).get(id_)
        assert op.name == 'Mark/Spot'

    def test_qualities_method(self):
        p = self._make_plugin()
        Quality.create(self.session, name='Production')
        result = p.qualities()
        assert len(result) == 1

    def test_add_qualities(self):
        p = self._make_plugin()
        id_ = p.add_qualities('Fine')
        q = self.session.query(Quality).get(id_)
        assert q.name == 'Fine'

    def test_consumables_method(self):
        p = self._make_plugin()
        Consumable.create(self.session, name='Shielded', image_path='/img')
        result = p.consumables()
        assert len(result) == 1

    def test_add_consumables(self):
        p = self._make_plugin()
        id_ = p.add_consumables('Unshielded')
        c = self.session.query(Consumable).get(id_)
        assert c.name == 'Unshielded'


# ─── CSV seed_data_base ─────────────────────────────────────────────

class TestSeedDataBase:
    """Test seed_data_base with a minimal CSV fixture."""

    @pytest.fixture()
    def csv_content(self):
        return (
            "machine_name\tthickness_name\tthickness\tthickness_unit\tmaterial\t"
            "pressuresys\tconsumable\ttool_number\tname\tpierce_height\tpierce_delay\t"
            "cut_height\tcut_speed\tvolts\tkerf_width\tplunge_rate\tpuddle_height\t"
            "puddle_delay\tamps\tpressure\tpause_at_end\n"
            "M1\t3mm\t3.0\tmm\tMild Steel\tpsi\tShielded\t1\tCut1\t5.0\t1.0\t"
            "4.0\t300.0\t100.0\t1.0\t10.0\t3.0\t0.5\t100.0\t15.0\t2.0\n"
        )

    @pytest.fixture()
    def csv_file(self, tmp_path, csv_content):
        f = tmp_path / 'cutdata.csv'
        f.write_text(csv_content)
        return str(f)

    def _make_plasma_plugin(self, engine, session):
        from qtpyvcp.plugins.plasma_processes import PlasmaProcesses
        p = PlasmaProcesses(db_type='sqlite')
        p._engine = engine
        p._session = session
        return p

    def test_seed_data_base_populates_tables(self, csv_file):
        engine = create_engine('sqlite:///:memory:')
        BASE.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        p = self._make_plasma_plugin(engine, session)
        p.seed_data_base(csv_file)

        assert Gas.get_all(session) != []
        assert Machine.get_all(session) != []
        assert Material.get_all(session) != []
        assert LinearSystem.get_all(session) != []
        assert Thickness.get_all(session) != []
        assert PressureSystem.get_all(session) != []
        assert Operation.get_all(session) != []
        assert Quality.get_all(session) != []
        assert Consumable.get_all(session) != []

    def test_seed_data_base_creates_machines(self, csv_file):
        engine = create_engine('sqlite:///:memory:')
        BASE.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        p = self._make_plasma_plugin(engine, session)
        p.seed_data_base(csv_file)

        machines = Machine.get_all(session)
        names = [m.name for m in machines]
        assert 'M1' in names

    def test_seed_data_base_creates_linear_systems(self, csv_file):
        engine = create_engine('sqlite:///:memory:')
        BASE.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        p = self._make_plasma_plugin(engine, session)
        p.seed_data_base(csv_file)

        names = [ls.name for ls in LinearSystem.get_all(session)]
        assert 'mm' in names
        assert 'inch' in names

    def test_seed_data_base_creates_pressure_systems(self, csv_file):
        engine = create_engine('sqlite:///:memory:')
        BASE.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        p = self._make_plasma_plugin(engine, session)
        p.seed_data_base(csv_file)

        names = [ps.name for ps in PressureSystem.get_all(session)]
        assert 'psi' in names

    def test_seed_data_base_creates_materials(self, csv_file):
        engine = create_engine('sqlite:///:memory:')
        BASE.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        p = self._make_plasma_plugin(engine, session)
        p.seed_data_base(csv_file)

        mats = {m.name: m.code for m in Material.get_all(session)}
        assert 'Mild Steel' in mats
        assert mats['Mild Steel'] == 'ms'

    def test_seed_data_base_creates_gases(self, csv_file):
        engine = create_engine('sqlite:///:memory:')
        BASE.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        p = self._make_plasma_plugin(engine, session)
        p.seed_data_base(csv_file)

        names = [g.name for g in Gas.get_all(session)]
        assert 'Air - Air' in names
        assert 'Nitrogen - Air' in names

    def test_seed_data_base_creates_operations(self, csv_file):
        engine = create_engine('sqlite:///:memory:')
        BASE.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        p = self._make_plasma_plugin(engine, session)
        p.seed_data_base(csv_file)

        names = [op.name for op in Operation.get_all(session)]
        assert 'Cut' in names
        assert 'Pierce' in names

    def test_seed_data_base_creates_qualities(self, csv_file):
        engine = create_engine('sqlite:///:memory:')
        BASE.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        p = self._make_plasma_plugin(engine, session)
        p.seed_data_base(csv_file)

        names = [q.name for q in Quality.get_all(session)]
        assert 'Production' in names
        assert 'Fine' in names

    def test_seed_data_base_creates_consumables(self, csv_file):
        engine = create_engine('sqlite:///:memory:')
        BASE.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        p = self._make_plasma_plugin(engine, session)
        p.seed_data_base(csv_file)

        names = [c.name for c in Consumable.get_all(session)]
        assert 'Shielded' in names
        assert 'Unshielded' in names

    def test_seed_data_base_creates_cutcharts(self, csv_file):
        engine = create_engine('sqlite:///:memory:')
        BASE.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        p = self._make_plasma_plugin(engine, session)
        p.seed_data_base(csv_file)

        cutcharts = Cutchart.get_all(session)
        assert len(cutcharts) == 1
        assert cutcharts[0].name == 'Cut1'
        assert cutcharts[0].tool_number == 1
        assert cutcharts[0].amps == 100.0

    def test_seed_data_base_multiple_rows(self, tmp_path):
        csv_content = (
            "machine_name\tthickness_name\tthickness\tthickness_unit\tmaterial\t"
            "pressuresys\tconsumable\ttool_number\tname\tpierce_height\tpierce_delay\t"
            "cut_height\tcut_speed\tvolts\tkerf_width\tplunge_rate\tpuddle_height\t"
            "puddle_delay\tamps\tpressure\tpause_at_end\n"
            "M1\t3mm\t3.0\tmm\tMild Steel\tpsi\tShielded\t1\tCut1\t5.0\t1.0\t"
            "4.0\t300.0\t100.0\t1.0\t10.0\t3.0\t0.5\t100.0\t15.0\t2.0\n"
            "M1\t6mm\t6.0\tmm\tMild Steel\tpsi\tShielded\t2\tCut2\t6.0\t1.5\t"
            "5.0\t250.0\t110.0\t1.2\t12.0\t3.5\t0.6\t110.0\t16.0\t2.5\n"
        )
        f = tmp_path / 'cutdata.csv'
        f.write_text(csv_content)

        engine = create_engine('sqlite:///:memory:')
        BASE.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        p = self._make_plasma_plugin(engine, session)
        p.seed_data_base(str(f))

        cutcharts = Cutchart.get_all(session)
        assert len(cutcharts) == 2

    def test_seed_data_base_drops_and_rebuilds(self, csv_file):
        engine = create_engine('sqlite:///:memory:')
        BASE.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        # Pre-populate some stale data
        Gas.create(session, name='OldGas')
        assert len(Gas.get_all(session)) == 1

        p = self._make_plasma_plugin(engine, session)
        p.seed_data_base(csv_file)

        # OldGas should be gone after drop_all + rebuild
        names = [g.name for g in Gas.get_all(session)]
        assert 'OldGas' not in names

    def test_seed_data_base_material_mapping(self, tmp_path):
        """Verify material-to-code mapping in seed_data_base."""
        csv_content = (
            "machine_name\tthickness_name\tthickness\tthickness_unit\tmaterial\t"
            "pressuresys\tconsumable\ttool_number\tname\tpierce_height\tpierce_delay\t"
            "cut_height\tcut_speed\tvolts\tkerf_width\tplunge_rate\tpuddle_height\t"
            "puddle_delay\tamps\tpressure\tpause_at_end\n"
            "M1\t3mm\t3.0\tmm\tAluminium\tpsi\tShielded\t1\tCut1\t5.0\t1.0\t"
            "4.0\t300.0\t100.0\t1.0\t10.0\t3.0\t0.5\t100.0\t15.0\t2.0\n"
        )
        f = tmp_path / 'cutdata.csv'
        f.write_text(csv_content)

        engine = create_engine('sqlite:///:memory:')
        BASE.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        p = self._make_plasma_plugin(engine, session)
        p.seed_data_base(str(f))

        mats = {m.name: m.code for m in Material.get_all(session)}
        assert mats['Aluminium'] == 'al'

    def test_seed_data_base_thickness_units(self, csv_file):
        """Verify thickness is assigned to correct linear system based on unit."""
        engine = create_engine('sqlite:///:memory:')
        BASE.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        p = self._make_plasma_plugin(engine, session)
        p.seed_data_base(csv_file)

        # 3mm should be linked to mm linear system (id=1 from seed order)
        mms = [t for t in Thickness.get_all(session) if t.linearsystem.name == 'mm']
        assert len(mms) == 1
        assert mms[0].name == '3mm'
