import React, { useState } from 'react';
import styled from 'styled-components';
import { NavLink } from 'react-router-dom';
import { device } from '../utils/breakpoints';
import { useSignOut } from '../SessionContext';
import { useConfig } from '../ConfigContext';
import MenuHeader from './MenuHeader';
import { GearFill, FileEarmarkPost, ArrowBarLeft } from 'react-bootstrap-icons';
import client from '../utils/httpClient';

const sideMenuWidth = 300;

const Left = styled.div`
  background: ${(props) => props.background || 'white'};
  width: ${sideMenuWidth}px;
  overflow: auto;
  transition: 0.5s;
  border-right: 1px solid #ded6ec;

  @media ${device.tablet} {
    flex-shrink: 0;
    width: ${(props) => (props.$mobileMenuOpen ? '100vw' : '0')};
    border-right: 1px solid #ded6ec;
  }
`;

const Right = styled.div`
  background: ${(props) => props.background || 'white'};
  // padding-bottom: 55px;
  width: 100%;
  height: 100%;
  box-sizing: border-box;
  -webkit-box-sizing: border-box;
  -moz-box-sizing: border-box;
  -o-box-sizing: border-box;
  overflow-x: hidden;
`;

const SideContent = styled.div`
  height: 100%;
  overflow: auto;
  // background-color: #f8f8f8;
  position: relative;
`;

const MainContent = styled.div`
  box-sizing: border-box;
  display: flex;
  height: 100%;
  overflow: hidden;
  border-top: 1px solid #ded6ec;
`;

const MainContainer = styled.div`
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
`;

function Nesis({ children, className }) {
  const [mobileModalVisible, setModalVisible] = useState(false);
  const background = 'white';

  function closeMobileMenu() {
    setModalVisible(false);
  }
  return (
    <MainContainer className={className}>
      <MenuHeader onMobileMenuClick={() => setModalVisible((prev) => !prev)} />
      <MainContent>
        <Left $mobileMenuOpen={mobileModalVisible} background={background}>
          <SideContent>
            <SideMenu onClose={closeMobileMenu} />
          </SideContent>
        </Left>
        <Right background={background}>
          <div>{children}</div>
        </Right>
      </MainContent>
    </MainContainer>
  );
}

const Menu = styled.div`
  padding: 10px;
`;

const MainMenuItem = styled(NavLink)`
  color: #525252;
  align-items: center;
  margin-top: 10px;
  padding-left: 20px;
  font-weight: 500;
  line-height: 40px;
  background-color: ${(props) => props.theme.white};
  display: ${(props) => (props.$mobileOnly ? 'none' : 'flex')};

  @media ${device.laptop} {
    display: flex;
    font-size: 13px;
  }

  &:hover {
    color: ${(props) => props.theme.black};
    text-decoration: none;
  }

  & > svg {
    margin-right: 13px;
    height: 18px;
    width: auto;
    fill: ${(props) => props.theme.primary};
    opacity: 0.23;
    flex-shrink: 0;
  }

  &.active {
    color: ${(props) => props.theme.black};
    background-color: #eee6ff;
    border-radius: 4px;
  }
`;

const MenuSeparator = styled.div`
  margin-top: 18px;
  border-bottom: 1px solid #d2d5db;
  width: 100%;
`;

const MenuTitle = styled.div`
  margin-top: 0px;
  width: 100%;
  text-align: right;
`;

function SideMenu({ onClose }) {
  const config = useConfig();
  const signOut = useSignOut(client, config);

  function closeMenu() {
    if (onClose) {
      onClose();
    }
  }

  return (
    <Menu>
      <MenuTitle>
        <ArrowBarLeft />
      </MenuTitle>
      <MainMenuItem
        to="/discovery/documents"
        activeClassName="active"
        onClick={closeMenu}
      >
        <FileEarmarkPost size={25} color="royalblue" className="mr-2" />{' '}
        Documents
      </MainMenuItem>
      <MenuSeparator />
      <MainMenuItem
        to={`/settings/datasources`}
        activeClassName="active"
        onClick={closeMenu}
        exact
      >
        <GearFill size={25} color="royalblue" className="mr-2" /> Settings
      </MainMenuItem>
      <MainMenuItem $mobileOnly as="button" onClick={signOut}>
        Sign Out
      </MainMenuItem>
    </Menu>
  );
}

export default Nesis;
