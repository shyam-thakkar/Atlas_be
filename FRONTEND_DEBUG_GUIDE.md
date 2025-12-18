# Frontend Tech Badge Creation - Debugging Guide

## Backend Status: ✅ WORKING
The backend has been tested and is working correctly. Both test cases passed:
- Adding tech with just `name` field: ✅
- Adding tech with `display_name` field: ✅

## Common Frontend Issues & Solutions

### 1. **Check Authentication**
The endpoint requires authentication. Ensure:
```javascript
// Include JWT token in headers
headers: {
  'Authorization': `Bearer ${accessToken}`,
  'Content-Type': 'application/json'
}
```

### 2. **Check Request Format**
The backend accepts these formats:

**Option A: Using 'name' field (simplest)**
```json
{
  "name": "Ruby",
  "icon_source_url": "https://cdn.simpleicons.org/ruby"
}
```

**Option B: Using 'display_name'**
```json
{
  "display_name": "Ruby",
  "icon_source_url": "https://cdn.simpleicons.org/ruby"
}
```

**Option C: Full control**
```json
{
  "display_name": "Ruby",
  "code_name": "ruby",
  "icon_source_url": "https://cdn.simpleicons.org/ruby",
  "doc_url": "https://www.ruby-lang.org/"
}
```

### 3. **Check Network Tab**
Open browser DevTools → Network tab and look for:
- **Request URL**: Should be `http://localhost:8000/api/profile/tech/`
- **Request Method**: POST
- **Status Code**: Should be 201 (Created) or 200 (Already exists)
- **Request Headers**: Check `Authorization` and `Content-Type`
- **Request Payload**: Verify the JSON structure

### 4. **Check Console for Errors**
Look for:
- CORS errors
- 401 Unauthorized (missing/invalid token)
- 400 Bad Request (check response body for details)

### 5. **Backend Logs**
Now that logging is enabled, check the Django server terminal for:
```
TechCreate POST - Raw data: {...}
TechCreate POST - Content-Type: application/json
TechCreate POST - User: user@example.com
```

If you see errors like:
```
TechCreate POST - Missing name/display_name/code_name
TechCreate POST - Validation errors: {...}
```

This tells you exactly what's wrong.

## Example Frontend Code (React/Next.js)

```typescript
const addTechnology = async (name: string, iconUrl?: string) => {
  try {
    const response = await fetch('http://localhost:8000/api/profile/tech/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getAccessToken()}`, // Your token getter
        'Content-Type': 'application/json',
      },
      credentials: 'include', // Important for cookies
      body: JSON.stringify({
        name: name,
        icon_source_url: iconUrl || `https://cdn.simpleicons.org/${name.toLowerCase()}`
      })
    });

    if (!response.ok) {
      const error = await response.json();
      console.error('Failed to add tech:', error);
      throw new Error(error.error || 'Failed to add technology');
    }

    const data = await response.json();
    console.log('Tech added:', data);
    return data;
  } catch (error) {
    console.error('Error adding technology:', error);
    throw error;
  }
};
```

## Quick Test
Try this in your browser console (while logged in):
```javascript
fetch('http://localhost:8000/api/profile/tech/', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN_HERE',
    'Content-Type': 'application/json',
  },
  credentials: 'include',
  body: JSON.stringify({
    name: 'Ruby',
    icon_source_url: 'https://cdn.simpleicons.org/ruby'
  })
})
.then(r => r.json())
.then(console.log)
.catch(console.error);
```

## Next Steps
1. Try the request from the frontend
2. Check the Django server terminal for the new log messages
3. Share the exact error message you see (from network tab or console)
4. If you see logs in the terminal, share those too
