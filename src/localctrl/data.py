from typing import Dict, List, Optional, Type, TypeVar

from sqlalchemy import Column, Integer, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from localctrl.config import Config
from localctrl.utils import time_str

Base = declarative_base()

T = TypeVar("T", bound="KVModel")


class KVModel(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(Text, unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)

    @classmethod
    def create_table(cls, engine):
        Base.metadata.create_all(engine, tables=[cls.__table__])

    @classmethod
    def get(cls: Type[T], session: Session, key: str) -> Optional[T]:
        return session.query(cls).filter(cls.key == key).first()

    @classmethod
    def get_all(cls: Type[T], session: Session) -> List[T]:
        return session.query(cls).all()

    @classmethod
    def set(cls: Type[T], session: Session, key: str, value: str) -> T:
        instance = cls.get(session, key)
        if instance:
            instance.value = value
        else:
            instance = cls(key=key, value=value)
            session.add(instance)
        session.commit()
        return instance

    @classmethod
    def delete(cls, session: Session, key: str) -> bool:
        instance = cls.get(session, key)
        if instance:
            session.delete(instance)
            session.commit()
            return True
        return False

    @classmethod
    def clear_all(cls, session: Session) -> int:
        """删除表中所有数据并返回删除的记录数量"""
        count = session.query(cls).delete()
        session.commit()
        return count

    @classmethod
    def to_dict(cls, session: Session) -> Dict[str, str]:
        result = {}
        for item in cls.get_all(session):
            result[item.key] = item.value
        return result


class KVStorage:
    def __init__(self, table_name: str, db_url: str = Config.db_url):
        self.engine = create_engine(db_url)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

        # 动态创建表类
        self.table_class = type(
            f"KV_{table_name}", (KVModel,), {"__tablename__": table_name}
        )

        # 创建表
        self.table_class.create_table(self.engine)

    def get_session(self) -> Session:
        return self.SessionLocal()

    def get(self, key: str) -> Optional[str]:
        with self.get_session() as session:
            item = self.table_class.get(session, key)
            return item.value if item else None

    def get_all(self) -> Dict[str, str]:
        with self.get_session() as session:
            return self.table_class.to_dict(session)

    def set(self, key: str, value: str) -> None:
        with self.get_session() as session:
            self.table_class.set(session, key, value)

    def delete(self, key: str) -> bool:
        with self.get_session() as session:
            return self.table_class.delete(session, key)

    def clear(self) -> int:
        """清空表中所有数据并返回删除的记录数量"""
        with self.get_session() as session:
            return self.table_class.clear_all(session)

    def log(self, message: str, time: str = None):
        if time is None:
            time = time_str()
        self.set(time, message)
