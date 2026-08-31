import { enumOptionsIsSelected, WidgetProps } from '@rjsf/utils';
import { useEffect } from 'react';

export default function AutoSelectSingleOptionWidget(props: WidgetProps) {
  const { disabled, multiple, onChange, options, readonly, registry, value } =
    props;
  const { enumDisabled, enumOptions } = options;
  const onlyValue =
    enumOptions?.length === 1 ? enumOptions[0].value : undefined;

  useEffect(() => {
    if (
      !disabled &&
      !readonly &&
      enumOptions?.length === 1 &&
      !enumDisabled?.includes(onlyValue) &&
      !enumOptionsIsSelected(onlyValue, value)
    ) {
      onChange(multiple ? [onlyValue] : onlyValue);
    }
  }, [
    disabled,
    enumDisabled,
    enumOptions,
    multiple,
    onChange,
    onlyValue,
    readonly,
    value,
  ]);

  const SelectWidget = registry.widgets.SelectWidget;
  return <SelectWidget {...props} />;
}
