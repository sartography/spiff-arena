// Example custom Autocomplete widget implementation
// This would be stored in a JavaScript file within the extension process model

module.exports = {
  /**
   * An autocomplete widget that fetches data from a specified API endpoint
   * This demonstrates more complex widget behavior with data fetching
   */
  default: function AutocompleteWidget(props) {
    var id = props.id;
    var value = props.value;
    var onChange = props.onChange;
    var label = props.label;
    var required = props.required;
    var disabled = props.disabled;
    var readonly = props.readonly;
    var rawErrors = props.rawErrors;
    var options = props.options;
    var React = require('react');
    var useState = React.useState;
    var useEffect = React.useEffect;
    var useRef = React.useRef;

    // MUI components
    var mui = require('@mui/material');

    // State for options, loading state, and input value
    var inputValueState = useState('');
    var inputValue = inputValueState[0];
    var setInputValue = inputValueState[1];
    var suggestionsState = useState([]);
    var suggestions = suggestionsState[0];
    var setSuggestions = suggestionsState[1];
    var loadingState = useState(false);
    var loading = loadingState[0];
    var setLoading = loadingState[1];
    var selectedOptionState = useState(null);
    var selectedOption = selectedOptionState[0];
    var setSelectedOption = selectedOptionState[1];
    var timeoutRef = useRef(null);

    // Configuration options with defaults
    var config = {
      minSearchLength: (options && options.minSearchLength) || 2,
      debounceMs: (options && options.debounceMs) || 300,
      labelField: (options && options.labelField) || 'label',
      valueField: (options && options.valueField) || 'value',
      // This is a mock endpoint - in a real widget, this would be configured via options
      apiEndpoint: (options && options.apiEndpoint) || '/api/autocomplete',
      placeholder: (options && options.placeholder) || 'Type to search...',
    };

    // Function to fetch suggestions
    var fetchSuggestions = function (searchText) {
      if (searchText.length < config.minSearchLength) {
        setSuggestions([]);
        return;
      }

      setLoading(true);

      // This is a mock implementation that simulates an API call
      // In a real widget, we would make an actual API call to the endpoint

      // Simulate API delay
      new Promise(function (resolve) {
        setTimeout(resolve, 500);
      })
        .then(function () {
          // Create some mock data based on the search term
          var mockData = [];
          var item1 = {};
          item1[config.valueField] = searchText + '-1';
          item1[config.labelField] = searchText + ' Option 1';
          mockData.push(item1);

          var item2 = {};
          item2[config.valueField] = searchText + '-2';
          item2[config.labelField] = searchText + ' Option 2';
          mockData.push(item2);

          var item3 = {};
          item3[config.valueField] = searchText + '-3';
          item3[config.labelField] = searchText + ' Option 3';
          mockData.push(item3);

          setSuggestions(mockData);
        })
        .catch(function (error) {
          console.error('Error fetching autocomplete suggestions:', error);
          setSuggestions([]);
        })
        .then(function () {
          setLoading(false);
        });
    };

    // Debounced search
    useEffect(
      function () {
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
        }

        timeoutRef.current = setTimeout(function () {
          fetchSuggestions(inputValue);
        }, config.debounceMs);

        return function () {
          if (timeoutRef.current) {
            clearTimeout(timeoutRef.current);
          }
        };
      },
      [inputValue],
    );

    // Update selectedOption when value changes from outside
    useEffect(
      function () {
        if (value) {
          // If value is an object with the expected structure
          if (typeof value === 'object' && value !== null) {
            setSelectedOption(value);
          }
          // If value is just the ID/value part
          else if (typeof value === 'string' || typeof value === 'number') {
            // Try to find in suggestions, or create a placeholder object
            var found = suggestions.find(function (item) {
              return item[config.valueField] === value;
            });
            if (found) {
              setSelectedOption(found);
            } else {
              // Create a placeholder with just the ID
              var placeholder = {};
              placeholder[config.valueField] = value;
              placeholder[config.labelField] = 'ID: ' + value;
              setSelectedOption(placeholder);

              // Optionally fetch the details for this ID
              // fetchItemDetails(value);
            }
          }
        } else {
          setSelectedOption(null);
        }
      },
      [value, suggestions],
    );

    // Check if there are validation errors
    var hasError = rawErrors && rawErrors.length > 0;

    // Create the renderInput function that would normally be passed as JSX
    var renderInput = function (params) {
      // Create the endAdornment with loading indicator if needed
      var loadingIndicator = loading
        ? React.createElement(mui.CircularProgress, {
            key: 'progress',
            color: 'inherit',
            size: 20,
          })
        : null;

      // Combine the loading indicator with the existing endAdornment
      var endAdornment = React.createElement(
        React.Fragment,
        null,
        [loadingIndicator, params.InputProps.endAdornment].filter(Boolean),
      );

      // Create the InputProps object
      var inputProps = Object.assign({}, params.InputProps, {
        endAdornment: endAdornment,
      });

      // Return the TextField
      return React.createElement(
        mui.TextField,
        Object.assign({}, params, {
          label: label,
          placeholder: config.placeholder,
          required: required,
          error: hasError,
          InputProps: inputProps,
        }),
      );
    };

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

    // Create the Autocomplete component
    var autocomplete = React.createElement(mui.Autocomplete, {
      id: id,
      value: selectedOption,
      onChange: function (event, newValue) {
        setSelectedOption(newValue);
        onChange(newValue);
      },
      inputValue: inputValue,
      onInputChange: function (event, newInputValue) {
        setInputValue(newInputValue);
      },
      options: suggestions,
      getOptionLabel: function (option) {
        return option ? option[config.labelField] : '';
      },
      loading: loading,
      disabled: disabled || readonly,
      renderInput: renderInput,
    });

    // Return the final component wrapped in a Box
    return React.createElement(
      mui.Box,
      {
        sx: { mb: 2, mt: 1, width: '100%' },
      },
      [autocomplete, errorMessage].filter(Boolean),
    );
  },
};
