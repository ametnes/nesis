import React, { useState } from 'react';
import styled from 'styled-components/macro';
import { ReactComponent as AttentionSign } from '../images/AttentionSign.svg';
import { ReactComponent as CloseMessageIcon } from '../images/CloseMessageIcon.svg';
import { device } from '../utils/breakpoints';

export const MessageVariant = {
  DANGER: 'danger',
  WARNING: 'warning',
  SUCCESS: 'success',
};

const backgroundByVariant = {
  [MessageVariant.DANGER]: '#D14949',
  [MessageVariant.WARNING]: '#FFE352',
  [MessageVariant.SUCCESS]: '#1EB648',
};

const colorByVariant = {
  [MessageVariant.DANGER]: '#ffffff',
  [MessageVariant.WARNING]: '#343434',
  [MessageVariant.SUCCESS]: '#ffffff',
};

const StyledAttentionSign = styled(AttentionSign)`
  margin-right: 13px;
  fill: ${(props) => colorByVariant[props.$variant]};
  flex-shrink: 0;
`;

const Container = styled.div`
  background: ${(props) => backgroundByVariant[props.$variant]};
  font-weight: 500;
  line-height: 16px;
  text-align: center;
  width: 100%;
  min-height: 37px;
  color: ${(props) => colorByVariant[props.$variant]};
  font-family: ${(props) => props.theme.mainFont};
  display: flex;
  align-items: center;
  padding: 0px 24px;
  margin-bottom: 12px;
  justify-content: space-between;

  & a {
    color: ${(props) => colorByVariant[props.$variant]};
    text-decoration: underline;
  }
`;

const MessageText = styled.div`
  display: flex;
  align-items: center;
`;

function BaseMessageRow({
  children,
  variant = MessageVariant.SUCCESS,
  onClose,
  className,
}) {
  if (!children) {
    return null;
  }
  return (
    <Container $variant={variant} className={className}>
      <MessageText>
        <StyledAttentionSign $variant={variant} />
        {children}
      </MessageText>
      {onClose && (
        <CloseButton $variant={variant} onClick={onClose} title="Close">
          <CloseMessageIcon />
        </CloseButton>
      )}
    </Container>
  );
}

export default function MessageRow({ key, children, variant, className }) {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) {
    return null;
  }
  return (
    <BaseMessageRow
      key={key}
      className={className}
      variant={variant}
      onClose={() => setDismissed(true)}
    >
      {children}
    </BaseMessageRow>
  );
}

export const CloseButton = styled.button`
  background: none;
  border: none;
  cursor: pointer;
  margin-left: 16px;
  & svg {
    stroke: ${(props) => colorByVariant[props.$variant]};
  }
`;

export const GlobalMessage = styled(BaseMessageRow)`
  height: 37px;
  margin-bottom: 0;

  @media ${device.tablet} {
    height: 85px;
  }
`;
