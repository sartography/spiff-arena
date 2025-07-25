// Minimal widget example that uses only native HTML elements
// This version avoids any issues with MUI components

module.exports = {
  // Export the widget as the default property
  default: function MinimalRatingWidget(props) {
    // Get React from the sandbox environment
    var React = require('react');

    // Extract props
    var id = props.id;
    var value = props.value || 0;
    var onChange = props.onChange;
    var label = props.label || 'Rating';

    // Handle clicking on a star
    function handleStarClick(rating) {
      return function (e) {
        e.preventDefault();
        onChange(rating);
      };
    }

    // Create stars for the rating (1-5)
    var stars = [];
    for (var i = 1; i <= 5; i++) {
      // Determine if this star should be filled based on the current value
      var filled = i <= value;

      // Create a star element
      stars.push(
        React.createElement(
          'span',
          {
            key: 'star-' + i,
            onClick: handleStarClick(i),
            style: {
              cursor: 'pointer',
              color: filled ? 'gold' : 'gray',
              fontSize: '24px',
              marginRight: '5px',
            },
          },
          '★',
        ),
      );
    }

    // Display the current value
    var valueText = React.createElement(
      'span',
      {
        style: {
          marginLeft: '10px',
          fontSize: '16px',
        },
      },
      'Value: ' + value,
    );

    // Create the label element
    var labelElement = React.createElement(
      'label',
      {
        htmlFor: id,
        style: {
          display: 'block',
          marginBottom: '5px',
          fontWeight: 'bold',
        },
      },
      label,
    );

    // Create a container for the stars and value
    var ratingContainer = React.createElement(
      'div',
      {
        style: {
          display: 'flex',
          alignItems: 'center',
        },
      },
      stars.concat(valueText),
    );

    // Return the complete widget
    return React.createElement(
      'div',
      {
        style: {
          margin: '10px 0',
          padding: '10px',
          border: '1px solid #ddd',
          borderRadius: '4px',
        },
      },
      [labelElement, ratingContainer],
    );
  },
};
