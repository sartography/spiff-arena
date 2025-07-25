// Simple rating widget that doesn't use JSX syntax
// This is the recommended format for extension widgets

module.exports = {
  // IMPORTANT: Use a named function here, not an arrow function
  default: function SimpleRatingWidget(props) {
    // Get React from the sandbox environment
    var React = require('react');
    var useState = React.useState;

    // Extract props
    var id = props.id;
    var value = props.value;
    var onChange = props.onChange;
    var label = props.label;
    var required = props.required;

    // Import MUI components directly instead of destructuring
    // This ensures we get the actual components, not undefined
    var mui = require('@mui/material');
    var Box = mui.Box;
    var Typography = mui.Typography;
    var Rating = mui.Rating;

    // Default to 0 if value is undefined
    var currentValue = typeof value === 'number' ? value : 0;

    // Handle value change
    function handleChange(event, newValue) {
      onChange(newValue);
    }

    // Create elements individually and verify they exist
    if (!Box || !Typography || !Rating) {
      console.error('MUI components not available:', {
        Box: !!Box,
        Typography: !!Typography,
        Rating: !!Rating,
      });
      // Return a simple div if components aren't available
      return React.createElement(
        'div',
        null,
        'Error loading widget components',
      );
    }

    var labelElement = React.createElement(
      Typography,
      {
        key: 'label',
        component: 'legend',
        sx: { fontWeight: required ? 'bold' : 'normal' },
      },
      label + (required ? ' *' : ''),
    );

    var ratingElement = React.createElement(Rating, {
      key: 'rating',
      id: id,
      name: id,
      value: currentValue,
      onChange: handleChange,
    });

    return React.createElement(Box, { sx: { mb: 2, mt: 1 } }, [
      labelElement,
      ratingElement,
    ]);
  },
};
