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
import UserDetailPage from './UserDetailPage';

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
  const [usersResponse, usersLoading, usersErrors, usersActions] =
    useApiGet('users');

  const [rolesResponse, rolesLoading, rolesErrors, rolesActions] =
    useApiGet('roles');

  const match = useRouteMatch();
  const isNew = match.url?.endsWith('/users/new');
  const isEdit = match.url?.endsWith('/edit');
  const history = useHistory();
  const [searchText, setSearchText] = React.useState();
  const [currentSort, setCurrentSort] = React.useState(null);

  const sortFn = getSortFunction(sortConfig, currentSort, sortByName);

  const filteredItems = React.useMemo(() => {
    const matchedData = usersResponse?.items;
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
  }, [usersResponse, searchText, sortFn]);

  const [paginatedDocuments, paging] = usePagination(filteredItems, 20);

  const addToast = useAddToast();

  const [confirmModal, showConfirmModal, setCurrentItem] = useConfirmationModal(
    async (id) => {
      await client.delete(`users/${id}`);
      usersActions.repeat();
      addToast({
        title: `Setting deleted`,
        content: 'Operation is successful',
      });
    },
  );

  return (
    <>
      {confirmModal}
      <CreateModal
        visible={!!isNew}
        roles={rolesResponse?.items}
        onSuccess={() => {
          setSearchText('');
          usersActions.repeat();
          history.replace('/settings/users');
        }}
      />
      <EditModal
        visible={!!isEdit}
        roles={rolesResponse?.items}
        onSuccess={() => {
          setSearchText('');
          usersActions.repeat();
          history.replace('/settings/users');
        }}
      />
      <div style={{ paddingTop: '3px' }}>
        <PageHeader paths={['Users']}>
          <div style={{ display: 'flex' }}>
            <RefreshButton
              onClick={() => usersActions.repeat()}
              style={{ marginRight: 12 }}
            >
              {/* <RefreshIcon /> */}
              <img src={RefreshIcon} />
              <RefreshText>Refresh</RefreshText>
            </RefreshButton>
            <ResponsiveAddButton
              onClick={() => history.push(`/settings/users/new`)}
            >
              <PlusSquare size={20} className="mr-2" />
              New
            </ResponsiveAddButton>
          </div>
        </PageHeader>
        <SearchInput
          className="my-2"
          placeholder="Search users"
          value={searchText}
          setValue={setSearchText}
        />
        <div>
          {/* <MessageRow variant="danger" style={{ marginTop: 6 }}>
            {usersErrors}
          </MessageRow> */}
          <MobileList>
            {usersLoading && <Spinner />}
            {paginatedDocuments.map((Documents, index) => (
              <MobileListItem
                key={Documents.id}
                mainContent={
                  <DocumentsMobileHeader>
                    <DocumentsIndex>{index + 1}</DocumentsIndex>{' '}
                    <div>
                      {Documents.enabled}
                      <DocumentsTitle>{Documents.name}</DocumentsTitle>
                    </div>
                  </DocumentsMobileHeader>
                }
                expandContent={
                  <div>
                    <AttributesTwoColumnsContainer>
                      <AttributeField title="Name">
                        {Documents.name}
                      </AttributeField>
                    </AttributesTwoColumnsContainer>
                    <EditButton
                      onClick={() =>
                        history.push({
                          pathname: `/settings/users/${Documents.id}`,
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
                      <img src={BinIcon} />
                      {/* <BinIcon />  */}
                      Delete
                    </DeleteButton>
                  </div>
                }
              />
            ))}
          </MobileList>
          <StyledTable
            columns={4}
            loading={usersLoading}
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
                  name: 'Email',
                  fieldName: 'email',
                  sortable: true,
                },
                {
                  name: 'Enabled',
                  fieldName: 'enabled',
                  // sortable: true,
                },
                {
                  name: 'Actions',
                  fieldName: 'actions',
                },
              ],
            }}
          >
            {!usersLoading && (
              <tbody>
                {!paginatedDocuments.length && (
                  <tr>
                    <td colSpan={4}>
                      <MessageRow variant="warning" style={{ marginTop: 4 }}>
                        No setting found
                      </MessageRow>
                    </td>
                  </tr>
                )}
                {paginatedDocuments.map((user) => (
                  <tr key={user.id}>
                    <td>{user.name}</td>
                    <td>{user.email}</td>
                    <td>{user.enabled ? 'True' : 'False'}</td>
                    <td style={{ display: 'flex', padding: '5px' }}>
                      <EditOutlinedSquareButton
                        onClick={() =>
                          history.push({
                            pathname: `/settings/users/${user.id}/edit`,
                            state: user,
                          })
                        }
                      >
                        Edit
                      </EditOutlinedSquareButton>
                      <DeleteItemButton
                        onClick={() => {
                          setCurrentItem(user.id);
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

function CreateModal({ visible, roles, onSuccess }) {
  const history = useHistory();

  function closeModal() {
    history.push('/settings/users');
  }

  return (
    <Modal isOpen={visible} onRequestClose={closeModal}>
      <UserDetailPage roles={roles} onSuccess={onSuccess} />
    </Modal>
  );
}

function EditModal({ visible, roles, onSuccess }) {
  const history = useHistory();
  const location = useLocation();

  const [userRolesResponse, roleLoading, roleErrors, roleActions] = useApiGet(
    `users/${location?.state?.id}/roles`,
  );

  function closeModal() {
    history.push('/settings/users');
  }

  return (
    <Modal isOpen={visible} onRequestClose={closeModal}>
      <UserDetailPage
        roles={roles}
        userRoles={userRolesResponse}
        onSuccess={onSuccess}
      />
    </Modal>
  );
}

const sortByName = (r1, r2) => {
  try {
    return (
      r2.name !== null && r1.name !== null && r2.name.localeCompare(r1.name)
    );
  } catch (error) {
    return false;
  }
};
const sortByEmail = (r1, r2) => {
  try {
    r2.email !== null && r1.email !== null && r2.email.localeCompare(r1.email);
  } catch (error) {
    return false;
  }
};

const sortConfig = {
  name: sortByName,
  type: sortByEmail,
};

export default DocumentsGPTPage;
