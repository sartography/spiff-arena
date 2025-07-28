// Example custom widget implementation
// This would be stored in a JavaScript file within the extension process model

module.exports = {
  /**
   * A simple rating widget that displays stars for rating
   * This demonstrates how to create a custom widget using the extension system
   */
  default: function RatingWidget(props) {
    var id = props.id;
    var value = props.value;
    var onChange = props.onChange;
    var label = props.label;
    var required = props.required;
    var disabled = props.disabled;
    var readonly = props.readonly;
    var rawErrors = props.rawErrors;
    var React = require('react');
    var useState = React.useState;

    // MUI components
    var mui = require('@mui/material');

    // State for hover value
    var hoverState = useState(-1);
    var hover = hoverState[0];
    var setHover = hoverState[1];

    // Default to 0 if value is undefined
    var currentValue = typeof value === 'number' ? value : 0;

    // Handle value change
    var handleChange = function (_event, newValue) {
      onChange(newValue);
    };

    // Handle mouse hover
    var handleHoverChange = function (_event, newHover) {
      setHover(newHover);
    };

    // Labels for the rating values
    var labels = {
      1: 'Poor',
      2: 'Fair',
      3: 'Average',
      4: 'Good',
      5: 'Excellent',
    };

    // Check if there are validation errors
    var hasError = rawErrors && rawErrors.length > 0;

    // Create the label component
    var labelComponent = React.createElement(
      mui.Typography,
      {
        key: 'label',
        component: 'legend',
        sx: {
          fontWeight: required ? 'bold' : 'normal',
          mb: 0.5,
          color: hasError ? 'error.main' : 'text.primary',
        },
      },
      label + (required ? ' *' : ''),
    );

    // Create the rating component
    var ratingComponent = React.createElement(mui.Rating, {
      key: 'rating',
      id: id,
      name: id,
      value: currentValue,
      precision: 1,
      onChange: handleChange,
      onChangeActive: handleHoverChange,
      disabled: disabled,
      readOnly: readonly,
    });

    // Create the label display component if needed
    var labelDisplay =
      value !== null
        ? React.createElement(
            mui.Box,
            {
              key: 'label-display',
              sx: { ml: 2, minWidth: 80 },
            },
            labels[hover !== -1 ? hover : value],
          )
        : null;

    // Create the rating container
    var ratingContainer = React.createElement(
      mui.Box,
      {
        key: 'rating-container',
        sx: { display: 'flex', alignItems: 'center' },
      },
      [ratingComponent, labelDisplay].filter(Boolean),
    );

    // Create error message if needed
    var errorMessage = hasError
      ? React.createElement(
          mui.FormHelperText,
          {
            key: 'error-message',
            error: true,
          },
          rawErrors.join(', '),
        )
      : null;

    // Return the complete widget
    return React.createElement(
      mui.Box,
      { sx: { mb: 2, mt: 1 } },
      [labelComponent, ratingContainer, errorMessage].filter(Boolean),
    );
  },
};
