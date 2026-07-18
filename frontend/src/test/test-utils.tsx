import { render, type RenderOptions } from '@testing-library/react';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import type { ReactElement } from 'react';

function AllProviders({ children }: { children: React.ReactNode }) {
  return <BrowserRouter>{children}</BrowserRouter>;
}

interface RenderWithRouterOptions extends Omit<RenderOptions, 'wrapper'> {
  route?: string;
  initialEntries?: string[];
}

function renderWithRouter(ui: ReactElement, options?: RenderWithRouterOptions) {
  const { route, initialEntries, ...renderOptions } = options || {};

  if (route || initialEntries) {
    const entries = initialEntries || [route || '/'];
    return render(ui, {
      wrapper: ({ children }) => <MemoryRouter initialEntries={entries}>{children}</MemoryRouter>,
      ...renderOptions,
    });
  }

  return render(ui, { wrapper: AllProviders, ...renderOptions });
}

export { renderWithRouter };
export { screen, fireEvent, waitFor, act } from '@testing-library/react';
export { default as userEvent } from '@testing-library/user-event';
