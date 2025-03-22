### [2025-03-22] Rename and Enhance Store Data Page to Manage Knowledge Base

**Area Affected**:  
- `routes.py`  
- `create_data.html` → renamed to `manage_knowledge_base.html`  
- `base.html` (dropdown menu link updated)

**Description**:  
- Renamed the route `/create_data` to `/manage_knowledge`  
- Renamed the HTML file from `create_data.html` to `manage_knowledge_base.html`  
- Updated the top-level menu link in `base.html` to point to the new route and label it "Manage Knowledge Base"  
- Preserved all form/accordion functionality for text, image, and file uploads  
- Introduced Bootstrap tabs with two tab options: **Store Knowledge** (active) and **Manage Knowledge** (placeholder)

**Reason**:  
To better reflect the purpose of the page and prepare for a future data management interface.

**Testing Done**:  
- Verified homepage loads successfully after fixing broken route reference  
- Confirmed dropdown menu in header works and links to the new route  
- Tested all accordion sections: Store Text, Upload Image, Upload File  
- Verified flash messages display correctly after form submissions  
- Confirmed tab switching works correctly with Bootstrap layout

**Follow-up**:  
- Build out the Manage Knowledge tab with a paginated, sortable data table (Step 2)
