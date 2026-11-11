# Global Record Search (Odoo 20)

Search business records from Odoo's built-in **Ctrl+K command palette**. Results
appear under **Records**, including in the palette's `/` namespace. This module
does not add a separate search bar to the home menu.

## Functionality

- Searches models connected to window actions in menus visible to the current
  user, subject to that user's read access.
- Uses each model's display-name search and can include administrator-configured
  extra stored text fields, such as a product barcode.
- Applies the current user's access restrictions and active company context to
  each search.
- Searches models in priority order and batches of 12, returning up to five
  matching records per model by default.
- Opens a selected result directly in its form, or opens the model's list view
  for additional matches using the same search domain.
- Highlights the typed term in result names and shows a useful subtitle when
  available (for example email, reference, related partner, or phone).
- Provides administrator settings to exclude models, set search priority, and
  add extra search fields.
- Uses a three-character minimum and 300 ms debounce by default. System
  parameters `global_record_search.limit` and
  `global_record_search.min_chars` can change the result limit and minimum
  length; keep the JavaScript `MIN_CHARS` value in sync with the latter.

## Implementation notes

This module depends on `web` and `web_enterprise`, adds a provider to Odoo's
command palette, and styles that built-in palette. Verify the palette UI against
the exact Odoo 20 build you deploy.

Install by placing `global_record_search` in an addons path, updating the Apps
list, and installing **Global Record Search**. The included tests can be run
with `--test-tags /global_record_search` on an Odoo 20 test instance.
