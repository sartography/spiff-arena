import { render } from '@testing-library/react';
import { WidgetProps } from '@rjsf/utils';
import { vi } from 'vitest';
import AutoSelectSingleOptionWidget from './AutoSelectSingleOptionWidget';

const onlyOption = 'only option';

type WidgetOverrides = {
  disabled?: boolean;
  enumDisabled?: string[];
  multiple?: boolean;
  readonly?: boolean;
};

const widgetProps = (
  enumValues: string[],
  value: string | string[] | undefined,
  onChange: ReturnType<typeof vi.fn>,
  overrides: WidgetOverrides = {},
) =>
  ({
    disabled: overrides.disabled,
    id: 'root_choice',
    name: 'choice',
    label: 'Choice',
    multiple: overrides.multiple,
    onBlur: vi.fn(),
    onChange,
    onFocus: vi.fn(),
    options: {
      enumDisabled: overrides.enumDisabled,
      enumOptions: enumValues.map((enumValue) => ({
        label: enumValue,
        value: enumValue,
      })),
    },
    readonly: overrides.readonly,
    registry: { widgets: { SelectWidget: () => null } },
    schema: { enum: enumValues, type: 'string' },
    value,
  }) as unknown as WidgetProps;

describe('AutoSelectSingleOptionWidget', () => {
  it('selects the only option', () => {
    const onChange = vi.fn();

    render(
      <AutoSelectSingleOptionWidget
        {...widgetProps([onlyOption], undefined, onChange)}
      />,
    );

    expect(onChange).toHaveBeenCalledTimes(1);
    expect(onChange).toHaveBeenCalledWith(onlyOption);
  });

  it('selects the only option as an array for a multi-select field', () => {
    const onChange = vi.fn();

    render(
      <AutoSelectSingleOptionWidget
        {...widgetProps([onlyOption], [], onChange, { multiple: true })}
      />,
    );

    expect(onChange).toHaveBeenCalledTimes(1);
    expect(onChange).toHaveBeenCalledWith([onlyOption]);
  });

  it('does not select the only option when the field is disabled', () => {
    const onChange = vi.fn();

    render(
      <AutoSelectSingleOptionWidget
        {...widgetProps([onlyOption], undefined, onChange, {
          disabled: true,
        })}
      />,
    );

    expect(onChange).not.toHaveBeenCalled();
  });

  it('does not select the only option when the field is read-only', () => {
    const onChange = vi.fn();

    render(
      <AutoSelectSingleOptionWidget
        {...widgetProps([onlyOption], undefined, onChange, {
          readonly: true,
        })}
      />,
    );

    expect(onChange).not.toHaveBeenCalled();
  });

  it('does not select the only option when the option is disabled', () => {
    const onChange = vi.fn();

    render(
      <AutoSelectSingleOptionWidget
        {...widgetProps([onlyOption], undefined, onChange, {
          enumDisabled: [onlyOption],
        })}
      />,
    );

    expect(onChange).not.toHaveBeenCalled();
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
