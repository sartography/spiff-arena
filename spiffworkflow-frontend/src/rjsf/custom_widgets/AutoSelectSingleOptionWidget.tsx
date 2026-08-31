import { enumOptionsIsSelected, WidgetProps } from '@rjsf/utils';
import { useEffect } from 'react';

export default function AutoSelectSingleOptionWidget(props: WidgetProps) {
  const { disabled, multiple, onChange, options, readonly, registry, value } =
    props;
  const { enumDisabled, enumOptions } = options;
  const enabledEnumOptions = enumOptions?.filter(
    (enumOption) => !enumDisabled?.includes(enumOption.value),
  );
  const hasOneEnabledOption = enabledEnumOptions?.length === 1;
  const onlyValue = hasOneEnabledOption
    ? enabledEnumOptions[0].value
    : undefined;

  useEffect(() => {
    if (
      !disabled &&
      !readonly &&
      hasOneEnabledOption &&
      !enumOptionsIsSelected(onlyValue, value)
    ) {
      onChange(multiple ? [onlyValue] : onlyValue);
    }
  }, [
    disabled,
    hasOneEnabledOption,
    multiple,
    onChange,
    onlyValue,
    readonly,
    value,
  ]);

  const SelectWidget = registry.widgets.SelectWidget;
  return <SelectWidget {...props} />;
}
