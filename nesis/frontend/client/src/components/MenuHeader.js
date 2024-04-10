import React from 'react';
import { useHistory } from 'react-router-dom';
import { PersonCircle, QuestionSquare } from 'react-bootstrap-icons';
import { useCurrentSession, useSignOut } from '../SessionContext';
import { ReactComponent as Hamburger } from '../images/Hamburger.svg';
import { ReactComponent as Logo } from '../images/Nesis.svg';
import styled from 'styled-components/macro';
import { device } from '../utils/breakpoints';
import client from '../utils/httpClient';
import { LightSquareButton } from './inputs/SquareButton';

const Main = styled.div`
  height: 45px;
  margin: 0;
  display: flex;
  justify-content: space-between;
  padding: 20px 8px;
`;

const LogoContainer = styled.div`
  display: flex;
  align-items: center;
  font-size: 18px;
  font-weight: bold;
  cursor: pointer;
  margin-left: 15px;
`;

const LogoFull = styled(Logo)`
  display: block;
  height: 105px;
  width: 105px;
  margin-right: 10px;
`;

const UserControlsRow = styled.div`
  display: flex;
  align-items: center;
  justify-content: flex-end;
  margin-right: 12px;

  & > .account-icon {
    margin-right: 8px;
  }

  & > .help-icon {
    margin-right: 8px;
  }

  @media ${device.laptop} {
    display: none;
  }
`;

const SignOutButton = styled(LightSquareButton)`
  background: linear-gradient(to right, #089fdf, #5dd375);
  min-width: auto;
  margin-left: 10px;
`;

const MobileMenuTrigger = styled.div`
  display: none;

  @media ${device.laptop} {
    display: flex;
    height: 100%;
    align-items: center;
    & > svg rect {
      fill: #089fdf;
    }
  }
`;

const HeaderToolBarIcon = styled.div`
  margin-left: 20px;
  margin-right: 20px;
`;

export default function MenuHeader({ onMobileMenuClick }) {
  const history = useHistory();
  const signOut = useSignOut(client);
  const session = useCurrentSession();
  const iconSize = 20;

  return (
    <>
      <Main>
        <MobileMenuTrigger onClick={onMobileMenuClick}>
          <Hamburger />
        </MobileMenuTrigger>
        <LogoContainer>
          <LogoFull />
        </LogoContainer>
        {session && (
          <UserControlsRow>
            <HeaderToolBarIcon>
              <a
                href="https://github.com/ametnes/nesis/blob/main/docs/README.md"
                target="_blank"
              >
                <QuestionSquare size={iconSize} className="help-icon" /> Help
              </a>
            </HeaderToolBarIcon>
            <HeaderToolBarIcon>
              <PersonCircle size={iconSize} className="account-icon" />
              {session?.email ? session?.email.split('@')[0] : ''}
            </HeaderToolBarIcon>
            <SignOutButton
              onClick={signOut}
              variant="outline-danger"
              size="sm"
              id="signOutButton"
            >
              Sign Out
            </SignOutButton>
          </UserControlsRow>
        )}
      </Main>
    </>
  );
}
