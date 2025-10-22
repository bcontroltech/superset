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
"""Schemas for imported files API"""

from marshmallow import fields, Schema
from marshmallow.validate import Length


class ImportedFilePostSchema(Schema):
    """Schema for creating imported files"""
    
    original_filename = fields.String(required=True, validate=Length(max=255))
    pipeline_id = fields.Integer(required=True)
    description = fields.String(allow_none=True)


class ImportedFileResponseSchema(Schema):
    """Schema for imported file responses"""
    
    id = fields.Integer()
    filename = fields.String()
    original_filename = fields.String()
    file_size = fields.Integer()
    mime_type = fields.String()
    pipeline_id = fields.Integer()
    pipeline_name = fields.String()
    is_active = fields.Boolean()
    description = fields.String()
    uploader_name = fields.String()
    created_on = fields.DateTime()
    changed_on = fields.DateTime()


class PipelineResponseSchema(Schema):
    """Schema for pipeline responses"""
    
    id = fields.Integer()
    name = fields.String()
    description = fields.String()
    is_active = fields.Boolean()
    sort_order = fields.Integer()