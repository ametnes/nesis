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

const EngineOptions = [
  { label: 'S3 Compatible', value: 's3' },
  { label: 'Google Drive', value: 'gdrive' },
  { label: 'Sharepoint', value: 'sharepoint' },
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

export default function DocumentDetailsPage({ onSuccess }) {
  const match = useRouteMatch();
  const [errorMessage, setErrorMessage] = React.useState('');

  return (
    <>
      <MessageRow variant="danger">{errorMessage}</MessageRow>
      <CreateDocument onSuccess={onSuccess} onError={setErrorMessage} />
    </>
  );
}

function CreateDocument({ onSuccess, onError }) {
  return (
    <>
      <ModalTitle>Connect new document storage</ModalTitle>
      <DocumentForm
        onSuccess={onSuccess}
        onError={onError}
        submitButtonText={'Create'}
      />
    </>
  );
}

function DocumentForm({
  onSuccess,
  onError,
  submitButtonText = 'Submit',
  initialValues = {
    module: 'qanda',
    name: '',
    attributes: {
      engine: '',
      connection: {
        user: '',
        password: '',
        endpoint: '',
      },
      dataobjects: '',
    },
  },
}) {
  const history = useHistory();
  const client = useClient();
  const addToast = useAddToast();

  function handleSubmit(values, actions) {
    client
      .post(`qanda/settings`, values)
      .then(() => {
        actions.setSubmitting(false);
        actions.resetForm();
        onSuccess();
        addToast({
          title: `Document Created`,
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
              label={'Storage Engine'}
              name="attributes.engine"
              isDisabled={false}
              options={EngineOptions}
              placeholder={`Select engine`}
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
                  <td>Endpoint</td>
                  <td>
                    <TextField
                      type="text"
                      id="endpoint"
                      placeholder="Endpoint"
                      name="attributes.connection.endpoint"
                      validate={required}
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
                      name="attributes.connection.user"
                      validate={required}
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
                      name="attributes.connection.password"
                      validate={required}
                    />
                  </td>
                </tr>
                <tr>
                  <td>Data Objects</td>
                  <td>
                    <TextField
                      type="text"
                      id="dataobjects"
                      placeholder="Comma separated data objects"
                      name="attributes.dataobjects"
                      validate={required}
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
                history.push('/settings/documents');
              }}
            />
          </FormikForm>
        )}
      </Formik>
    </div>
  );
}
