# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
"""A collection of ORM models for pipeline configurations"""

from flask_appbuilder import Model
from sqlalchemy import Boolean, Column, Integer, String, Text

from superset.models.helpers import AuditMixinNullable, ImportExportMixin


class Pipeline(Model, AuditMixinNullable, ImportExportMixin):
    """
    ORM model for pipeline configurations
    """

    __tablename__ = "pipelines"

    id = Column(Integer, primary_key=True)
    
    # Pipeline information
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # Pipeline status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Display order for UI
    sort_order = Column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<Pipeline {self.name}>"

    @classmethod
    def get_default_pipelines(cls) -> list[dict[str, any]]:
        """Return the default pipeline configurations to be pre-loaded"""
        return [
            {"name": "Plano de Contas", "description": "Chart of accounts configuration", "sort_order": 1},
            {"name": "Filiais", "description": "Branch/subsidiary configuration", "sort_order": 2},
            {"name": "Empresas", "description": "Company configuration", "sort_order": 3},
            {"name": "Centros de Custo", "description": "Cost center configuration", "sort_order": 4},
            {"name": "Departamentos", "description": "Department configuration", "sort_order": 5},
            {"name": "Regras Contábeis", "description": "Accounting rules configuration", "sort_order": 6},
            {"name": "Condições de Pagamento", "description": "Payment terms configuration", "sort_order": 7},
            {"name": "Períodos", "description": "Period configuration", "sort_order": 8},
            {"name": "Alocação", "description": "Allocation configuration", "sort_order": 9},
            {"name": "Premissas", "description": "Assumptions configuration", "sort_order": 10},
            {"name": "Grupo de Colaboradores", "description": "Employee group configuration", "sort_order": 11},
            {"name": "Premissas de Colaboradores", "description": "Employee assumptions configuration", "sort_order": 12},
            {"name": "Pessoas", "description": "People configuration", "sort_order": 13},
            {"name": "Cargos", "description": "Positions configuration", "sort_order": 14},
            {"name": "Salários", "description": "Salary configuration", "sort_order": 15},
            {"name": "Clientes", "description": "Customer configuration", "sort_order": 16},
            {"name": "Produtos", "description": "Product configuration", "sort_order": 17},
            {"name": "Alocação de Receitas", "description": "Revenue allocation configuration", "sort_order": 18},
            {"name": "Impostos", "description": "Tax configuration", "sort_order": 19},
            {"name": "Compras de Serviços", "description": "Service purchases configuration", "sort_order": 20},
            {"name": "Pagamentos a Fornecedores", "description": "Supplier payments configuration", "sort_order": 21},
        ]