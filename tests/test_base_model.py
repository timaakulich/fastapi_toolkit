
from fastapi_toolkit.db.base import BaseModel


class TestBaseModel:
    def test_auto_tablename_from_class_name(self):
        class MyTable(BaseModel):
            __abstract__ = True

        assert MyTable.__tablename__ == "mytable"

    def test_custom_table_name(self):
        class CustomModel(BaseModel):
            __table_name__ = "custom_table"
            __abstract__ = True

        assert CustomModel.__tablename__ == "custom_table"
