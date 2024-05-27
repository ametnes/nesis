import React from 'react';
import styled from 'styled-components';
// import styled from 'styled-components/macro';
import TextInput from '../inputs/TextInput';
// import { ReactComponent as SearchIcon } from './SearchIcon.svg';
import SearchIcon from './SearchIcon.svg';

const Main = styled.div`
  width: 100%;
  margin-bottom: 16px;
`;

export default function SearchInput({
  placeholder,
  value,
  setValue,
  className,
}) {
  return (
    <Main className={className}>
      <TextInput
        placeholder={placeholder}
        // preIcon={<SearchIcon />}
        preIcon={<img src={SearchIcon} />}
        value={value}
        onChange={(e) => setValue(e.target.value)}
      />
    </Main>
  );
}
