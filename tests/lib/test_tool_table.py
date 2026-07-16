import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from qtpyvcp.lib.db_tool.base import Base
from qtpyvcp.lib.db_tool.tool_table import ToolTable, Tool, ToolModel


@pytest.fixture
def session():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db_session = Session()
    yield db_session
    db_session.close()


class TestToolTableCRUD:
    def test_create_and_query(self, session):
        table = ToolTable(name='my_table')
        session.add(table)
        session.commit()

        result = session.query(ToolTable).filter_by(name='my_table').first()
        assert result is not None
        assert result.name == 'my_table'

    def test_tool_table_has_no_tools_initially(self, session):
        table = ToolTable(name='empty')
        session.add(table)
        session.commit()

        fresh = session.query(ToolTable).filter_by(name='empty').first()
        assert len(fresh.tools) == 0

    def test_add_tools_to_table(self, session):
        table = ToolTable(name='with_tools')
        tool1 = Tool(tool_no=1, remark='tool one', tool_table=table)
        tool2 = Tool(tool_no=2, remark='tool two', tool_table=table)
        session.add(table)
        session.commit()

        fresh = session.query(ToolTable).filter_by(name='with_tools').first()
        assert len(fresh.tools) == 2

    def test_tool_table_id_auto_increment(self, session):
        t1 = ToolTable(name='first')
        t2 = ToolTable(name='second')
        session.add_all([t1, t2])
        session.commit()

        fresh_t1 = session.query(ToolTable).filter_by(name='first').first()
        fresh_t2 = session.query(ToolTable).filter_by(name='second').first()
        assert fresh_t1.id == 1
        assert fresh_t2.id == 2


class TestToolCRUD:
    def test_create_tool_with_all_offsets(self, session):
        table = ToolTable(name='main')
        session.add(table)
        session.commit()

        tool = Tool(
            tool_no=5, in_use=1, pocket=3,
            x_offset=0.1, y_offset=-0.2, z_offset=0.05,
            a_offset=0.0, b_offset=0.0, c_offset=0.0,
            i_offset=0.0, j_offset=0.0, q_offset=0.0,
            u_offset=0.0, v_offset=0.0, w_offset=0.0,
            diameter=10.5, tool_table_id=table.id, remark='offset tool'
        )
        session.add(tool)
        session.commit()

        fresh = session.query(Tool).filter_by(tool_no=5).first()
        assert fresh is not None
        assert fresh.diameter == 10.5
        assert fresh.x_offset == 0.1
        assert fresh.y_offset == -0.2
        assert fresh.z_offset == 0.05

    def test_tool_belongs_to_tool_table(self, session):
        table = ToolTable(name='parent')
        tool = Tool(tool_no=1, tool_table=table)
        session.add(table)
        session.commit()

        fresh = session.query(Tool).filter_by(tool_no=1).first()
        assert fresh.tool_table is not None
        assert fresh.tool_table.name == 'parent'

    def test_tool_no_as_identifier(self, session):
        for i in range(10):
            tool = Tool(tool_no=i + 1)
            session.add(tool)
        session.commit()

        result = session.query(Tool).filter_by(tool_no=7).first()
        assert result is not None
        assert result.tool_no == 7

    def test_default_offset_values_are_none(self, session):
        tool = Tool(tool_no=1)
        session.add(tool)
        session.commit()

        fresh = session.query(Tool).filter_by(tool_no=1).first()
        assert fresh.x_offset is None
        assert fresh.y_offset is None
        assert fresh.z_offset is None
        assert fresh.diameter is None

    def test_tool_remark_can_be_none(self, session):
        tool = Tool(tool_no=1, remark=None)
        session.add(tool)
        session.commit()

        fresh = session.query(Tool).filter_by(tool_no=1).first()
        assert fresh.remark is None

    def test_tool_in_use_and_pocket(self, session):
        tool = Tool(tool_no=1, in_use=1, pocket=5)
        session.add(tool)
        session.commit()

        fresh = session.query(Tool).filter_by(tool_no=1).first()
        assert fresh.in_use == 1
        assert fresh.pocket == 5


