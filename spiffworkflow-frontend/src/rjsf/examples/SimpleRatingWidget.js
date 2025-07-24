// Simple rating widget that doesn't use JSX syntax
// This is the recommended format for extension widgets

module.exports = {
  default: function SimpleRatingWidget(props) {
    const React = require('react');
    const { useState } = React;
    const { id, value, onChange, label, required } = props;
    
    // MUI components
    const mui = require('@mui/material');
    
    // Default to 0 if value is undefined
    const currentValue = typeof value === 'number' ? value : 0;
    
    // Handle value change
    const handleChange = function(event, newValue) {
      onChange(newValue);
    };
    
    // Create the rating component
    return React.createElement(
      mui.Box, 
      { sx: { mb: 2, mt: 1 } },
      [
        // Label
        React.createElement(
          mui.Typography,
          { 
            key: 'label',
            component: 'legend',
            sx: { fontWeight: required ? 'bold' : 'normal' }
          },
          label + (required ? ' *' : '')
        ),
        
        // Rating
        React.createElement(
          mui.Rating,
          {
            key: 'rating',
            id: id,
            name: id,
            value: currentValue,
            onChange: handleChange
          }
        )
      ]
    );
  }
};