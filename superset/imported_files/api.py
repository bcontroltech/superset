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
"""REST API for imported files"""

import logging
import os
import uuid
from typing import Any

from flask import current_app, g, request, Response, send_file
from flask_appbuilder.api import expose, protect, safe
from flask_appbuilder.models.sqla.interface import SQLAInterface
from marshmallow import ValidationError
from werkzeug.utils import secure_filename

from superset import event_logger, security_manager
from superset.constants import MODEL_API_RW_METHOD_PERMISSION_MAP, RouteMethod
from superset.imported_files.schemas import (
    ImportedFilePostSchema,
    ImportedFileResponseSchema,
    PipelineResponseSchema,
)
from superset.models.imported_files import ImportedFile
from superset.models.pipeline import Pipeline
from superset.superset_typing import FlaskResponse
from superset.utils.decorators import statsd_gauge
from superset.views.base_api import BaseSupersetModelRestApi

logger = logging.getLogger(__name__)

# Configuration
UPLOAD_FOLDER = "/tmp/superset_imports"  # This should be configurable
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'csv', 'xlsx', 'xls', 'json', 'xml'
}


def allowed_file(filename: str) -> bool:
    """Check if the file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


class ImportedFileRestApi(BaseSupersetModelRestApi):
    """REST API for imported files"""
    
    datamodel = SQLAInterface(ImportedFile)
    
    include_route_methods = {
        RouteMethod.GET_LIST,
        RouteMethod.GET,
        RouteMethod.POST,
        RouteMethod.DELETE,
        "download",
        "upload",
    }
    
    resource_name = "imported_file"
    class_permission_name = "ImportedFile"
    method_permission_name = MODEL_API_RW_METHOD_PERMISSION_MAP
    
    list_columns = [
        "id",
        "original_filename", 
        "file_size",
        "mime_type",
        "pipeline_id",
        "pipeline_name",
        "is_active",
        "uploader_name",
        "created_on",
        "changed_on",
    ]
    
    show_columns = list_columns + ["description", "file_path"]
    
    openapi_spec_tag = "Imported Files"
    
    @expose("/upload", methods=("POST",))
    @protect()
    @statsd_gauge()
    @event_logger.log_this_with_context(
        action=lambda self, *args, **kwargs: f"{self.__class__.__name__}.upload",
        log_to_statsd=False,
    )
    def upload(self) -> FlaskResponse:
        """Upload a new file.
        ---
        post:
          summary: Upload a new file
          requestBody:
            required: true
            content:
              multipart/form-data:
                schema:
                  type: object
                  properties:
                    file:
                      type: string
                      format: binary
                    pipeline_id:
                      type: integer
                    description:
                      type: string
          responses:
            201:
              description: File uploaded successfully
              content:
                application/json:
                  schema:
                    type: object
                    properties:
                      id:
                        type: integer
                      message:
                        type: string
            400:
              $ref: '#/components/responses/400'
            401:
              $ref: '#/components/responses/401'
            413:
              description: File too large
            500:
              $ref: '#/components/responses/500'
        """
        try:
            # Check if file is present in request
            if 'file' not in request.files:
                return self.response_400(message="No file provided")
            
            file = request.files['file']
            
            # Check if file was selected
            if file.filename == '':
                return self.response_400(message="No file selected")
            
            # Validate file
            if not file or not allowed_file(file.filename):
                return self.response_400(message="File type not allowed")
            
            # Get form data
            pipeline_id = request.form.get('pipeline_id')
            description = request.form.get('description', '')
            
            if not pipeline_id:
                return self.response_400(message="Pipeline ID is required")
            
            try:
                pipeline_id = int(pipeline_id)
            except (ValueError, TypeError):
                return self.response_400(message="Invalid pipeline ID")
            
            # Check if pipeline exists
            pipeline = self.datamodel.session.query(Pipeline).filter_by(
                id=pipeline_id, is_active=True
            ).first()
            
            if not pipeline:
                return self.response_400(message="Pipeline not found or inactive")
            
            # Create upload directory if it doesn't exist
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            
            # Generate unique filename
            original_filename = secure_filename(file.filename)
            file_extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
            unique_filename = f"{uuid.uuid4().hex}.{file_extension}" if file_extension else str(uuid.uuid4().hex)
            file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
            
            # Save file
            file.save(file_path)
            file_size = os.path.getsize(file_path)
            
            # Check file size
            if file_size > MAX_FILE_SIZE:
                os.remove(file_path)  # Clean up
                return self.response_400(message="File size exceeds maximum allowed size")
            
            # Create database record
            imported_file = ImportedFile(
                filename=unique_filename,
                original_filename=original_filename,
                file_path=file_path,
                file_size=file_size,
                mime_type=file.content_type,
                pipeline_id=pipeline_id,
                description=description,
                uploaded_by_fk=g.user.id,
                is_active=True,
            )
            
            self.datamodel.add(imported_file)
            self.datamodel.session.commit()
            
            return self.response(
                201,
                id=imported_file.id,
                message="File uploaded successfully"
            )
            
        except Exception as ex:
            logger.error(f"Error uploading file: {str(ex)}", exc_info=True)
            return self.response_500(message="Internal server error")
    
    @expose("/<int:pk>/download", methods=("GET",))
    @protect()
    @safe
    @statsd_gauge()
    @event_logger.log_this_with_context(
        action=lambda self, *args, **kwargs: f"{self.__class__.__name__}.download",
        log_to_statsd=False,
    )
    def download(self, pk: int) -> FlaskResponse:
        """Download a file.
        ---
        get:
          summary: Download a file
          parameters:
          - in: path
            schema:
              type: integer
            name: pk
            description: The imported file id
          responses:
            200:
              description: File content
              content:
                application/octet-stream:
                  schema:
                    type: string
                    format: binary
            401:
              $ref: '#/components/responses/401'
            404:
              $ref: '#/components/responses/404'
            500:
              $ref: '#/components/responses/500'
        """
        try:
            imported_file = self.datamodel.get(pk)
            if not imported_file or not imported_file.is_active:
                return self.response_404()
            
            if not os.path.exists(imported_file.file_path):
                return self.response_404(message="File not found on disk")
            
            return send_file(
                imported_file.file_path,
                as_attachment=True,
                download_name=imported_file.original_filename,
                mimetype=imported_file.mime_type or 'application/octet-stream'
            )
            
        except Exception as ex:
            logger.error(f"Error downloading file: {str(ex)}", exc_info=True)
            return self.response_500(message="Internal server error")

    @expose("/<int:pk>", methods=("DELETE",))
    @protect()
    @safe
    @statsd_gauge()
    @event_logger.log_this_with_context(
        action=lambda self, *args, **kwargs: f"{self.__class__.__name__}.delete",
        log_to_statsd=False,
    )
    def delete(self, pk: int) -> Response:
        """Delete an imported file.
        ---
        delete:
          summary: Delete an imported file
          parameters:
          - in: path
            schema:
              type: integer
            name: pk
            description: The imported file id
          responses:
            200:
              description: File deleted successfully
              content:
                application/json:
                  schema:
                    type: object
                    properties:
                      message:
                        type: string
            401:
              $ref: '#/components/responses/401'
            403:
              $ref: '#/components/responses/403'
            404:
              $ref: '#/components/responses/404'
            500:
              $ref: '#/components/responses/500'
        """
        try:
            imported_file = self.datamodel.get(pk)
            if not imported_file:
                return self.response_404()
            
            # Delete file from disk
            if os.path.exists(imported_file.file_path):
                try:
                    os.remove(imported_file.file_path)
                except OSError:
                    logger.warning(f"Could not delete file from disk: {imported_file.file_path}")
            
            # Delete from database
            self.datamodel.delete(imported_file)
            self.datamodel.session.commit()
            
            return self.response(200, message="File deleted successfully")
            
        except Exception as ex:
            logger.error(f"Error deleting file: {str(ex)}", exc_info=True)
            return self.response_500(message="Internal server error")


class PipelineRestApi(BaseSupersetModelRestApi):
    """REST API for pipelines"""
    
    datamodel = SQLAInterface(Pipeline)
    
    include_route_methods = {
        RouteMethod.GET_LIST,
        RouteMethod.GET,
    }
    
    resource_name = "pipeline"
    class_permission_name = "Pipeline"
    method_permission_name = MODEL_API_RW_METHOD_PERMISSION_MAP
    
    list_columns = [
        "id",
        "name",
        "description",
        "is_active",
        "sort_order",
    ]
    
    show_columns = list_columns
    
    order_columns = ["sort_order", "name"]
    
    openapi_spec_tag = "Pipelines"