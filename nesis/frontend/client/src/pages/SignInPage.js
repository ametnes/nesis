import React, { useContext, useState } from 'react';
import styled from 'styled-components';
import { ReactComponent as Nesis } from '../images/NesisIcon.svg';
import { Formik, Form as FormikForm } from 'formik';
import { TextField } from '../components/form';
import { required } from '../components/form/validators';
import { BsArrowRightShort } from 'react-icons/bs';
import FullPageFormContainer from '../components/layout/FullPageFormContainer';
import client from '../utils/httpClient';
import parseApiErrorMessage from '../utils/parseApiErrorMessage';
import SessionContext from '../SessionContext';
import { useHistory } from 'react-router-dom';
import { setToken } from '../utils/tokenStorage';
import MessageRow from '../components/MessageRow';

const LogoContainer = styled.div`
  margin-top: 32px;
  margin-bottom: 32px;
  cursor: pointer;
  display: flex;
  justify-content: center;
`;

const Heading1 = styled.h1`
  display: flex;
  justify-content: center;
  margin-top: 38px;
  margin-bottom: 38px;
  color: #8c52ff;
`;

const Heading2 = styled.h2`
  display: flex;
  justify-content: center;
  margin-top: 38px;
  margin-bottom: 38px;
  color: #8c52ff;
`;

const NosisLogo = styled(Nesis)`
  width: 200px;
  height: 200px;
`;

const StyledButtonWrapper = styled.div`
  & > * {
    margin-top: 42px;
    width: 100%;
  }
`;

const ActionButton = styled.button`
  width: 100%;
  background-image: linear-gradient(to right, #089fdf 21%, #5dd375 100%);
  border-radius: 0;
  border: 0;
  height: 50px;
  font-size: 14px;
  color: white;
  font-weight: 500;
  position: relative;

  & svg {
    position: absolute;
    right: 16px;
    top: 12px;
    font-size: 26px;
  }
`;

const Page = styled.div`
  height: 100%;
  overflow: auto;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
`;

const FormRow = styled.div`
  margin-top: 26px;
`;

const HTTP_STATUS_UNAUTHORIZED = 401;

const SignInPage = () => {
  const [error, setError] = useState();
  const { setSession } = useContext(SessionContext);
  const history = useHistory();

  function submit(session, actions) {
    client
      .post('sessions', session)
      .then((res) => {
        actions.setSubmitting(false);
        handleSuccess(session.email, res);
      })
      .catch((err) => {
        actions.setSubmitting(false);
        if (err?.response?.status === HTTP_STATUS_UNAUTHORIZED) {
          setError('Incorrect email or password');
        } else {
          setError(parseApiErrorMessage(err));
        }
      });
  }

  function handleSuccess(email, response) {
    setSession({
      email,
    });
    setToken(response.body.token);
    history.push('discovery/documents');
  }

  return (
    <Page>
      <FullPageFormContainer>
        <div>
          <LogoContainer>
            <NosisLogo />
          </LogoContainer>
        </div>
        <div>
          <Heading1>Nesis</Heading1>
          <Heading2>Your Enterprise Knowledge Partner</Heading2>
          <MessageRow variant="danger">{error}</MessageRow>
          <Formik
            initialValues={{
              email: '',
              password: '',
            }}
            onSubmit={submit}
          >
            {({ isSubmitting, resetForm }) => (
              <FormikForm>
                <FormRow>
                  <TextField
                    type="name"
                    id="email"
                    placeholder="enter your email"
                    name="email"
                    validate={required}
                  />
                </FormRow>
                <FormRow>
                  <TextField
                    type="password"
                    id="password"
                    placeholder="**********"
                    name="password"
                    validate={required}
                  />
                </FormRow>
                <StyledButtonWrapper>
                  <ActionButton disabled={isSubmitting} type="submit">
                    Log In
                    <BsArrowRightShort />
                  </ActionButton>
                </StyledButtonWrapper>
              </FormikForm>
            )}
          </Formik>
        </div>
      </FullPageFormContainer>
    </Page>
  );
};

export default SignInPage;
