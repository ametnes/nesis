import React from 'react';
import {
  LightSquareButton,
  OutlinedSquareButton,
  EditOutlinedSquareButton,
} from '../../../components/inputs/SquareButton';
import styled from 'styled-components';
// import styled from 'styled-components/macro';
import { device } from '../../../utils/breakpoints';
import Table, { DeleteItemButton } from '../../../components/Table';
import { useHistory, useRouteMatch, useLocation } from 'react-router-dom';
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
import { PlusSquare } from 'react-bootstrap-icons';
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
import RoleDetailPage from './RoleDetailPage';

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

const DocumentsGPTPage = () => {
  const [
    DocumentsResponse,
    DocumentsLoading,
    DocumentsErrors,
    DocumentsActions,
  ] = useApiGet('roles');

  const match = useRouteMatch();
  const isNew = match.url?.endsWith('/roles/new');
  const isEdit = match.url?.endsWith('/edit');
  const history = useHistory();
  const [searchText, setSearchText] = React.useState();
  const [currentSort, setCurrentSort] = React.useState(null);

  const sortFn = getSortFunction(sortConfig, currentSort, sortByName);

  const filteredItems = React.useMemo(() => {
    const matchedData = DocumentsResponse?.items;
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
      await client.delete(`roles/${id}`);
      DocumentsActions.repeat();
      addToast({
        title: `Role deleted`,
        content: 'Operation is successful',
      });
    },
  );

  return (
    <>
      {confirmModal}
      <EditOrCreateModal
        visible={!!isNew || !!isEdit}
        onSuccess={() => {
          setSearchText('');
          DocumentsActions.repeat();
          history.replace('/settings/roles');
        }}
      />
      <div style={{ paddingTop: '3px' }}>
        <PageHeader paths={['Roles']}>
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
              onClick={() => history.push(`/settings/roles/new`)}
            >
              <PlusSquare size={20} className="mr-2" />
              New
            </ResponsiveAddButton>
          </div>
        </PageHeader>
        <SearchInput
          className="my-2"
          placeholder="Search roles"
          value={searchText}
          setValue={setSearchText}
        />
        <div>
          {/* <MessageRow variant="danger" style={{ marginTop: 6 }}>
            {DocumentsErrors}
          </MessageRow> */}
          <MobileList>
            {DocumentsLoading && <Spinner />}
            {paginatedDocuments.map((role, index) => (
              <MobileListItem
                key={role.name}
                mainContent={
                  <DocumentsMobileHeader>
                    <DocumentsIndex>{index + 1}</DocumentsIndex>{' '}
                    <div>
                      <span>
                        <StatusIcon status={role.enabled} />
                        {role.enabled ? 'ONLINE' : 'OFFLINE'}
                      </span>
                      <DocumentsTitle>{role.name}</DocumentsTitle>
                    </div>
                  </DocumentsMobileHeader>
                }
                expandContent={
                  <div>
                    <EditButton
                      onClick={() =>
                        history.push({
                          pathname: `/settings/roles/${role.id}/edit`,
                          state: role,
                        })
                      }
                    >
                      Edit
                    </EditButton>
                    <DeleteButton
                      onClick={() => {
                        setCurrentItem(role.id);
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
            columns={3}
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
                  name: 'Create Date',
                  fieldName: 'create_date',
                  sortable: true,
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
                    <td colSpan={3}>
                      <MessageRow variant="warning" style={{ marginTop: 4 }}>
                        No roles found
                      </MessageRow>
                    </td>
                  </tr>
                )}
                {paginatedDocuments.map((role) => (
                  <tr key={role.id}>
                    <td>{role.name}</td>
                    <td>{role?.create_date}</td>
                    <td style={{ display: 'flex' }}>
                      <EditOutlinedSquareButton
                        onClick={() =>
                          history.push({
                            pathname: `/settings/roles/${role.id}/edit`,
                            state: role,
                          })
                        }
                      >
                        Edit
                      </EditOutlinedSquareButton>
                      <DeleteItemButton
                        onClick={() => {
                          setCurrentItem(role.id);
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
    history.push('/settings/roles');
  }

  return (
    <Modal isOpen={visible} onRequestClose={closeModal}>
      <RoleDetailPage onSuccess={onSuccess} />
    </Modal>
  );
}

const sortByName = (r1, r2) =>
  r1.name !== null && r2.name !== null && r2.name.localeCompare(r1.name);
const sortByCreateDate = (r1, r2) =>
  r1.create_date &&
  r2.create_date &&
  r2.create_date.localeCompare(r1.create_date);

const sortConfig = {
  name: sortByName,
  create_date: sortByCreateDate,
};

export default DocumentsGPTPage;
