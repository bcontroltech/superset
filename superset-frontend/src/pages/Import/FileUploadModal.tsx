/**
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

import { useState } from 'react';
import { t, SupersetClient } from '@superset-ui/core';
import {
  Modal,
  Upload,
  Select,
  Form,
  Input,
  Button,
  Typography,
  type UploadFile,
  type UploadChangeParam,
} from '@superset-ui/core/components';
import { Progress } from 'antd';
import { Icons } from '@superset-ui/core/components/Icons';

interface Pipeline {
  id: number;
  name: string;
}

interface FileUploadModalProps {
  show: boolean;
  onHide: () => void;
  pipelines: Pipeline[];
  addDangerToast: (msg: string) => void;
  addSuccessToast: (msg: string) => void;
}

interface FormData {
  pipeline_id: number;
  description?: string;
}

const FileUploadModal = ({
  show,
  onHide,
  pipelines,
  addDangerToast,
  addSuccessToast,
}: FileUploadModalProps) => {
  const [form] = Form.useForm<FormData>();
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [fileList, setFileList] = useState<UploadFile[]>([]);

  const handleCancel = () => {
    form.resetFields();
    setFileList([]);
    setUploading(false);
    setUploadProgress(0);
    onHide();
  };

  const handleUpload = async () => {
    try {
      const values = await form.validateFields();
      
      if (fileList.length === 0) {
        addDangerToast(t('Please select a file to upload'));
        return;
      }

      setUploading(true);
      setUploadProgress(0);

      const file = fileList[0];
      const formData = new FormData();
      formData.append('file', file.originFileObj as File);
      formData.append('pipeline_id', values.pipeline_id.toString());
      if (values.description) {
        formData.append('description', values.description);
      }

      const response = await SupersetClient.post({
        endpoint: '/api/v1/imported_files/',
        body: formData,
        parseMethod: 'json',
        headers: {
          // Remove default Content-Type to let browser set it with boundary
        },
      });

      if (response.json) {
        addSuccessToast(t('File uploaded successfully'));
        handleCancel();
      }
    } catch (error: any) {
      setUploading(false);
      setUploadProgress(0);
      
      let errorMessage = t('Failed to upload file');
      if (error.response?.status === 413) {
        errorMessage = t('File is too large. Please choose a smaller file.');
      } else if (error.response?.status === 415) {
        errorMessage = t('File type not supported. Please choose a different file.');
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      addDangerToast(errorMessage);
    }
  };

  const handleFileChange = (info: UploadChangeParam<UploadFile>) => {
    setFileList(info.fileList.slice(-1)); // Keep only the last file
  };

  const uploadProps = {
    beforeUpload: () => false, // Prevent automatic upload
    onChange: handleFileChange,
    fileList,
    maxCount: 1,
    accept: '.csv,.xlsx,.xls,.json,.txt',
  };

  return (
    <Modal
      title={t('Import File')}
      show={show}
      onHide={handleCancel}
      footer={[
        <Button key="cancel" onClick={handleCancel} disabled={uploading}>
          {t('Cancel')}
        </Button>,
        <Button
          key="upload"
          type="primary"
          onClick={handleUpload}
          loading={uploading}
        >
          {uploading ? t('Uploading...') : t('Upload')}
        </Button>,
      ]}
      width={600}
      destroyOnHidden
    >
      <Form form={form} layout="vertical" disabled={uploading}>
        <Form.Item
          name="pipeline_id"
          label={t('Pipeline')}
          rules={[{ required: true, message: t('Please select a pipeline') }]}
        >
          <Select
            placeholder={t('Select pipeline')}
            options={pipelines.map(pipeline => ({
              value: pipeline.id,
              label: pipeline.name,
            }))}
          />
        </Form.Item>

        <Form.Item
          name="description"
          label={t('Description')}
        >
          <Input.TextArea
            rows={3}
            placeholder={t('Optional description for this file')}
          />
        </Form.Item>

        <Form.Item label={t('File')}>
          <Upload.Dragger {...uploadProps}>
            <p className="ant-upload-drag-icon">
              <Icons.UploadOutlined />
            </p>
            <p className="ant-upload-text">
              {t('Click or drag file to this area to upload')}
            </p>
            <p className="ant-upload-hint">
              {t('Support for CSV, Excel, JSON, and TXT files')}
            </p>
          </Upload.Dragger>
        </Form.Item>

        {uploading && (
          <Form.Item>
            <Typography.Text type="secondary">
              {t('Uploading file...')}
            </Typography.Text>
            <Progress percent={uploadProgress} />
          </Form.Item>
        )}
      </Form>
    </Modal>
  );
};

export default FileUploadModal;