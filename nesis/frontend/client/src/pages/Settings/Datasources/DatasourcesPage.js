import React from 'react';
import {
  LightSquareButton,
  OutlinedSquareButton,
  EditOutlinedSquareButton,
} from '../../../components/inputs/SquareButton';
import styled from 'styled-components/macro';
import { device } from '../../../utils/breakpoints';
import Table, { DeleteItemButton } from '../../../components/Table';
import { useHistory, useRouteMatch } from 'react-router-dom';
import { getSortFunction } from '../../../utils/paginationUtils';
import { filterItems } from '../../../utils/filterUtils';
import { usePagination } from '../../../components/PaginationRow';
import SearchInput from '../../../components/table/SearchInput';
import Modal from '../../../components/Modal';
import ResponsiveAddButton from '../../../components/layout/ResponsiveAddButton';
import client from '../../../utils/httpClient';
import useConfirmationModal from '../../../components/useConfirmationModal';
import useApiGet from '../../../utils/useApiGet';
import { useAddToast } from '../../../ToasterContext';
import { ReactComponent as RefreshIcon } from '../../../images/RefreshIcon.svg';
import MessageRow from '../../../components/MessageRow';
import StatusIcon from '../../../components/StatusIcon';
import { PlusSquare } from 'react-bootstrap-icons';
import {
  MobileList,
  EditButton,
  DeleteButton,
  AttributesTwoColumnsContainer,
} from '../../../components/layout/MobileListItem';
import MobileListItem from '../../../components/layout/MobileListItem';
import Spinner from '../../../components/Spinner';
import AttributeField from '../../../components/layout/AttributeField';
import { ReactComponent as BinIcon } from '../../../images/BinIcon.svg';
import DatasourcesDetailPage from './DatasourcesDetailPage';

const TypeOptions = {
  minio: 'MinIO',
  windows_share: 'Windows Share',
  sharepoint: 'Sharepoint',
  google_drive: 'Google Drive',
  s3: 'S3 Bucket',
};

const ActionButton = styled(LightSquareButton)`
  width: 62px;
  height: 29px;
  min-width: 62px;
  min-height: 29px;
  padding: 0;
  display: inline;
`;

const PageHeader = styled.div`
  display: flex;
  justify-content: end;
  flex-direction: row;
  padding-bottom: 3px;
`;

const StyledTable = styled(Table)`
  & th {
    background: #f1f1f1;
    color: ${(props) => props.theme.black};
  }

  @media ${device.tablet} {
    display: none;
  }
`;

const RefreshButton = styled(OutlinedSquareButton)`
  min-width: auto;
  & > svg {
    margin-right: 4px;
    @media ${device.tablet} {
      margin-right: 0;
    }
    & > path {
      fill: #089fdf;
    }
  }
`;

const RefreshText = styled.span`
  display: inline;
  @media ${device.tablet} {
    display: none;
  }
`;

const DatasourceMobileHeader = styled.span`
  margin: 8px 0;
  display: flex;
  flex-direction: row;
  align-items: center;

  & > div {
    margin-left: 10px;
    display: flex;
    flex-direction: column;
  }
`;

const DatasourceIndex = styled.div`
  width: 26px;
  height: 26px;
  border-radius: 50%;
  font-weight: 600;
  color: ${(props) => props.theme.white};
  background: #089fdf;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
`;

const DatasourceTitle = styled.span`
  font-weight: 600;
  line-height: 160%;
`;

const Types = [
  'sql_server',
  'postgres',
  'oracle',
  'minio',
  'windows',
  'sharepoint',
];

