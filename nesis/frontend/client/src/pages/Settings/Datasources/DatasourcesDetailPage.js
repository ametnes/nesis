import React from 'react';
import { useHistory, useRouteMatch, useLocation } from 'react-router-dom';
import useClient from '../../../utils/useClient';
import parseApiErrorMessage from '../../../utils/parseApiErrorMessage';
import { Formik, Form as FormikForm, FieldArray, Field } from 'formik';
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
import { func } from 'prop-types';

const TypeOptions = [
  { label: 'MinIO', value: 'minio' },
  { label: 'Windows Share', value: 'windows_share' },
  { label: 'Sharepoint', value: 'sharepoint' },
  // { label: 'Google Drive', value: 'google_drive' },
  { label: 'S3 Bucket', value: 's3' },
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
  const location = useLocation();
  return (
    <>
      <ModalTitle>
        {location?.state?.id ? `Edit` : `Create`} datasource
      </ModalTitle>
      <DataSourceForm
        datasource={location?.state}
        onSuccess={onSuccess}
        onError={onError}
        submitButtonText={location?.state?.id ? `Edit` : `Create`}
      />
    </>
  );
}

function DataSourceForm({
  datasource,
  onSuccess,
  onError,
  submitButtonText = 'Submit',
  initialValues = {
    id: datasource?.id,
    name: datasource?.name,
    type: datasource?.type,
    connection: {
      user: datasource?.connection?.user,
      client_id: datasource?.connection?.client_id,
      password: '',
      endpoint: datasource?.connection?.endpoint,
      port: datasource?.connection?.port,
      region: datasource?.connection?.region,
      dataobjects: datasource?.connection?.dataobjects,
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
          title: `Datasource created`,
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
              value="connection.type"
            />
            <FormRow>
              <Column>
                <TextField
                  type="text"
                  id="name"
                  label="Name*"
                  placeholder="Name"
                  name="name"
                  validate={required}
                  disabled={
                    initialValues?.id !== null &&
                    initialValues?.id !== undefined
                  }
                />
              </Column>
            </FormRow>
            {values?.type == 's3' && s3Connection()}
            {values?.type == 'minio' && minioConnection()}
            {values?.type == 'windows_share' && sambaConnection()}
            {values?.type == 'sharepoint' && sharepointConnection()}
            {!['s3', 'minio', 'windows_share', 'sharepoint'].includes(
              values?.type,
            ) && (
              <StyledTable>
                <thead>
                  <tr>
                    <th>Attribute</th>
                    <th>Value</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Host *</td>
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
                  <tr>
                    <td>Schedule</td>
                    <td>
                      <TextField
                        type="text"
                        id="schedule"
                        placeholder="Valid cron schedule"
                        name="schedule"
                      />
                    </td>
                  </tr>
                </tbody>
              </StyledTable>
            )}

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

function s3Connection() {
  return (
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
            />
          </td>
        </tr>
        <tr>
          <td>
            Access Key <RequiredIndicator />
          </td>
          <td>
            <TextField
              type="text"
              id="user"
              placeholder="User"
              name="connection.user"
              validate={required}
            />
          </td>
        </tr>
        <tr>
          <td>Access Secret*</td>
          <td>
            <TextField
              type="password"
              id="password"
              placeholder="password"
              name="connection.password"
              validate={required}
            />
          </td>
        </tr>
        <tr>
          <td>Region*</td>
          <td>
            <TextField
              type="text"
              id="region"
              placeholder="Region"
              name="connection.region"
              validate={required}
            />
          </td>
        </tr>
        <tr>
          <td>
            Buckets <RequiredIndicator />
          </td>
          <td>
            <TextField
              type="text"
              id="dataobjects"
              placeholder="Buckets (comma separated) e.g. bucket1/key2,bucket2/key2"
              name="connection.dataobjects"
            />
          </td>
        </tr>
        <tr>
          <td>Schedule</td>
          <td>
            <TextField
              type="text"
              id="schedule"
              placeholder="Valid cron schedule"
              name="schedule"
            />
          </td>
        </tr>
      </tbody>
    </StyledTable>
  );
}

function minioConnection() {
  return (
    <StyledTable>
      <thead>
        <tr>
          <th>Attribute</th>
          <th>Value</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>
            Host <RequiredIndicator />
          </td>
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
          <td>
            Access Key <RequiredIndicator />
          </td>
          <td>
            <TextField
              type="text"
              id="user"
              placeholder="User"
              name="connection.user"
              validate={required}
            />
          </td>
        </tr>
        <tr>
          <td>
            Access Secret <RequiredIndicator />
          </td>
          <td>
            <TextField
              type="password"
              id="password"
              placeholder="password"
              name="connection.password"
              validate={required}
            />
          </td>
        </tr>
        <tr>
          <td>
            Buckets <RequiredIndicator />
          </td>
          <td>
            <TextField
              type="text"
              id="dataobjects"
              placeholder="Buckets (comma separated) e.g. bucket1/key2,bucket2/key2"
              name="connection.dataobjects"
            />
          </td>
        </tr>
        <tr>
          <td>Schedule</td>
          <td>
            <TextField
              type="text"
              id="schedule"
              placeholder="Valid cron schedule"
              name="schedule"
            />
          </td>
        </tr>
      </tbody>
    </StyledTable>
  );
}

function sambaConnection() {
  return (
    <StyledTable>
      <thead>
        <tr>
          <th>Attribute</th>
          <th>Value</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>
            Share path <RequiredIndicator />
          </td>
          <td>
            <TextField
              type="text"
              id="host"
              placeholder="For example \\host\share"
              name="connection.endpoint"
              validate={required}
            />
          </td>
        </tr>
        <tr>
          <td>Username</td>
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
          <td>Folders</td>
          <td>
            <TextField
              type="text"
              id="dataobjects"
              placeholder="Comma separated folder names"
              name="connection.dataobjects"
            />
          </td>
        </tr>
        <tr>
          <td>Schedule</td>
          <td>
            <TextField
              type="text"
              id="schedule"
              placeholder="Valid cron schedule"
              name="schedule"
            />
          </td>
        </tr>
      </tbody>
    </StyledTable>
  );
}

function sharepointConnection() {
  return (
    <StyledTable>
      <thead>
        <tr>
          <th>Attribute</th>
          <th>Value</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>
            Site URL <RequiredIndicator />
          </td>
          <td>
            <TextField
              type="text"
              id="host"
              placeholder="For example https://zolos.sharepoint.com/"
              name="connection.endpoint"
              validate={required}
            />
          </td>
        </tr>
        <tr>
          <td>
            Client ID <RequiredIndicator />
          </td>
          <td>
            <TextField
              type="text"
              id="clientId"
              placeholder="Client ID"
              name="connection.client_id"
              validate={required}
            />
          </td>
        </tr>
        <tr>
          <td>
            Thumbprint <RequiredIndicator />
          </td>
          <td>
            <TextField
              type="password"
              id="thumbprint"
              placeholder="Thumbprint"
              name="connection.thumbprint"
              validate={required}
            />
          </td>
        </tr>
        <tr>
          <td style={{ verticalAlign: 'top' }}>
            Certificate <RequiredIndicator />
          </td>
          <td>
            <Field
              component="textarea"
              validate={required}
              id="certificate"
              label="Private key"
              placeholder="Certificate Private Key"
              rows="5"
              cols="70"
              name="connection.certificate"
            ></Field>
          </td>
        </tr>
        <tr>
          <td>Folders</td>
          <td>
            <TextField
              type="text"
              id="dataobjects"
              placeholder="Comma separated folder names"
              name="connection.dataobjects"
            />
          </td>
        </tr>
        <tr>
          <td>Schedule</td>
          <td>
            <TextField
              type="text"
              id="schedule"
              placeholder="Valid cron schedule"
              name="schedule"
            />
          </td>
        </tr>
      </tbody>
    </StyledTable>
  );
}

function RequiredIndicator() {
  return <span style={{ color: 'red' }}>*</span>;
}
