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
"""Add imported files and pipeline tables

Revision ID: a1b2c3d4e5f6
Revises: c233f5365c9e
Create Date: 2025-10-22 21:01:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "c233f5365c9e"


def upgrade():
    # Create pipelines table
    op.create_table(
        "pipelines",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        # AuditMixinNullable columns
        sa.Column("created_on", sa.DateTime(), nullable=True),
        sa.Column("changed_on", sa.DateTime(), nullable=True),
        sa.Column("created_by_fk", sa.Integer(), nullable=True),
        sa.Column("changed_by_fk", sa.Integer(), nullable=True),
        # ImportExportMixin columns
        sa.Column("uuid", sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(["created_by_fk"], ["ab_user.id"]),
        sa.ForeignKeyConstraint(["changed_by_fk"], ["ab_user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    
    # Create indexes for pipelines table
    op.create_index(op.f("ix_pipelines_is_active"), "pipelines", ["is_active"], unique=False)
    op.create_index(op.f("ix_pipelines_uuid"), "pipelines", ["uuid"], unique=False)

    # Create imported_files table
    op.create_table(
        "imported_files",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=True),
        sa.Column("pipeline_id", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("uploaded_by_fk", sa.Integer(), nullable=False),
        # AuditMixinNullable columns
        sa.Column("created_on", sa.DateTime(), nullable=True),
        sa.Column("changed_on", sa.DateTime(), nullable=True),
        sa.Column("created_by_fk", sa.Integer(), nullable=True),
        sa.Column("changed_by_fk", sa.Integer(), nullable=True),
        # ImportExportMixin columns
        sa.Column("uuid", sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(["pipeline_id"], ["pipelines.id"]),
        sa.ForeignKeyConstraint(["uploaded_by_fk"], ["ab_user.id"]),
        sa.ForeignKeyConstraint(["created_by_fk"], ["ab_user.id"]),
        sa.ForeignKeyConstraint(["changed_by_fk"], ["ab_user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    
    # Create indexes for imported_files table
    op.create_index(op.f("ix_imported_files_is_active"), "imported_files", ["is_active"], unique=False)
    op.create_index(op.f("ix_imported_files_uuid"), "imported_files", ["uuid"], unique=False)

    # Insert default pipeline data
    pipeline_table = sa.table(
        "pipelines",
        sa.column("name", sa.String),
        sa.column("description", sa.Text),
        sa.column("is_active", sa.Boolean),
        sa.column("sort_order", sa.Integer),
    )
    
    default_pipelines = [
        {"name": "Plano de Contas", "description": "Chart of accounts configuration", "is_active": True, "sort_order": 1},
        {"name": "Filiais", "description": "Branch/subsidiary configuration", "is_active": True, "sort_order": 2},
        {"name": "Empresas", "description": "Company configuration", "is_active": True, "sort_order": 3},
        {"name": "Centros de Custo", "description": "Cost center configuration", "is_active": True, "sort_order": 4},
        {"name": "Departamentos", "description": "Department configuration", "is_active": True, "sort_order": 5},
        {"name": "Regras Contábeis", "description": "Accounting rules configuration", "is_active": True, "sort_order": 6},
        {"name": "Condições de Pagamento", "description": "Payment terms configuration", "is_active": True, "sort_order": 7},
        {"name": "Períodos", "description": "Period configuration", "is_active": True, "sort_order": 8},
        {"name": "Alocação", "description": "Allocation configuration", "is_active": True, "sort_order": 9},
        {"name": "Premissas", "description": "Assumptions configuration", "is_active": True, "sort_order": 10},
        {"name": "Grupo de Colaboradores", "description": "Employee group configuration", "is_active": True, "sort_order": 11},
        {"name": "Premissas de Colaboradores", "description": "Employee assumptions configuration", "is_active": True, "sort_order": 12},
        {"name": "Pessoas", "description": "People configuration", "is_active": True, "sort_order": 13},
        {"name": "Cargos", "description": "Positions configuration", "is_active": True, "sort_order": 14},
        {"name": "Salários", "description": "Salary configuration", "is_active": True, "sort_order": 15},
        {"name": "Clientes", "description": "Customer configuration", "is_active": True, "sort_order": 16},
        {"name": "Produtos", "description": "Product configuration", "is_active": True, "sort_order": 17},
        {"name": "Alocação de Receitas", "description": "Revenue allocation configuration", "is_active": True, "sort_order": 18},
        {"name": "Impostos", "description": "Tax configuration", "is_active": True, "sort_order": 19},
        {"name": "Compras de Serviços", "description": "Service purchases configuration", "is_active": True, "sort_order": 20},
        {"name": "Pagamentos a Fornecedores", "description": "Supplier payments configuration", "is_active": True, "sort_order": 21},
    ]
    
    op.bulk_insert(pipeline_table, default_pipelines)


def downgrade():
    # Drop tables in reverse order due to foreign key constraints
    op.drop_table("imported_files")
    op.drop_table("pipelines")