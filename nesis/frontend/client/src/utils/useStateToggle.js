import { useState } from 'react';

export default function useStateToggle(initialState = false) {
  const [value, setValue] = useState(initialState);
  const toggle = () => setValue(!value);
  return [value, toggle];
}
