import React, { useCallback } from 'react';
import { getTemplate, WidgetProps } from '@rjsf/utils';

function DateWidget(props: WidgetProps) {
  const { onChange, options, registry } = props;
  const BaseInputTemplate = getTemplate<'BaseInputTemplate'>(
    'BaseInputTemplate',
    registry,
    options
  );
  const handleChange = useCallback(
    (value: any) => onChange(value || undefined),
    [onChange]
  );

  return <BaseInputTemplate type="date" {...props} onChange={handleChange} />;
}

export default DateWidget;
