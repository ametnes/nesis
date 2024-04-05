import React from 'react';
import { useHistory, useRouteMatch, useLocation } from 'react-router-dom';
import useClient from '../../../utils/useClient';
import parseApiErrorMessage from '../../../utils/parseApiErrorMessage';
import { Formik, Form as FormikForm, FieldArray } from 'formik';
import { Select, TextField } from '../../../components/form';
import { required } from '../../../components/form/validators';
import FormControls from '../../../components/FormControls';
import { useAddToast } from '../../../ToasterContext';
import { ModalTitle } from '../../../components/Modal';
import MessageRow from '../../../components/MessageRow';
import FormRow, { Column } from '../../../components/layout/FormRow';
import Table, { DeleteItemButton } from '../../../components/Table';
import styled from 'styled-components/macro';
import { device } from '../../../utils/breakpoints';

const TypeOptions = [
  { label: 'MinIO', value: 'minio' },
  { label: 'Windows Share', value: 'windows_share' },
  { label: 'Sharepoint', value: 'sharepoint' },
  { label: 'Google Drive', value: 'google_drive' },
];

const StyledTable = styled(Table)``;

const StyledFormRow = styled(FormRow)`
  align-items: stretch;

  & > *:not(:last-child) {
    margin-right: 20px;
    flex: auto;
  }
`;

const Separator = styled.div`
  display: none;

  @media ${device.tablet} {
    display: flex;
    justify-content: center;

    & > hr {
      border: 1px solid #e4ecff;
      width: 50%;
      margin: 0;
      margin-top: 20px;
    }
  }
`;

const AddDataobjectWrapper = styled.div`
  width: 100%;
  display: flex;
  justify-content: center;
  margin-top: 21px;
`;

const AddDataobjectButton = styled.button`
  color: #089fdf;
  background: none;
  cursor: pointer;

  &:hover {
    text-decoration: underline;
  }
`;

export default function DataSourceDetailsPage({ onSuccess }) {
  const match = useRouteMatch();
  const [errorMessage, setErrorMessage] = React.useState('');

  return (
    <>
      <MessageRow variant="danger">{errorMessage}</MessageRow>
      <CreateDataSource onSuccess={onSuccess} onError={setErrorMessage} />
    </>
  );
}

function CreateDataSource({ onSuccess, onError }) {
  return (
    <>
      <ModalTitle>Connect new Datasource</ModalTitle>
      <DataSourceForm
        onSuccess={onSuccess}
        onError={onError}
        submitButtonText={'Create'}
      />
    </>
  );
}

function DataSourceForm({
  onSuccess,
  onError,
  submitButtonText = 'Submit',
  initialValues = {
    module: 'data',
    name: '',
    connection: {
      user: '',
      password: '',
      endpoint: '',
      port: '',
      database: '',
      dataobjects: '',
    },
  },
}) {
  const history = useHistory();
  const client = useClient();
  const addToast = useAddToast();

  function handleSubmit(values, actions) {
    client
      .post(`datasources`, values)
      .then(() => {
        actions.setSubmitting(false);
        actions.resetForm();
        onSuccess();
        addToast({
          title: `Dataobject created`,
          content: 'Operation is successful',
        });
      })
      .catch((error) => {
        actions.setSubmitting(false);
        onError(parseApiErrorMessage(error));
      });
  }

  return (
    <div>
      <Formik initialValues={initialValues} onSubmit={handleSubmit}>
        {({ isSubmitting, resetForm, values }) => (
          <FormikForm>
            <Select
              label={'Type'}
              name="type"
              isDisabled={false}
              options={TypeOptions}
              placeholder={`Select type`}
            />
            <FormRow>
              <Column>
                <TextField
                  type="text"
                  id="name"
                  label="Name"
                  placeholder="Name"
                  name="name"
                  validate={required}
                />
              </Column>
            </FormRow>

            <StyledTable>
              <thead>
                <tr>
                  <th>Attribute</th>
                  <th>Value</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Host</td>
                  <td>
                    <TextField
                      type="text"
                      id="host"
                      placeholder="Endpoint"
                      name="connection.endpoint"
                      validate={required}
                    />
                  </td>
                </tr>
                <tr>
                  <td>Port</td>
                  <td>
                    <TextField
                      type="text"
                      id="port"
                      placeholder="Port"
                      name="connection.port"
                    />
                  </td>
                </tr>
                <tr>
                  <td>Database</td>
                  <td>
                    <TextField
                      type="text"
                      id="database"
                      placeholder="Database"
                      name="connection.database"
                    />
                  </td>
                </tr>
                <tr>
                  <td>User</td>
                  <td>
                    <TextField
                      type="text"
                      id="user"
                      placeholder="User"
                      name="connection.user"
                    />
                  </td>
                </tr>
                <tr>
                  <td>Password</td>
                  <td>
                    <TextField
                      type="password"
                      id="password"
                      placeholder="password"
                      name="connection.password"
                    />
                  </td>
                </tr>
                <tr>
                  <td>Dataobjects</td>
                  <td>
                    <TextField
                      type="text"
                      id="dataobjects"
                      placeholder="Dataobjects (comma separated)"
                      name="connection.dataobjects"
                    />
                  </td>
                </tr>
              </tbody>
            </StyledTable>

            <FormControls
              centered
              submitTitle={submitButtonText}
              submitDisabled={isSubmitting}
              onCancel={() => {
                resetForm();
                history.push('/settings/datasources');
              }}
            />
          </FormikForm>
        )}
      </Formik>
    </div>
  );
}
