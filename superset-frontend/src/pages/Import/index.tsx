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

import { useMemo, useState, useCallback, useEffect } from 'react';
import { t, SupersetClient } from '@superset-ui/core';
import { useListViewResource } from 'src/views/CRUD/hooks';
import { createErrorHandler } from 'src/views/CRUD/utils';
import withToasts from 'src/components/MessageToasts/withToasts';
import SubMenu, { SubMenuProps } from 'src/features/home/SubMenu';
import { DeleteModal } from '@superset-ui/core/components';
import {
  ListView,
  ListViewFilterOperator as FilterOperator,
  type ListViewProps,
  type ListViewFilters,
} from 'src/components';
import { Icons } from '@superset-ui/core/components/Icons';
import FileUploadModal from './FileUploadModal';

interface ImportedFile {
  id: number;
  filename: string;
  file_size: number;
  file_size_humanized: string;
  pipeline: {
    id: number;
    name: string;
  };
  description?: string;
  upload_date: string;
  uploader?: {
    first_name: string;
    last_name: string;
  };
}

interface Pipeline {
  id: number;
  name: string;
}

interface ImportFileListProps {
  addDangerToast: (msg: string) => void;
  addSuccessToast: (msg: string) => void;
  user: {
    userId: string | number;
    firstName: string;
    lastName: string;
  };
}

const PAGE_SIZE = 25;

