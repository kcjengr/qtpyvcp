import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, String, Integer


@pytest.fixture()
def engine(tmp_path):
    db_path = tmp_path / 'test.db'
    e = create_engine(f'sqlite:///{db_path}', echo=False)
    yield e


@pytest.fixture()
def session(engine):
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()


class TestEngine:
    def test_engine_created(self):
        from qtpyvcp.lib.db_tool.base import engine
        assert engine is not None

    def test_engine_is_sqlite(self):
        from qtpyvcp.lib.db_tool.base import engine
        assert 'sqlite' in str(engine.url)

    def test_engine_echo_false(self):
        from qtpyvcp.lib.db_tool.base import engine
        assert engine.echo is False

    def test_engine_url_path(self, tmp_path):
        from qtpyvcp.lib.db_tool.base import engine
        assert 'db.sqlite' in str(engine.url.database)


class TestSession:
    def test_session_factory_created(self):
        from qtpyvcp.lib.db_tool.base import Session
        assert Session is not None

    def test_session_factory_produces_sessions(self):
        from qtpyvcp.lib.db_tool.base import Session
        s = Session()
        assert s is not None
        s.close()


class TestBase:
    def test_base_created(self):
        from qtpyvcp.lib.db_tool.base import Base
        assert Base is not None

    def test_base_is_declarative_base(self):
        from qtpyvcp.lib.db_tool.base import Base
        assert hasattr(Base, 'metadata')

    def test_metadata_has_table_definitions(self):
        from qtpyvcp.lib.db_tool.base import Base
        assert 'tool_table' in Base.metadata.tables
        assert 'tool' in Base.metadata.tables
        assert 'tool_model' in Base.metadata.tables

    def test_can_subclass_base(self, session):
        from qtpyvcp.lib.db_tool.base import Base

        class TestTable1(Base):
            __tablename__ = 'test_table_1'
            id = Column(Integer, primary_key=True)
            name = Column(String)

        assert 'test_table_1' in Base.metadata.tables

    def test_subclass_creates_table(self, session):
        from qtpyvcp.lib.db_tool.base import Base

        class TestTable2(Base):
            __tablename__ = 'test_table_2'
            id = Column(Integer, primary_key=True)
            name = Column(String)

        Base.metadata.create_all(session.get_bind())
        session.execute(TestTable2.__table__.insert().values(name='test'))
        result = session.query(TestTable2).first()
        assert result is not None
        assert result.name == 'test'


class TestEngineConfig:
    def test_default_engine_file(self):
        from qtpyvcp.lib.db_tool.base import engine
        assert 'db.sqlite' in str(engine.url.database)

    def test_session_bind_to_engine(self, session):
        from qtpyvcp.lib.db_tool.base import Session
        s = Session()
        assert s.get_bind() is not None
        s.close()


class TestBaseInheritance:
    def test_base_has_create_all(self):
        from qtpyvcp.lib.db_tool.base import Base
        assert hasattr(Base, 'metadata')

    def test_base_has_drop_all(self):
        from qtpyvcp.lib.db_tool.base import Base
        assert hasattr(Base.metadata, 'drop_all')
