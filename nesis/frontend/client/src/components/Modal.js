import React from 'react';
import ReactModal from 'react-modal';
import styled from 'styled-components';
// import styled from 'styled-components/macro';
import CloseIcon from '../images/CloseIcon.svg';
// import { ReactComponent as CloseIcon } from '../images/CloseIcon.svg';
import { device } from '../utils/breakpoints';

try {
  ReactModal.setAppElement('#root');
} catch (e) {
  //ignored
}

const StyledCloseIcon = styled.img`
  position: absolute;
  right: 30px;
  top: 30px;
  opacity: 0.2;
  cursor: pointer;
`;

export const ModalTitle = styled.div`
  font-weight: 500;
  line-height: 160%;
  width: 100%;
  text-align: center;
`;

export const ButtonsContainer = styled.div`
  display: flex;
  justify-content: center;
  width: 100%;
  margin-top: 16px;

  & > *:not(:last-child) {
    margin-right: 8px;
  }
`;

const ModalContent = styled.div`
  height: 100%;
  width: 100%;
  padding: 40px 80px;

  @media ${device.tablet} {
    padding: 12px;
  }
`;

export default function Modal({ isOpen, onRequestClose, children }) {
  const customStyles = {
    content: {
      position: 'relative',
      top: '50%',
      left: '50%',
      right: 'auto',
      bottom: 'auto',
      marginRight: '-50%',
      transform: 'translate(-50%, -50%)',
      width: '90vw',
      borderRadius: '10px',
      maxWidth: 700,
      padding: 0,
      paddingTop: 20,
    },
    overlay: {
      background: 'rgba(0, 21, 78, 0.35)',
    },
  };
  return (
    <ReactModal
      isOpen={isOpen}
      onRequestClose={onRequestClose}
      style={customStyles}
    >
      {onRequestClose && (
        <StyledCloseIcon src={CloseIcon} onClick={onRequestClose} />
      )}
      <ModalContent>{children}</ModalContent>
    </ReactModal>
  );
}
