import { render } from '@testing-library/react';
import { WidgetProps } from '@rjsf/utils';
import { vi } from 'vitest';
import AutoSelectSingleOptionWidget from './AutoSelectSingleOptionWidget';

const widgetProps = (
  enumValues: string[],
  value: string | undefined,
  onChange: ReturnType<typeof vi.fn>,
) =>
  ({
    id: 'root_choice',
    name: 'choice',
    label: 'Choice',
    onBlur: vi.fn(),
    onChange,
    onFocus: vi.fn(),
    options: {
      enumOptions: enumValues.map((enumValue) => ({
        label: enumValue,
        value: enumValue,
      })),
    },
    registry: { widgets: { SelectWidget: () => null } },
    schema: { enum: enumValues, type: 'string' },
    value,
  }) as unknown as WidgetProps;

describe('AutoSelectSingleOptionWidget', () => {
  it('selects the only option', () => {
    const onChange = vi.fn();

    render(
      <AutoSelectSingleOptionWidget
        {...widgetProps(['only option'], undefined, onChange)}
      />,
    );

    expect(onChange).toHaveBeenCalledTimes(1);
    expect(onChange).toHaveBeenCalledWith('only option');
  });

  it('leaves multiple options unchanged', () => {
    const onChange = vi.fn();

    render(
      <AutoSelectSingleOptionWidget
        {...widgetProps(['first', 'second'], undefined, onChange)}
      />,
    );

    expect(onChange).not.toHaveBeenCalled();
  });

  it('replaces a value that is no longer valid after options change', () => {
    const onChange = vi.fn();
    const { rerender } = render(
      <AutoSelectSingleOptionWidget
        {...widgetProps(['first', 'second'], 'second', onChange)}
      />,
    );

    rerender(
      <AutoSelectSingleOptionWidget
        {...widgetProps(['first'], 'second', onChange)}
      />,
    );

    expect(onChange).toHaveBeenCalledTimes(1);
    expect(onChange).toHaveBeenCalledWith('first');
  });
});
