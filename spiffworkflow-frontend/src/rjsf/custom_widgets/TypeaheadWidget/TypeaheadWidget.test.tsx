import { render, screen } from '@testing-library/react';
import { afterEach, vi } from 'vitest';
import HttpService from '../../../services/HttpService';
import TypeaheadWidget from './TypeaheadWidget';

const item = { name: 'Richmond', state: 'VA', country: 'US' };

// Formatting a selected value should not need a live typeahead service.
afterEach(() => {
  vi.restoreAllMocks();
});

describe('TypeaheadWidget itemFormat', () => {
  it.each([
    ['{name} ({state} - {country})', 'Richmond (VA - US)'],
    ['{name}/{name}', 'Richmond/Richmond'],
    ['{{name}}', '{Richmond}'],
    ['no placeholders', JSON.stringify(item)],
    ['{'.repeat(10000), JSON.stringify(item)],
  ])('formats selected records using braced keys', (itemFormat, expected) => {
    vi.spyOn(HttpService, 'makeCallToBackend').mockImplementation(() => {});

    render(
      <TypeaheadWidget
        id="city"
        label="City"
        options={{ category: 'cities', itemFormat }}
        value={JSON.stringify(item)}
        onChange={vi.fn()}
      />,
    );

    expect(screen.getByRole('combobox')).toHaveValue(expected);
  });
});