class TestToolModelCRUD:
    def test_create_model_for_tool(self, session):
        tool = Tool(tool_no=1)
        model = ToolModel(tool_no=1, model='Makita-DF330D')
        session.add_all([tool, model])
        session.commit()

        fresh = session.query(ToolModel).filter_by(tool_no=1).first()
        assert fresh is not None
        assert fresh.model == 'Makita-DF330D'

    def test_model_references_tool_via_fk(self, session):
        tool = Tool(tool_no=42)
        model = ToolModel(tool_no=42, model='some-tool')
        session.add_all([tool, model])
        session.commit()

        fresh = session.query(ToolModel).filter_by(tool_no=42).first()
        assert fresh.tool_no == 42

    def test_model_belongs_to_tool_table(self, session):
        table = ToolTable(name='catalog')
        session.add(table)
        session.flush()

        tool = Tool(tool_no=1, tool_table_id=table.id)
        model = ToolModel(tool_no=1, model='test-model', tool_table_id=table.id)
        session.add_all([tool, model])
        session.commit()

        fresh = session.query(ToolModel).first()
        assert fresh is not None
        assert fresh.tool_table is not None
        assert fresh.tool_table.name == 'catalog'

    def test_multiple_models_for_different_tools(self, session):
        t1 = Tool(tool_no=1)
        t2 = Tool(tool_no=2)
        m1 = ToolModel(tool_no=1, model='model-a')
        m2 = ToolModel(tool_no=2, model='model-b')
        session.add_all([t1, t2, m1, m2])
        session.commit()

        models = session.query(ToolModel).all()
        assert len(models) == 2
        by_tool = {m.tool_no: m.model for m in models}
        assert by_tool[1] == 'model-a'
        assert by_tool[2] == 'model-b'


class TestRelationships:
    def test_back_populates_tools(self, session):
        table = ToolTable(name='linked')
        tool = Tool(tool_no=1, tool_table=table)
        session.add(table)
        session.commit()

        fresh = session.query(ToolTable).filter_by(name='linked').first()
        assert fresh.tools[0].tool_table is fresh

    def test_back_populates_tool_models(self, session):
        table = ToolTable(name='with_models')
        model = ToolModel(tool_no=1, model='test', tool_table=table)
        session.add(table)
        session.commit()

        fresh = session.query(ToolTable).filter_by(name='with_models').first()
        assert fresh.tool_models[0].tool_table is fresh

    def test_cascade_delete_tool_table_does_not_remove_tools(self, session):
        """No cascade='delete' configured on ToolTable.tools relationship."""
        table = ToolTable(name='cascade_test')
        tool = Tool(tool_no=1, tool_table=table)
        session.add(table)
        session.commit()

        session.delete(table)
        session.commit()

        remaining = session.query(Tool).all()
        assert len(remaining) == 1

    def test_cascade_delete_tool_table_does_not_remove_models(self, session):
        """No cascade='delete' configured on ToolTable.tool_models relationship."""
        table = ToolTable(name='cascade_models')
        model = ToolModel(tool_no=1, model='test', tool_table=table)
        session.add(table)
        session.commit()

        session.delete(table)
        session.commit()

        remaining = session.query(ToolModel).all()
        assert len(remaining) == 1


class TestEdgeCases:
    def test_duplicate_tool_no_allowed(self, session):
        """No unique constraint on tool_no — both should insert."""
        t1 = Tool(tool_no=1, remark='first')
        t2 = Tool(tool_no=1, remark='second')
        session.add_all([t1, t2])
        session.commit()

        results = session.query(Tool).filter_by(tool_no=1).all()
        assert len(results) == 2

    def test_null_remark_allowed(self, session):
        tool = Tool(tool_no=1, remark=None)
        session.add(tool)
        session.commit()

        fresh = session.query(Tool).filter_by(tool_no=1).first()
        assert fresh.remark is None

    def test_empty_string_name(self, session):
        table = ToolTable(name='')
        session.add(table)
        session.commit()

        fresh = session.query(ToolTable).filter_by(name='').first()
        assert fresh is not None
