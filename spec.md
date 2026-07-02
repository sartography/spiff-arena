On /process-instances page, rather than the way we currently filter dates, do the following instead (and probably only allow filtering by process instance start date instead of both start and end, but if there's an easy way, not sure).
Make it fit into the current UI as well as possible, though let's not change all of the other carbon components to MUI at this time unless easy.

Implement a **Filter Time Range** dropdown with these preset options:

* **Last hour**
* **Last 24 hours**
* **Last 7 days**
* **Last 14 days**
* **Last 30 days**
* **Last 90 days**
* **Absolute date**

The dropdown button shows the currently selected range, for example **“14D”**. The active option in the menu has a checkmark.

Also include a search/input field at the top of the dropdown that accepts custom relative ranges, with placeholder text like:

`Custom range: 2h, 4d, 8w...`

Supported shorthand examples:

* `h` = hours
* `d` = days
* `w` = weeks

When the user selects **Absolute date**, open a calendar range picker.

Absolute date picker behavior:

* Show a monthly calendar with month/year header.
* Provide previous and next month navigation.
* Let the user select a date range.
* Highlight the selected range continuously across the calendar.
* Show separate start and end time inputs below the calendar.
* Include a **UTC** checkbox/toggle (though do whatever is best for our app)
* Include **Back** and **Apply** buttons.
* **Back** returns to the preset dropdown.
* **Apply** confirms the selected absolute date/time range.

The resulting filter should produce a start timestamp and end timestamp. For relative presets, compute them as `now - duration` through `now`. For absolute date, use the selected start/end dates and times, respecting the UTC setting.
