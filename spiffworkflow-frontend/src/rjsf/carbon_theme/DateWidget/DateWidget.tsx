import React, { useCallback } from 'react';
import { getTemplate, WidgetProps } from '@rjsf/utils';
import DateAndTimeService from '../../../services/DateAndTimeService';

function DateWidget(props: WidgetProps) {
  const { onChange, options, registry } = props;
  const BaseInputTemplate = getTemplate<'BaseInputTemplate'>(
    'BaseInputTemplate',
    registry,
    options,
  );
  const handleChange = useCallback(
    (value: any) => {
      // react json schema forces y-m-d format for dates
      const newValue = DateAndTimeService.dateStringToYMDFormat(value);
      onChange(newValue || undefined);
    },
    [onChange],
  );

  return <BaseInputTemplate type="date" {...props} onChange={handleChange} />;
}

export default DateWidget;
