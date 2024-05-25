import React from 'react';
import {
  LightSquareButton,
  OutlinedSquareButton,
  EditOutlinedSquareButton,
} from '../../../components/inputs/SquareButton';
import styled from 'styled-components/macro';
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
import { ReactComponent as RefreshIcon } from '../../../images/RefreshIcon.svg';
import MessageRow from '../../../components/MessageRow';
import { PlusSquare } from 'react-bootstrap-icons';
import StatusIcon from '../../../components/StatusIcon';
import {
  MobileList,
  EditButton,
  DeleteButton,
} from '../../../components/layout/MobileListItem';
import MobileListItem from '../../../components/layout/MobileListItem';
import Spinner from '../../../components/Spinner';
import AttributeField from '../../../components/layout/AttributeField';
import { ReactComponent as BinIcon } from '../../../images/BinIcon.svg';
import AppDetailPage from './AppDetailPage';

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

const AppsMobileHeader = styled.span`
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

const AppsIndex = styled.div`
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

const AppsTitle = styled.span`
  font-weight: 600;
  line-height: 160%;
`;

const Page = () => {
  const [appsResponse, appsLoading, appsErrors, appsActions] =
    useApiGet('apps');

  const [rolesResponse, rolesLoading, rolesErrors, rolesActions] =
    useApiGet('roles');

  const match = useRouteMatch();
  const isNew = match.url?.endsWith('/apps/new');
  const isEdit = match.url?.endsWith('/edit');
  const history = useHistory();
  const [searchText, setSearchText] = React.useState();
  const [currentSort, setCurrentSort] = React.useState(null);

  const sortFn = getSortFunction(sortConfig, currentSort, sortByName);

  const filteredItems = React.useMemo(() => {
    const matchedData = appsResponse?.items;
    const items = filterItems(
      matchedData || [],
      {},
      (data) =>
        !searchText ||
        data.name?.toLowerCase().includes(searchText.toLocaleLowerCase()) ||
        data.description
          ?.toLowerCase()
          .includes(searchText.toLocaleLowerCase()),
    );
    items.sort(sortFn);
    return items;
  }, [appsResponse, searchText, sortFn]);

  const [paginatedApps, paging] = usePagination(filteredItems, 20);

  const addToast = useAddToast();

  const [confirmModal, showConfirmModal, setCurrentItem] = useConfirmationModal(
    async (id) => {
      await client.delete(`apps/${id}`);
      appsActions.repeat();
      addToast({
        title: `App deleted`,
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
          appsActions.repeat();
        }}
      />
      <EditModal
        visible={!!isEdit}
        roles={rolesResponse?.items}
        onSuccess={() => {
          setSearchText('');
          appsActions.repeat();
          history.replace('/settings/apps');
        }}
      />
      <div style={{ paddingTop: '3px' }}>
        <PageHeader paths={['Apps']}>
          <div style={{ display: 'flex' }}>
            <RefreshButton
              onClick={() => appsActions.repeat()}
              style={{ marginRight: 12 }}
            >
              <RefreshIcon />
              <RefreshText>Refresh</RefreshText>
            </RefreshButton>
            <ResponsiveAddButton
              onClick={() => history.push(`/settings/apps/new`)}
            >
              <PlusSquare size={20} className="mr-2" />
              New
            </ResponsiveAddButton>
          </div>
        </PageHeader>
        <SearchInput
          className="my-2"
          placeholder="Search apps"
          value={searchText}
          setValue={setSearchText}
        />
        <div>
          {/* <MessageRow variant="danger" style={{ marginTop: 6 }}>
            {AppsErrors}
          </MessageRow> */}
          <MobileList>
            {appsLoading && <Spinner />}
            {paginatedApps.map((app, index) => (
              <MobileListItem
                key={app.name}
                mainContent={
                  <AppsMobileHeader>
                    <AppsIndex>{index + 1}</AppsIndex>{' '}
                    <div>
                      <span>{app.enabled}</span>
                      <AppsTitle>{app.name}</AppsTitle>
                    </div>
                  </AppsMobileHeader>
                }
                expandContent={
                  <div>
                    <EditButton
                      onClick={() =>
                        history.push({
                          pathname: `/settings/apps/${app.id}/edit`,
                          state: app,
                        })
                      }
                    >
                      Edit
                    </EditButton>
                    <DeleteButton
                      onClick={() => {
                        setCurrentItem(app.id);
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
            columns={3}
            loading={appsLoading}
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
                  name: 'Description',
                  fieldName: 'description',
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
            {!appsLoading && (
              <tbody>
                {!paginatedApps.length && (
                  <tr>
                    <td colSpan={4}>
                      <MessageRow variant="warning" style={{ marginTop: 4 }}>
                        No apps found
                      </MessageRow>
                    </td>
                  </tr>
                )}
                {paginatedApps.map((app) => (
                  <tr key={app.id}>
                    <td>{app.name}</td>
                    <td>{app.description}</td>
                    <td>{app?.create_date}</td>
                    <td style={{ display: 'flex' }}>
                      <EditOutlinedSquareButton
                        onClick={() =>
                          history.push({
                            pathname: `/settings/apps/${app.id}/edit`,
                            state: app,
                          })
                        }
                      >
                        Edit
                      </EditOutlinedSquareButton>
                      <DeleteItemButton
                        onClick={() => {
                          setCurrentItem(app.id);
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
    history.push('/settings/apps');
  }

  return (
    <Modal isOpen={visible} onRequestClose={closeModal}>
      <AppDetailPage roles={roles} onSuccess={onSuccess} />
    </Modal>
  );
}

function EditModal({ visible, roles, onSuccess }) {
  const history = useHistory();
  const location = useLocation();

  function closeModal() {
    history.push('/settings/apps');
  }

  const [appRolesResponse, roleLoading, roleErrors, roleActions] = useApiGet(
    `apps/${location?.state?.id}/roles`,
  );

  return (
    <Modal isOpen={visible} onRequestClose={closeModal}>
      <AppDetailPage
        roles={roles}
        appRoles={appRolesResponse}
        onSuccess={onSuccess}
      />
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

export default Page;
