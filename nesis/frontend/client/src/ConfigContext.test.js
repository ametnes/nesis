import React from 'react';
import { cleanup, fireEvent } from '@testing-library/react';

import { waitFor } from '@testing-library/dom';
import { renderWithRouter } from './utils/testUtils';
import apiClient from './utils/httpClient';

jest.mock('./utils/httpClient', () => ({
  get: jest.fn(),
}));

describe.skip('ConfigContext', () => {
  afterEach(cleanup);

  it('loads current user from api into context', async () => {
    apiClient.get.mockResolvedValue({
      body: {
        count: 1,
        results: [
          {
            account: 2333333,
            attributes: {
              verified: true,
            },
            create_date: '2020-07-06 05:16:55',
            email: 'test@test.com',
            enabled: true,
            id: 23322,
            name: 'Clive Drexler',
            root: true,
          },
        ],
      },
    });
    const { getByText } = renderWithRouter(<TestComponent />);
    const setSession = getByText('Set Session');
    fireEvent.click(setSession);
    await waitFor(() => expect(getByText('Verified:true')).toBeInTheDocument());
  });
});
