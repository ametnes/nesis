import React from 'react';
import {
  LightSquareButton,
  OutlinedSquareButton,
} from '../../../components/inputs/SquareButton';
import styled from 'styled-components';
// import styled from 'styled-components/macro';
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
// import { ReactComponent as RefreshIcon } from '../../../images/RefreshIcon.svg';
import RefreshIcon from '../../../images/RefreshIcon.svg';
import MessageRow from '../../../components/MessageRow';
import StatusIcon from '../../../components/StatusIcon';
import {
  MobileList,
  EditButton,
  DeleteButton,
  AttributesTwoColumnsContainer,
} from '../../../components/layout/MobileListItem';
import MobileListItem from '../../../components/layout/MobileListItem';
import Spinner from '../../../components/Spinner';
import AttributeField from '../../../components/layout/AttributeField';
// import { ReactComponent as BinIcon } from '../../../images/BinIcon.svg';
import BinIcon from '../../../images/BinIcon.svg';
import DocumentsDetailPage from './DocumentsDetailPage';

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
  //   padding-top: 18px;
  padding-bottom: 6px;
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

const DocumentsMobileHeader = styled.span`
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

const DocumentsIndex = styled.div`
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

const DocumentsTitle = styled.span`
  font-weight: 600;
  line-height: 160%;
`;

const Engines = ['s3', 'gdrive', 'sharepoint'];

const DocumentsGPTPage = () => {
  const [
    DocumentsResponse,
    DocumentsLoading,
    DocumentsErrors,
    DocumentsActions,
  ] = useApiGet('qanda/settings');

  const match = useRouteMatch();
  const isNew = match.url?.endsWith('/documents/new');
  const history = useHistory();
  const [searchText, setSearchText] = React.useState();
  const [currentSort, setCurrentSort] = React.useState(null);

  const sortFn = getSortFunction(sortConfig, currentSort, sortByName);

  const filteredItems = React.useMemo(() => {
    const matchedData = DocumentsResponse?.items?.filter(
      (source) => Engines.indexOf(source?.attributes?.engine) != -1,
    );
    const items = filterItems(
      matchedData || [],
      {},
      (data) =>
        !searchText ||
        data.name?.toLowerCase().includes(searchText.toLocaleLowerCase()) ||
        data?.attributes?.engine
          ?.toLowerCase()
          .includes(searchText.toLocaleLowerCase()),
    );
    items.sort(sortFn);
    return items;
  }, [DocumentsResponse, searchText, sortFn]);

  const [paginatedDocuments, paging] = usePagination(filteredItems, 20);

  const addToast = useAddToast();

  const [confirmModal, showConfirmModal, setCurrentItem] = useConfirmationModal(
    async (id) => {
      await client.delete(`qanda/settings/${id}`);
      DocumentsActions.repeat();
      addToast({
        title: `Setting deleted`,
        content: 'Operation is successful',
      });
    },
  );

  return (
    <>
      {confirmModal}
      <EditOrCreateModal
        visible={!!isNew}
        onSuccess={() => {
          setSearchText('');
          DocumentsActions.repeat();
          history.replace('/settings/documents');
        }}
      />
      <div style={{ paddingTop: '3px' }}>
        <PageHeader paths={['Documents']}>
          <div style={{ display: 'flex' }}>
            <RefreshButton
              onClick={() => DocumentsActions.repeat()}
              style={{ marginRight: 12 }}
            >
              {/* <RefreshIcon /> */}
              <img src={RefreshIcon} />
              <RefreshText>Refresh</RefreshText>
            </RefreshButton>
            <ResponsiveAddButton
              onClick={() => history.push(`/settings/documents/new`)}
            >
              New Documents
            </ResponsiveAddButton>
          </div>
        </PageHeader>
        <SearchInput
          className="my-2"
          placeholder="Search settings"
          value={searchText}
          setValue={setSearchText}
        />
        <div>
          {/* <MessageRow variant="danger" style={{ marginTop: 6 }}>
            {DocumentsErrors}
          </MessageRow> */}
          <MobileList>
            {DocumentsLoading && <Spinner />}
            {paginatedDocuments.map((Documents, index) => (
              <MobileListItem
                key={Documents.name}
                mainContent={
                  <DocumentsMobileHeader>
                    <DocumentsIndex>{index + 1}</DocumentsIndex>{' '}
                    <div>
                      <span>
                        <StatusIcon status={Documents.enabled} />
                        {Documents.enabled ? 'ONLINE' : 'OFFLINE'}
                      </span>
                      <DocumentsTitle>{Documents.name}</DocumentsTitle>
                    </div>
                  </DocumentsMobileHeader>
                }
                expandContent={
                  <div>
                    <AttributesTwoColumnsContainer>
                      <AttributeField title="Engine">
                        {Documents.engine}
                      </AttributeField>
                    </AttributesTwoColumnsContainer>
                    <EditButton
                      onClick={() =>
                        history.push({
                          pathname: `/settings/documents/${Documents.id}`,
                          state: Documents,
                        })
                      }
                    >
                      Edit
                    </EditButton>
                    <DeleteButton
                      onClick={() => {
                        setCurrentItem(Documents.id);
                        showConfirmModal();
                      }}
                    >
                      {/* <BinIcon /> */}
                      <img src={BinIcon} />
                      Delete
                    </DeleteButton>
                  </div>
                }
              />
            ))}
          </MobileList>
          <StyledTable
            columns={5}
            loading={DocumentsLoading}
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
                  fieldName: 'attributes.type',
                  sortable: true,
                },
                {
                  name: 'Endpoint',
                  fieldName: 'endpoint',
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
            {!DocumentsLoading && (
              <tbody>
                {!paginatedDocuments.length && (
                  <tr>
                    <td colSpan={5}>
                      <MessageRow variant="warning" style={{ marginTop: 4 }}>
                        No setting found
                      </MessageRow>
                    </td>
                  </tr>
                )}
                {paginatedDocuments.map((Documents) => (
                  <tr key={Documents.id}>
                    <td>{Documents.name}</td>
                    <td>{Documents?.attributes?.engine}</td>
                    <td>{Documents?.attributes?.connection?.endpoint}</td>
                    <td>
                      <StatusIcon status={Documents.enabled} />
                      {Documents.enabled ? 'ONLINE' : 'OFFLINE'}
                    </td>
                    <td style={{ display: 'flex' }}>
                      <DeleteItemButton
                        onClick={() => {
                          setCurrentItem(Documents.id);
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
    history.push('/settings/documents');
  }

  return (
    <Modal isOpen={visible} onRequestClose={closeModal}>
      <DocumentsDetailPage onSuccess={onSuccess} />
    </Modal>
  );
}

const sortByName = (r1, r2) => r2.name.localeCompare(r1.name);
const sortByType = (r1, r2) => r2.type.localeCompare(r1.engine);

const sortConfig = {
  name: sortByName,
  engine: sortByType,
};

export default DocumentsGPTPage;
