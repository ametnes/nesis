import React from 'react';
import { useHistory, useRouteMatch, useLocation } from 'react-router-dom';
import useClient from '../../../utils/useClient';
import parseApiErrorMessage from '../../../utils/parseApiErrorMessage';
import { Formik, Form as FormikForm, FieldArray } from 'formik';
import { Checkbox, TextField } from '../../../components/form';
import { Field } from 'formik';
import { required } from '../../../components/form/validators';
import FormControls from '../../../components/FormControls';
import { useAddToast } from '../../../ToasterContext';
import { ModalTitle } from '../../../components/Modal';
import MessageRow from '../../../components/MessageRow';
import FormRow, { Column } from '../../../components/layout/FormRow';
import Table, { DeleteItemButton } from '../../../components/Table';
import styled from 'styled-components/macro';

const StyledTable = styled(Table)``;

export default function AppDetailsPage({ roles, appRoles, onSuccess }) {
  const match = useRouteMatch();
  const [errorMessage, setErrorMessage] = React.useState('');
  const [secret, setSecret] = React.useState('');

  return (
    <>
      {errorMessage && <MessageRow variant="danger">{errorMessage}</MessageRow>}
      {secret && (
        <div
          style={{
            display: 'inline-block',
            maxWidth: '100%',
            overflowWrap: 'break-word',
            padding: '5px',
            backgroundColor: '#33cc33',
            marginTop: '5px',
          }}
        >
          <span style={{ fontWeight: 'bold', paddingBottom: '15px' }}>
            Safely save this app secret, it will not be shown again:
          </span>{' '}
          {secret}
        </div>
      )}
      <CreateApp
        onSuccess={setSecret}
        roles={roles}
        appRoles={appRoles}
        onError={setErrorMessage}
      />
    </>
  );
}

function CreateApp({ onSuccess, roles, appRoles, onError }) {
  const location = useLocation();

  return (
    <>
      <ModalTitle>{location?.state?.id ? `Edit` : `Create`} app</ModalTitle>
      <AppForm
        app={location?.state}
        roles={roles}
        appRoles={appRoles}
        onSuccess={onSuccess}
        onError={onError}
        submitButtonText={location?.state?.id ? `Update` : `Create`}
      />
    </>
  );
}

function AppForm({
  app,
  roles,
  onSuccess,
  appRoles,
  onError,
  submitButtonText = 'Submit',
  initialValues = {
    id: app?.id,
    name: app?.name,
    roles: appRoles?.items?.map((role) => role.id),
  },
}) {
  const history = useHistory();
  const client = useClient();
  const addToast = useAddToast();
  const location = useLocation();

  function handleSubmit(values, actions) {
    client
      .post(`apps`, values)
      .then((res, err) => {
        console.log(JSON.stringify(res.body));
        values.secret = res.body.secret;
        onSuccess(res.body.secret);
        values.id = res.body.id;
        actions.setSubmitting(false);
        actions.resetForm();
        // onSuccess();
        addToast({
          title: `App Created`,
          content: 'Operation is successful',
        });
      })
      .catch((error) => {
        actions.setSubmitting(false);
        onError(parseApiErrorMessage(error));
      });
  }

  initialValues.id = location?.state?.id;
  initialValues.name = location?.state?.name;
  initialValues.description = location?.state?.description;
  initialValues.enabled = location?.state?.enabled;

  return (
    <div>
      <Formik
        initialValues={initialValues}
        onSubmit={handleSubmit}
        roles={roles}
      >
        {({ isSubmitting, resetForm, values }) => (
          <FormikForm>
            <TextField
              type="text"
              id="name"
              label="Name"
              placeholder="Name"
              name="name"
              validate={required}
              disabled={
                initialValues?.id !== null && initialValues?.id !== undefined
              }
            />
            <TextField
              type="text"
              id="description"
              label="Description"
              placeholder="Description"
              name="description"
            />
            <Checkbox id="enabled" name="enabled" label="Enabled" />
            <StyledTable>
              <thead>
                <tr>
                  <th>Role</th>
                  <th>Attached</th>
                </tr>
              </thead>
              <tbody>
                {(roles || []).map((role, index) => (
                  <tr key={role.id}>
                    <td>{role.name}</td>
                    <td>
                      <Field
                        type="checkbox"
                        name="roles"
                        value={role?.id}
                        checked={values?.roles?.includes(role?.id)}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </StyledTable>

            <FormControls
              centered
              submitTitle={submitButtonText}
              submitDisabled={isSubmitting}
              onCancel={() => {
                resetForm();
                history.push('/settings/apps');
              }}
            />
          </FormikForm>
        )}
      </Formik>
    </div>
  );
}
