import { ComponentType } from 'react';
import { withTheme, FormProps } from '@rjsf/core';

import Theme from '../Theme';

const CarbonForm: ComponentType<FormProps> = withTheme(Theme);

export default CarbonForm;
