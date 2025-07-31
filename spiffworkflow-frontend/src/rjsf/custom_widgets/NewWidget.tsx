// Example custom widget implementation
// This would be stored in a JavaScript file within the extension process model
import React, { useState, useEffect } from 'react';
import { Box, Rating, Typography, FormHelperText } from '@mui/material';

interface RatingWidgetProps {
  id: string;
  value: number | null;
  onChange: (value: number | null) => void;
  label: string;
  required?: boolean;
  disabled?: boolean;
  readonly?: boolean;
  rawErrors?: string[];
}

interface RatingLabels {
  [key: number]: string;
}

export default function RatingWidgetNew(props: RatingWidgetProps): JSX.Element {
  const {
    id,
    value,
    onChange,
    label,
    required = false,
    disabled = false,
    readonly = false,
    rawErrors = [],
  } = props;

  // State for hover value
  const [hover, setHover] = useState<number>(-1);

  // State for the rating value
  const [currentValue, setCurrentValue] = useState<number | null>(
    typeof value === 'number' ? value : null,
  );

  // // Sync with external value changes from the form
  // useEffect(() => {
  //   // Only update if the external value is different from the internal state
  //   if (value !== currentValue) {
  //     setCurrentValue(typeof value === 'number' ? value : null);
  //   }
  // }, [value, currentValue]);

  // Handle value change
  const handleChange = (_event: React.SyntheticEvent, newValue: number | null) => {
    setCurrentValue(newValue);
    onChange(newValue);
  };

  // Handle mouse hover
  const handleHoverChange = (_event: React.SyntheticEvent, newHover: number) => {
    console.log("THIS OUR HOVER")
    setHover(newHover);
  };

  // Labels for the rating values
  const labels: RatingLabels = {
    1: 'Poor',
    2: 'Fair',
    3: 'Average',
    4: 'Good',
    5: 'Excellent',
  };

  // Check if there are validation errors
  const hasError = rawErrors && rawErrors.length > 0;

  return (
    <Box sx={{ mb: 2, mt: 1 }}>
      <Typography
        component="legend"
        sx={{
          fontWeight: required ? 'bold' : 'normal',
          mb: 0.5,
          color: hasError ? 'error.main' : 'text.primary',
        }}
      >
        {label}{required ? ' *' : ''}
      </Typography>

      <Box sx={{ display: 'flex', alignItems: 'center' }}>
        "THE STUFFS"
        <Rating
          id={id}
          name={id}
          value={currentValue}
          precision={1}
          onChange={handleChange}
          onChangeActive={handleHoverChange}
          disabled={disabled}
          readOnly={readonly}
        />

        {currentValue !== null && (
          <Box sx={{ ml: 2, minWidth: 80 }}>
            {labels[hover !== -1 ? hover : currentValue]}
          </Box>
        )}
      </Box>

      {hasError && (
        <FormHelperText error>
          {rawErrors.join(', ')}
        </FormHelperText>
      )}
    </Box>
  );
}
