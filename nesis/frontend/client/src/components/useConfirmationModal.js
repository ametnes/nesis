import { useState } from 'react';
import React from 'react';
import SquareButton, { DangerSquareButton } from './inputs/SquareButton';
import Modal, { ButtonsContainer, ModalTitle } from './Modal';
import parseApiErrorMessage from '../utils/parseApiErrorMessage';
import MessageRow from '../components/MessageRow';
// import styled from 'styled-components/macro';
import styled from 'styled-components';

const CancelButton = styled(SquareButton)`
  background-color: ${(props) => props.theme.primaryLight};
  color: ${(props) => props.theme.black};
`;

export default function useConfirmationModal(
  onConfirm,
  message = 'Are you sure?',
  confirmTitle = 'Confirm',
) {
  const [visible, setVisible] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [currentItem, setCurrentItem] = useState(null);

  const content = (
    <ConfirmModal
      key={currentItem || undefined}
      visible={visible}
      onClose={() => setVisible(false)}
      loading={loading}
      error={error}
      onConfirm={() => {
        setLoading(true);
        setError('');
        Promise.resolve(onConfirm(currentItem))
          .then(() => {
            setLoading(false);
            setVisible(false);
          })
          .catch((e) => {
            setLoading(false);
            setError(parseApiErrorMessage(e));
          });
      }}
      message={message}
      confirmTitle={confirmTitle}
    />
  );

  function showModal(item) {
    if (item) {
      setCurrentItem(item);
    }
    setVisible(true);
  }

  return [content, showModal, setCurrentItem];
}

function ConfirmModal({
  visible,
  onClose,
  onConfirm,
  message,
  confirmTitle,
  loading,
  error,
}) {
  return (
    <Modal isOpen={visible} onRequestClose={onClose}>
      <ModalTitle>{message}</ModalTitle>
      <MessageRow variant="danger">{error}</MessageRow>
      <ButtonsContainer>
        <DangerSquareButton
          type="button"
          onClick={onConfirm}
          disabled={loading}
        >
          {loading ? 'Loading' : confirmTitle}
        </DangerSquareButton>

        <CancelButton onClick={onClose}>Cancel</CancelButton>
      </ButtonsContainer>
    </Modal>
  );
}
