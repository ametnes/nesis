import React from 'react';
import { useHistory, useRouteMatch, useLocation } from 'react-router-dom';
import useClient from '../../../utils/useClient';
import parseApiErrorMessage from '../../../utils/parseApiErrorMessage';
import { Formik, Form as FormikForm, FieldArray } from 'formik';
import { Checkbox, TextField } from '../../../components/form';
import { required } from '../../../components/form/validators';
import FormControls from '../../../components/FormControls';
import { useAddToast } from '../../../ToasterContext';
import { ModalTitle } from '../../../components/Modal';
import MessageRow from '../../../components/MessageRow';
import FormRow, { Column } from '../../../components/layout/FormRow';
import Table, { DeleteItemButton } from '../../../components/Table';
import styled from 'styled-components/macro';
import { device } from '../../../utils/breakpoints';
import { Field } from 'formik';

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

export default function DocumentDetailsPage({ roles, userRoles, onSuccess }) {
  const match = useRouteMatch();
  const [errorMessage, setErrorMessage] = React.useState('');

  return (
    <>
      <MessageRow variant="danger">{errorMessage}</MessageRow>
      <CreateDocument
        roles={roles}
        userRoles={userRoles}
        onSuccess={onSuccess}
        onError={setErrorMessage}
      />
    </>
  );
}

function CreateDocument({ roles, userRoles, onSuccess, onError }) {
  return (
    <>
      <ModalTitle>{userRoles ? `Edit` : `New`} user</ModalTitle>
      <DocumentForm
        roles={roles}
        userRoles={userRoles}
        onSuccess={onSuccess}
        onError={onError}
        submitButtonText={userRoles ? `Update` : `Create`}
      />
    </>
  );
}

function DocumentForm({
  roles,
  userRoles,
  onSuccess,
  onError,
  submitButtonText = 'Submit',
  initialValues = {
    id: '',
    name: '',
    email: '',
    password: '',
    roles: userRoles?.items?.map((role) => role.id),
  },
}) {
  const history = useHistory();
  const client = useClient();
  const addToast = useAddToast();
  const location = useLocation();

  function handleSubmit(values, actions) {
    console.log(values);
    client
      .post(`users`, values)
      .then(() => {
        actions.setSubmitting(false);
        actions.resetForm();
        onSuccess();
        addToast({
          title: `User Created`,
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
  initialValues.email = location?.state?.email;
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
            <TextField type="hidden" id="id" name="id" />
            <TextField
              type="text"
              id="name"
              placeholder="Full name"
              name="name"
              validate={required}
            />
            <TextField
              type="text"
              id="email"
              placeholder="Email"
              name="email"
              validate={required}
            />
            <TextField
              type="password"
              id="password"
              placeholder="Password"
              name="password"
              validate={values.roles ? null : required}
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
                history.push('/settings/users');
              }}
            />
          </FormikForm>
        )}
      </Formik>
    </div>
  );
}
