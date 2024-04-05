import React from 'react';

export default function FormPageWrapper({ children }) {
  return <div>{children}</div>;
}

export function InnerFormContent({ children }) {
  return (
    <div style={{ paddingBottom: '10px', borderBottom: '1px solid #cccccc' }}>
      {children}
    </div>
  );
}
