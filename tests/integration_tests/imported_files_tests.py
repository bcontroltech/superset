"""Tests for imported files API endpoints."""

import json
import os
import tempfile
from unittest.mock import patch

from tests.integration_tests.base_tests import SupersetTestCase


class TestImportedFilesApi(SupersetTestCase):
    """Test imported files API endpoints."""

    def test_pipelines_list(self):
        """Test getting list of pipelines."""
        self.login(username="admin")
        response = self.get("/api/v1/pipeline/")
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data.decode("utf-8"))
        self.assertIn("result", data)
        # Should have the default pipelines we created
        self.assertGreater(len(data["result"]), 0)

    def test_file_upload_missing_file(self):
        """Test file upload without file."""
        self.login(username="admin")
        response = self.client.post(
            "/api/v1/imported_files/",
            data={"pipeline_id": 1, "description": "Test"}
        )
        self.assertEqual(response.status_code, 400)

    def test_file_upload_missing_pipeline(self):
        """Test file upload without pipeline."""
        self.login(username="admin")
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp.write(b"col1,col2\nval1,val2\n")
            tmp_path = tmp.name
        
        try:
            with open(tmp_path, "rb") as f:
                response = self.client.post(
                    "/api/v1/imported_files/",
                    data={"file": (f, "test.csv")},
                    content_type="multipart/form-data"
                )
            self.assertEqual(response.status_code, 400)
        finally:
            os.unlink(tmp_path)

    def test_imported_files_list(self):
        """Test getting list of imported files."""
        self.login(username="admin")
        response = self.get("/api/v1/imported_files/")
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data.decode("utf-8"))
        self.assertIn("result", data)