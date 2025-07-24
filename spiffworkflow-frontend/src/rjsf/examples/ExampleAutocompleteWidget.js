// Example custom Autocomplete widget implementation
// This would be stored in a JavaScript file within the extension process model

module.exports = {
  /**
   * An autocomplete widget that fetches data from a specified API endpoint
   * This demonstrates more complex widget behavior with data fetching
   */
  default: function AutocompleteWidget(props) {
    const { id, value, onChange, label, required, disabled, readonly, rawErrors, options } = props;
    const React = require('react');
    const { useState, useEffect, useRef } = React;
    
    // MUI components
    const mui = require('@mui/material');
    
    // State for options, loading state, and input value
    const [inputValue, setInputValue] = useState('');
    const [suggestions, setSuggestions] = useState([]);
    const [loading, setLoading] = useState(false);
    const [selectedOption, setSelectedOption] = useState(null);
    const timeoutRef = useRef(null);
    
    // Configuration options with defaults
    const config = {
      minSearchLength: options?.minSearchLength || 2,
      debounceMs: options?.debounceMs || 300,
      labelField: options?.labelField || 'label',
      valueField: options?.valueField || 'value',
      // This is a mock endpoint - in a real widget, this would be configured via options
      apiEndpoint: options?.apiEndpoint || '/api/autocomplete',
      placeholder: options?.placeholder || 'Type to search...',
    };
    
    // Function to fetch suggestions
    const fetchSuggestions = async function(searchText) {
      if (searchText.length < config.minSearchLength) {
        setSuggestions([]);
        return;
      }
      
      setLoading(true);
      
      try {
        // This is a mock implementation that simulates an API call
        // In a real widget, we would make an actual API call to the endpoint
        
        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Create some mock data based on the search term
        const mockData = [
          { [config.valueField]: searchText + '-1', [config.labelField]: searchText + ' Option 1' },
          { [config.valueField]: searchText + '-2', [config.labelField]: searchText + ' Option 2' },
          { [config.valueField]: searchText + '-3', [config.labelField]: searchText + ' Option 3' },
        ];
        
        setSuggestions(mockData);
      } catch (error) {
        console.error('Error fetching autocomplete suggestions:', error);
        setSuggestions([]);
      } finally {
        setLoading(false);
      }
    };
    
    // Debounced search
    useEffect(function() {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      
      timeoutRef.current = setTimeout(function() {
        fetchSuggestions(inputValue);
      }, config.debounceMs);
      
      return function() {
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
        }
      };
    }, [inputValue]);
    
    // Update selectedOption when value changes from outside
    useEffect(function() {
      if (value) {
        // If value is an object with the expected structure
        if (typeof value === 'object' && value !== null) {
          setSelectedOption(value);
        }
        // If value is just the ID/value part
        else if (typeof value === 'string' || typeof value === 'number') {
          // Try to find in suggestions, or create a placeholder object
          const found = suggestions.find(function(item) {
            return item[config.valueField] === value;
          });
          if (found) {
            setSelectedOption(found);
          } else {
            // Create a placeholder with just the ID
            const placeholder = {};
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
    }, [value, suggestions]);
    
    // Check if there are validation errors
    const hasError = rawErrors && rawErrors.length > 0;
    
    // Create the renderInput function that would normally be passed as JSX
    const renderInput = function(params) {
      // Create the endAdornment with loading indicator if needed
      const loadingIndicator = loading ? 
        React.createElement(mui.CircularProgress, { 
          key: 'progress',
          color: 'inherit', 
          size: 20 
        }) : null;
      
      // Combine the loading indicator with the existing endAdornment
      const endAdornment = React.createElement(
        React.Fragment,
        null,
        [loadingIndicator, params.InputProps.endAdornment].filter(Boolean)
      );
      
      // Create the InputProps object
      const inputProps = {
        ...params.InputProps,
        endAdornment: endAdornment
      };
      
      // Return the TextField
      return React.createElement(
        mui.TextField,
        {
          ...params,
          label: label,
          placeholder: config.placeholder,
          required: required,
          error: hasError,
          InputProps: inputProps
        }
      );
    };
    
    // Create error message if needed
    const errorMessage = hasError ? 
      React.createElement(
        mui.FormHelperText,
        { 
          key: 'error-message',
          error: true 
        },
        rawErrors.join(', ')
      ) : null;
    
    // Create the Autocomplete component
    const autocomplete = React.createElement(
      mui.Autocomplete,
      {
        id: id,
        value: selectedOption,
        onChange: function(event, newValue) {
          setSelectedOption(newValue);
          onChange(newValue);
        },
        inputValue: inputValue,
        onInputChange: function(event, newInputValue) {
          setInputValue(newInputValue);
        },
        options: suggestions,
        getOptionLabel: function(option) {
          return option ? option[config.labelField] : '';
        },
        loading: loading,
        disabled: disabled || readonly,
        renderInput: renderInput
      }
    );
    
    // Return the final component wrapped in a Box
    return React.createElement(
      mui.Box,
      { 
        sx: { mb: 2, mt: 1, width: '100%' } 
      },
      [autocomplete, errorMessage].filter(Boolean)
    );
  }
};