const DatasourcesPage = () => {
  const [
    datasourcesResponse,
    datasourcesLoading,
    datasourcesErrors,
    datasourcesActions,
  ] = useApiGet('datasources');

  const match = useRouteMatch();
  const isNew = match.url?.endsWith('/datasources/new');
  const isEdit = match.url?.endsWith('/edit');
  const history = useHistory();
  const [searchText, setSearchText] = React.useState();
  const [currentSort, setCurrentSort] = React.useState(null);

  const sortFn = getSortFunction(sortConfig, currentSort, sortByName);

  const filteredItems = React.useMemo(() => {
    const matchedData = datasourcesResponse?.items;
    const items = filterItems(
      matchedData || [],
      {},
      (data) =>
        !searchText ||
        data.name?.toLowerCase().includes(searchText.toLocaleLowerCase()) ||
        data.type?.toLowerCase().includes(searchText.toLocaleLowerCase()),
    );
    items.sort(sortFn);
    return items;
  }, [datasourcesResponse, searchText, sortFn]);

  const [paginatedDatasources, paging] = usePagination(filteredItems, 20);

  const addToast = useAddToast();

  const [confirmModal, showConfirmModal, setCurrentItem] = useConfirmationModal(
    async (id) => {
      await client.delete(`datasources/${id}`);
      datasourcesActions.repeat();
      addToast({
        title: `Datasources deleted`,
        content: 'Operation is successful',
      });
    },
  );

  const [confirmIngest, showConfirmIngest, setCurrentIngestItem] =
    useConfirmationModal(async (id) => {
      await client.post('tasks', {
        parent_id: id,
        type: 'ingest_datasource',
        definition: {
          datasource: {
            id: id,
          },
        },
      });
      datasourcesActions.repeat();
      addToast({
        title: `Datasource ingestion created`,
        content: 'Operation successful',
      });
    }, 'Do you want to run start the ingestion process?');

  return (
    <>
      {confirmModal}
      {confirmIngest}
      <EditOrCreateModal
        visible={!!isNew || !!isEdit}
        onSuccess={() => {
          setSearchText('');
          datasourcesActions.repeat();
          history.replace('/settings/datasources');
        }}
      />
      <div style={{ paddingTop: '3px' }}>
        <PageHeader paths={['datasources']}>
          <div style={{ display: 'flex' }}>
            <RefreshButton
              onClick={() => datasourcesActions.repeat()}
              style={{ marginRight: 12 }}
            >
              <RefreshIcon />
              <RefreshText>Refresh</RefreshText>
            </RefreshButton>
            <ResponsiveAddButton
              onClick={() => history.push(`/settings/datasources/new`)}
            >
              <PlusSquare size={20} className="mr-2" />
              New
            </ResponsiveAddButton>
          </div>
        </PageHeader>
        <SearchInput
          className="my-2"
          placeholder="Search datasources"
          value={searchText}
          setValue={setSearchText}
        />
        <div>
          {/* <MessageRow variant="danger" style={{ marginTop: 6 }}>
            {datasourcesErrors}
          </MessageRow> */}
          <MobileList>
            {datasourcesLoading && <Spinner />}
            {paginatedDatasources.map((datasource, index) => (
              <MobileListItem
                key={datasource.name}
                mainContent={
                  <DatasourceMobileHeader>
                    <DatasourceIndex>{datasource.id}</DatasourceIndex>{' '}
                    <div>
                      <span>
                        <StatusIcon status={datasource.status} />
                        {datasource.status}
                      </span>
                      <DatasourceTitle>{datasource.name}</DatasourceTitle>
                    </div>
                  </DatasourceMobileHeader>
                }
                expandContent={
                  <div>
                    <AttributesTwoColumnsContainer>
                      <AttributeField title="Type">
                        {datasource?.connection?.type}
                      </AttributeField>
                    </AttributesTwoColumnsContainer>
                    <EditButton
                      onClick={() =>
                        history.push({
                          pathname: `/datasources/${datasource.id}`,
                          state: datasource,
                        })
                      }
                    >
                      Edit
                    </EditButton>
                    <EditButton
                      onClick={() => {
                        setCurrentIngestItem(datasource.id);
                        showConfirmIngest();
                      }}
                    >
                      Ingest
                    </EditButton>
                    <DeleteButton
                      onClick={() => {
                        setCurrentItem(datasource.name);
                        showConfirmModal();
                      }}
                    >
                      <BinIcon /> Delete
                    </DeleteButton>
                  </div>
                }
              />
            ))}
          </MobileList>
          <StyledTable
            columns={5}
            loading={datasourcesLoading}
            currentSort={currentSort}
            setCurrentSort={setCurrentSort}
            config={{
              columns: [
                {
                  name: 'Name',
                  fieldName: 'name',
                  sortable: true,
                },
                {
                  name: 'Type',
                  fieldName: 'type',
                  sortable: true,
                },
                {
                  name: 'Endpoint',
                  fieldName: 'connection.endpoint',
                  sortable: true,
                },
                {
                  name: 'Status',
                  fieldName: 'enabled',
                },
                {
                  name: 'Actions',
                  fieldName: 'actions',
                },
              ],
            }}
          >
            {!datasourcesLoading && (
              <tbody>
                {!paginatedDatasources.length && (
                  <tr>
                    <td colSpan={5}>
                      <MessageRow variant="warning" style={{ marginTop: 4 }}>
                        No settings found
                      </MessageRow>
                    </td>
                  </tr>
                )}
                {paginatedDatasources.map((datasource) => (
                  <tr key={datasource.id}>
                    <td>{datasource.name}</td>
                    <td>{TypeOptions[datasource?.type]}</td>
                    <td>
                      {datasource?.connection?.url ||
                        datasource?.connection?.endpoint ||
                        datasource?.connection?.host}
                    </td>
                    <td>
                      <StatusIcon status={datasource.status} />
                      {datasource.status}
                    </td>
                    <td style={{ display: 'flex' }}>
                      <EditOutlinedSquareButton
                        onClick={() =>
                          history.push({
                            pathname: `/settings/datasources/${datasource.id}/edit`,
                            state: datasource,
                          })
                        }
                      >
                        Edit
                      </EditOutlinedSquareButton>
                      <EditOutlinedSquareButton
                        onClick={() => {
                          setCurrentIngestItem(datasource.id);
                          showConfirmIngest();
                        }}
                      >
                        Ingest
                      </EditOutlinedSquareButton>

                      <DeleteItemButton
                        onClick={() => {
                          setCurrentItem(datasource.id);
                          showConfirmModal();
                        }}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            )}
          </StyledTable>
        </div>
        {paging}
      </div>
    </>
  );
};

function EditOrCreateModal({ visible, onSuccess }) {
  const history = useHistory();

  function closeModal() {
    history.push('/settings/datasources');
  }

  return (
    <Modal isOpen={visible} onRequestClose={closeModal}>
      <DatasourcesDetailPage onSuccess={onSuccess} />
    </Modal>
  );
}

const sortByName = (r1, r2) => r2.name.localeCompare(r1.name);
const sortByType = (r1, r2) => r2.type.localeCompare(r1.type);

const sortConfig = {
  name: sortByName,
  type: sortByType,
};

export default DatasourcesPage;
