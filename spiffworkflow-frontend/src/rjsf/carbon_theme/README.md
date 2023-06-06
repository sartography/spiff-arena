### Custom Validation Error Message for String Inputs

If you have a property in your json schema like:

    "user_generated_number_1": {"type": "string", "title": "User Generated Number", "default": "0", "minLength": 3}

it will generate this error message by default: "User Generated Number must NOT have fewer than 3 characters."

If you add the `validationErrorMessage` key to the property json it will print that message instead.
