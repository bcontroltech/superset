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
"""A collection of ORM models for imported files"""

from typing import Optional

from flask_appbuilder import Model
from flask_appbuilder.models.decorators import renders
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from superset import security_manager
from superset.models.helpers import AuditMixinNullable, ImportExportMixin
from superset.models.pipeline import Pipeline


class ImportedFile(Model, AuditMixinNullable, ImportExportMixin):
    """
    ORM model for imported files
    """

    __tablename__ = "imported_files"

    id = Column(Integer, primary_key=True)
    
    # File information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=True)
    
    # Pipeline association
    pipeline_id = Column(
        Integer,
        ForeignKey("pipelines.id"),
        nullable=False,
    )
    pipeline = relationship(Pipeline, foreign_keys=[pipeline_id])
    
    # File status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Optional description/notes
    description = Column(Text, nullable=True)
    
    # User who uploaded the file
    uploaded_by_fk = Column(
        Integer,
        ForeignKey("ab_user.id"),
        nullable=False,
    )
    uploaded_by = relationship(
        security_manager.user_model,
        foreign_keys=[uploaded_by_fk],
    )

    def __repr__(self) -> str:
        return f"<ImportedFile {self.original_filename}>"

    @renders("file_size")
    def file_size_humanized(self) -> str:
        """Return file size in human readable format"""
        if self.file_size is None:
            return ""
        
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

    @property
    def uploader_name(self) -> str:
        """Return the name of the user who uploaded the file"""
        if self.uploaded_by:
            return str(self.uploaded_by)
        return "Unknown"

    @property
    def pipeline_name(self) -> str:
        """Return the name of the associated pipeline"""
        if self.pipeline:
            return self.pipeline.name
        return "Unknown"