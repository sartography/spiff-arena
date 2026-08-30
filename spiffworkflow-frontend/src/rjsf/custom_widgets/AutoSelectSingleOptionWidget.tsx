import { enumOptionsIsSelected, WidgetProps } from '@rjsf/utils';
import { useEffect } from 'react';

export default function AutoSelectSingleOptionWidget(props: WidgetProps) {
  const { onChange, options, registry, value } = props;
  const { enumOptions } = options;
  const onlyValue =
    enumOptions?.length === 1 ? enumOptions[0].value : undefined;

  useEffect(() => {
    if (enumOptions?.length === 1 && !enumOptionsIsSelected(onlyValue, value)) {
      onChange(onlyValue);
    }
  }, [enumOptions, onChange, onlyValue, value]);

  const SelectWidget = registry.widgets.SelectWidget;
  return <SelectWidget {...props} />;
}