function ImportFileList({
  addDangerToast,
  addSuccessToast,
  user,
}: ImportFileListProps) {
  const {
    state: {
      loading,
      resourceCount: filesCount,
      resourceCollection: files,
      bulkSelectEnabled,
    },
    hasPerm,
    fetchData,
    refreshData,
    toggleBulkSelect,
  } = useListViewResource<ImportedFile>(
    'imported_files',
    t('Imported files'),
    addDangerToast,
  );

  const [uploadModalOpen, setUploadModalOpen] = useState<boolean>(false);
  const [fileCurrentlyDeleting, setFileCurrentlyDeleting] =
    useState<ImportedFile | null>(null);
  const [pipelines, setPipelines] = useState<Pipeline[]>([]);

  // Fetch pipelines
  useEffect(() => {
    SupersetClient.get({ endpoint: '/api/v1/pipeline/' }).then(
      ({ json }) => {
        setPipelines(json.result || []);
      },
      createErrorHandler(errMsg =>
        addDangerToast(t('Failed to fetch pipelines: %s', errMsg)),
      ),
    );
  }, [addDangerToast]);

  const handleFileDelete = ({ id, filename }: ImportedFile) => {
    SupersetClient.delete({
      endpoint: `/api/v1/imported_files/${id}`,
    }).then(
      () => {
        refreshData();
        setFileCurrentlyDeleting(null);
        addSuccessToast(t('Deleted: %s', filename));
      },
      createErrorHandler(errMsg =>
        addDangerToast(
          t('There was an issue deleting %s: %s', filename, errMsg),
        ),
      ),
    );
  };

  const handleBulkFileDelete = (filesToDelete: ImportedFile[]) => {
    Promise.all(
      filesToDelete.map(file =>
        SupersetClient.delete({
          endpoint: `/api/v1/imported_files/${file.id}`,
        }),
      ),
    ).then(
      () => {
        refreshData();
        addSuccessToast(
          t('Successfully deleted %d files', filesToDelete.length),
        );
      },
      createErrorHandler(errMsg =>
        addDangerToast(
          t('There was an issue deleting the selected files: %s', errMsg),
        ),
      ),
    );
  };

  const handleFileDownload = useCallback((file: ImportedFile) => {
    const downloadUrl = `/api/v1/imported_files/${file.id}/download`;
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = file.filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }, []);

  const canCreate = hasPerm('can_write');
  const canDelete = hasPerm('can_write');

  const initialSort = [{ id: 'upload_date', desc: true }];

  const columns = useMemo(
    () => [
      {
        accessor: 'filename',
        Header: t('Filename'),
        Cell: ({ row: { original } }: any) => (
          <span>
            {original.filename}
            <Icons.DownloadOutlined
              iconSize="s"
              onClick={() => handleFileDownload(original)}
              css={{
                marginLeft: 8,
                cursor: 'pointer',
                color: '#1890ff',
                '&:hover': { color: '#40a9ff' },
              }}
              title={t('Download file')}
            />
          </span>
        ),
      },
      {
        accessor: 'pipeline_id',
        Header: t('Pipeline ID'),
        show: false, // Hidden column for filtering
      },
      {
        accessor: 'pipeline.name',
        Header: t('Pipeline'),
        Cell: ({ row: { original } }: any) => original.pipeline?.name || original.pipeline_name || '-',
      },
      {
        accessor: 'file_size_humanized',
        Header: t('Size'),
      },
      {
        accessor: 'description',
        Header: t('Description'),
        Cell: ({ row: { original } }: any) => original.description || '-',
      },
      {
        accessor: 'upload_date',
        Header: t('Upload Date'),
        Cell: ({ row: { original } }: any) =>
          new Date(original.upload_date).toLocaleString(),
      },
      {
        accessor: 'uploader',
        Header: t('Uploaded By'),
        Cell: ({ row: { original } }: any) =>
          original.uploader
            ? `${original.uploader.first_name} ${original.uploader.last_name}`
            : '-',
      },
      {
        accessor: 'actions',
        Header: t('Actions'),
        disableSortBy: true,
        Cell: ({ row: { original } }: any) => (
          <div>
            {canDelete && (
              <Icons.DeleteOutlined
                iconSize="s"
                onClick={() => setFileCurrentlyDeleting(original)}
                css={{
                  cursor: 'pointer',
                  color: '#ff4d4f',
                  '&:hover': { color: '#ff7875' },
                }}
                title={t('Delete file')}
              />
            )}
          </div>
        ),
      },
    ],
    [canDelete, handleFileDownload],
  );

  const subMenuButtons: SubMenuProps['buttons'] = [];

  if (canDelete) {
    subMenuButtons.push({
      name: t('Bulk select'),
      onClick: toggleBulkSelect,
      buttonStyle: 'secondary',
    });
  }

  if (canCreate) {
    subMenuButtons.push({
      icon: <Icons.PlusOutlined iconSize="m" />,
      name: t('Import file'),
      buttonStyle: 'primary',
      onClick: () => {
        setUploadModalOpen(true);
      },
    });
  }

  const filters: ListViewFilters = useMemo(
    () => [
      {
        Header: t('Filename'),
        key: 'search',
        id: 'filename',
        input: 'search',
        operator: FilterOperator.Contains,
      },
      {
        Header: t('Pipeline'),
        key: 'pipeline',
        id: 'pipeline_id',
        input: 'select',
        operator: FilterOperator.Equals,
        unfilteredLabel: t('All'),
        selects: pipelines.map(pipeline => ({
          value: pipeline.id,
          label: pipeline.name,
        })),
      },
    ],
    [pipelines],
  );

  const emptyState = {
    title: t('No files imported yet'),
    image: 'filter-results.svg',
    buttonAction: () => setUploadModalOpen(true),
    buttonText: t('Import file'),
    buttonIcon: <Icons.PlusOutlined iconSize="m" />,
  };

  const onModalHide = () => {
    setUploadModalOpen(false);
    refreshData();
  };

  const bulkActions: ListViewProps['bulkActions'] = canDelete
    ? [
        {
          key: 'delete',
          name: t('Delete'),
          onSelect: handleBulkFileDelete,
          type: 'danger',
        },
      ]
    : [];

  return (
    <>
      <SubMenu name={t('Import')} buttons={subMenuButtons} />
      <FileUploadModal
        show={uploadModalOpen}
        onHide={onModalHide}
        pipelines={pipelines}
        addDangerToast={addDangerToast}
        addSuccessToast={addSuccessToast}
      />
      {fileCurrentlyDeleting && (
        <DeleteModal
          description={t(
            'This action will permanently delete the file %s.',
            fileCurrentlyDeleting.filename,
          )}
          onConfirm={() => {
            if (fileCurrentlyDeleting) {
              handleFileDelete(fileCurrentlyDeleting);
            }
          }}
          onHide={() => setFileCurrentlyDeleting(null)}
          open
          title={t('Delete File?')}
        />
      )}
      <ListView<ImportedFile>
        className="imported-files-list-view"
        columns={columns}
        count={filesCount}
        data={files}
        fetchData={fetchData}
        filters={filters}
        initialSort={initialSort}
        loading={loading}
        pageSize={PAGE_SIZE}
        bulkActions={bulkActions}
        bulkSelectEnabled={bulkSelectEnabled}
        disableBulkSelect={toggleBulkSelect}
        addDangerToast={addDangerToast}
        addSuccessToast={addSuccessToast}
        emptyState={emptyState}
        refreshData={refreshData}
      />
    </>
  );
}

export default withToasts(ImportFileList);