# Fix Maintenance Add Form 404

## Problem
The maintenance add form still returns "Server error: 404 Not Found" after the previous URL fix.

## Current State
- `maintenance/urls.py` has `app_name = 'maintenance'` and route `create_maintenance`
- Root `PROPATIA/urls.py` includes `path('maintenance/', include('maintenance.urls'), name='maintenance')`
- JS was changed from `{% url 'maintenance:create_maintenance' %}` to `/maintenance/create/`
- `reverse('maintenance:create_maintenance')` correctly returns `/maintenance/create/`
- The 404 persists in the browser

## Hypothesis
The 404 is likely coming from one of these sources:
1. The user is accessing the site through a URL prefix (e.g., `/rentals/` or similar) and `/maintenance/create/` is missing that prefix
2. The view is returning 404 because `request.user` is not authenticated or the property/unit lookup fails
3. There's a middleware or routing layer that rewrites/redirects the request
4. The form is submitting to the wrong URL due to a base tag or proxy configuration

## Plan
1. Inspect `dashboard_base.html` and other templates for `<base>` tags or URL prefixes that would affect absolute paths
2. Inspect `PROPATIA/urls.py` for any prefix patterns or middleware that affects `/maintenance/` routing
3. Inspect `maintenance/views.py` `create_maintenance` for any 404-raising logic (property/unit lookups, permissions)
4. If the site runs under a URL prefix, update the JS fetch URL to be relative or configurable
5. If the view raises 404, add explicit validation and return 400 with form errors instead

## Validation
- Submit the maintenance add form in the browser
- Confirm the Network tab shows a 200 response with `{"success": true, ...}`
- Confirm the new maintenance record appears in the list
