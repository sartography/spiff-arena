// Example custom widget implementation
// This would be stored in a JavaScript file within the extension process model

module.exports = {
  /**
   * A simple rating widget that displays stars for rating
   * This demonstrates how to create a custom widget using the extension system
   */
  default: function RatingWidget(props) {
    const { id, value, onChange, label, required, disabled, readonly, rawErrors } = props;
    const React = require('react');
    const { useState } = React;
    
    // MUI components
    const { Box, Rating, Typography, FormHelperText } = require('@mui/material');
    
    // State for hover value
    const [hover, setHover] = useState(-1);
    
    // Default to 0 if value is undefined
    const currentValue = typeof value === 'number' ? value : 0;
    
    // Handle value change
    const handleChange = (event, newValue) => {
      onChange(newValue);
    };
    
    // Handle mouse hover
    const handleHoverChange = (event, newHover) => {
      setHover(newHover);
    };
    
    // Labels for the rating values
    const labels = {
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
            color: hasError ? 'error.main' : 'text.primary'
          }}
        >
          {label}{required ? ' *' : ''}
        </Typography>
        
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
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
          
          {value !== null && (
            <Box sx={{ ml: 2, minWidth: 80 }}>
              {labels[hover !== -1 ? hover : value]}
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
};