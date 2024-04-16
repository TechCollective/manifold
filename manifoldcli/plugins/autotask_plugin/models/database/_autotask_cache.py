from typing import List
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from manifoldcli.models.database.db_base import DBBase

class Autotask_Cache_Last_Sync(DBBase):
    __tablename__ = 'autotask_cache_last_sync'
    primary_key: Mapped[int] = mapped_column(primary_key=True)
    name = Column(String, unique=True, nullable=False)
    tenant_key: Mapped[int] = mapped_column(ForeignKey("autotask_tenants.primary_key"))
    last_sync = Column(DateTime)

class Autotask_Contract_Category(DBBase):
    __tablename__ = '_autotask_contract_category'
    value = Column(Integer, unique=True, nullable=False, primary_key=True, autoincrement=False)
    label = Column(String, nullable=False)
    isActive = Column(Boolean)
    tenant_key: Mapped[int] = mapped_column(ForeignKey("autotask_tenants.primary_key"))

class Autotask_RMM_Manufacturer(DBBase):
    __tablename__ = '_autotask_rmm_manufacturer'
    primary_key: Mapped[int] = mapped_column(primary_key=True)
    value = Column(Integer, unique=True, nullable=False)
    label = Column(String, unique=True, nullable=False)
    tenant_key: Mapped[int] = mapped_column(ForeignKey("autotask_tenants.primary_key"))

class Autotask_RMM_Model(DBBase):
    __tablename__ = '_autotask_rmm_model'
    primary_key: Mapped[int] = mapped_column(primary_key=True)
    value = Column(Integer, unique=True, nullable=False)
    label = Column(String, unique=True, nullable=False)
    tenant_key: Mapped[int] = mapped_column(ForeignKey("autotask_tenants.primary_key"))

# TODO Look into this. Might not need it
class Autotask_Product_Catagory(DBBase):
    __tablename__ = '_autotask_product_catagory'
    primary_key: Mapped[int] = mapped_column(primary_key=True)
    value = Column(Integer, unique=True, nullable=False)
    label = Column(String, unique=True, nullable=False)
    tenant_key: Mapped[int] = mapped_column(ForeignKey("autotask_tenants.primary_key"))

class Autotask_Products(DBBase):
    __tablename__ = '_autotask_products'
    primary_key: Mapped[int] = mapped_column(primary_key=True)
    autotask_id = Column(Integer, unique=True, nullable=False)
    manufacturer = Column(String, nullable=False)
    manufacturerProductName = Column(String)
    name = Column(String)
    sku = Column(String)
    tenant_key: Mapped[int] = mapped_column(ForeignKey("autotask_tenants.primary_key"))

class Autotask_Issues(DBBase):
    __tablename__ = '_autotask_issues'
    value = Column(Integer, unique=True, nullable=False, primary_key=True, autoincrement=False)
    label = Column(String, nullable=False)
    isActive = Column(Boolean)
    tenant_key: Mapped[int] = mapped_column(ForeignKey("autotask_tenants.primary_key"))


class Autotask_Subissues(DBBase):
    __tablename__ = '_autotask_subissues'
    value = Column(Integer, unique=True, nullable=False, primary_key=True, autoincrement=False)
    label = Column(String, nullable=False)
    isActive = Column(Boolean)
    tenant_key: Mapped[int] = mapped_column(ForeignKey("autotask_tenants.primary_key"))
    parent_value: Mapped[int] = mapped_column(ForeignKey("_autotask_issues.value"))
    parent = relationship("Autotask_Issues", foreign_keys=[parent_value])

# class Autotask_Contract_Types(DBBase):
#     __tablename__ = '_autotask_issues'
#     value = Column(Integer, unique=True, nullable=False, primary_key=True, autoincrement=False)
#     label = Column(String, nullable=False)
#     isActive = Column(Boolean)
#     tenant_key: Mapped[int] = mapped_column(ForeignKey("autotask_tenants.primary_key"))