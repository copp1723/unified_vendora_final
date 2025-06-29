# VENDORA Frontend Integration Guide

## Overview

This guide documents the complete frontend integration with the FastAPI backend for the VENDORA platform. The frontend is built with React, TypeScript, and modern UI components.

## Current Implementation Status ✅

### 1. Authentication & Authorization
- ✅ Firebase Authentication integrated
- ✅ Email/password login
- ✅ Email verification requirement
- ✅ Role-based access control (admin/dealer)
- ✅ Protected routes
- ✅ Global auth context

### 2. API Integration
- ✅ VendoraAPI class with authenticated requests
- ✅ All backend endpoints integrated
- ✅ TypeScript interfaces matching Pydantic models
- ✅ Error handling and user feedback
- ✅ Loading states

### 3. Core Features

#### Dealer Portal
- ✅ Dashboard with metrics and insights
- ✅ AI Chat interface for queries
- ✅ Task feedback system
- ✅ Pipeline status monitoring
- ✅ File upload interface
- ✅ File management

#### Admin Dashboard
- ✅ System health monitoring
- ✅ Real-time metrics
- ✅ Query analytics
- ✅ Error tracking
- ✅ Admin AI assistant
- ✅ Dealer management interface

### 4. UI/UX
- ✅ Responsive design
- ✅ Loading states
- ✅ Error messages with toasts
- ✅ Success feedback
- ✅ Drag-and-drop file upload
- ✅ Real-time updates (polling)

## Setup Instructions

### 1. Environment Configuration

Create a `.env` file in the `vendora_rep_src` directory:

```bash
cp .env.example .env
```

Update the values with your Firebase configuration and API URL.

### 2. Install Dependencies

```bash
cd vendora_rep_src
npm install
```

### 3. Start Development Server

```bash
npm run dev
```

The application will be available at `http://localhost:5173`

## Architecture

### Component Structure
```
vendora_rep_src/
├── components/
│   ├── ui/           # shadcn/ui components
│   ├── ErrorBoundary.tsx
│   ├── FeedbackForm.tsx
│   ├── FileUpload.tsx
│   └── ProtectedRoute.tsx
├── contexts/
│   ├── AuthContext.tsx
│   └── ThemeContext.tsx
├── lib/
│   ├── api.ts        # API client
│   ├── firebase.ts   # Firebase config
│   ├── types.ts      # TypeScript types
│   └── queryClient.ts
├── pages/
│   ├── DealerPortal.tsx
│   ├── AdminDashboard.tsx
│   └── TestAuth.tsx
└── App.tsx
```

### Key Components

#### AuthContext
Manages global authentication state and user information.

```typescript
const { user, userInfo, isLoading, isAuthenticated } = useAuth();
```

#### API Client
Centralized API communication with automatic authentication.

```typescript
const response = await api.submitQuery({
  query: "What were my top sellers?",
  dealership_id: "dealer_123",
  context: { source: "web_portal" }
});
```

#### Protected Routes
Ensures only authenticated users with proper permissions can access certain pages.

```typescript
<ProtectedRoute requireAdmin>
  <AdminDashboard />
</ProtectedRoute>
```

## API Endpoints

### Authentication
- `GET /api/v1/auth/me` - Get current user info
- `POST /api/v1/auth/users` - Create new user (admin only)

### Query Processing
- `POST /api/v1/query` - Submit analytical query
- `GET /api/v1/task/{task_id}/status` - Get task status
- `POST /api/v1/task/{task_id}/feedback` - Submit feedback

### Pipeline
- `GET /api/v1/pipeline/tasks` - List pipeline tasks
- `GET /api/v1/pipeline/task/{task_id}` - Get specific task

### System (Admin)
- `GET /api/v1/system/metrics` - System metrics
- `GET /api/v1/system/overview` - System overview
- `GET /api/v1/agent/{agent_id}/explanation` - Agent details

## Data Flow

1. **User Login**
   - Firebase authentication
   - Get ID token
   - Fetch user info from backend
   - Store in AuthContext

2. **Query Submission**
   - User enters query in chat
   - Submit to `/api/v1/query`
   - Receive QueryResponse with task_id
   - Display summary and confidence
   - Enable feedback submission

3. **File Upload**
   - User selects/drops files
   - Validate file types and sizes
   - Upload to backend (TODO: implement endpoint)
   - Files processed through pipeline
   - Status visible in Pipeline tab

## Remaining Tasks

### Backend Integration
- [ ] Implement file upload endpoint
- [ ] WebSocket/SSE for real-time updates
- [ ] Dealer-specific dashboard data endpoint
- [ ] Automated report viewing endpoints

### Frontend Enhancements
- [ ] Real-time task status updates (WebSocket)
- [ ] Data visualization components
- [ ] Download processed reports
- [ ] Advanced filtering for pipeline tasks
- [ ] Dealer management functionality

### Testing
- [ ] Unit tests for components
- [ ] Integration tests for API calls
- [ ] E2E tests for critical flows

## Security Considerations

1. **Authentication**
   - All API calls include Firebase ID token
   - Email verification required
   - Role-based access control

2. **Data Access**
   - Dealers can only access their own data
   - Admins have system-wide access
   - Dealership ID validation

3. **File Upload**
   - File type validation
   - Size limits (50MB default)
   - Malware scanning (backend responsibility)

## Performance Optimizations

1. **Query Caching**
   - React Query handles caching
   - Configurable cache times
   - Background refetching

2. **Lazy Loading**
   - Code splitting for routes
   - Component lazy loading
   - Image optimization

3. **State Management**
   - Minimal re-renders
   - Optimized context usage
   - Memoized expensive operations

## Troubleshooting

### Common Issues

1. **"Authentication token not available"**
   - Ensure user is logged in
   - Check Firebase configuration
   - Verify email is verified

2. **CORS Errors**
   - Backend CORS configuration
   - Check API_URL in .env

3. **File Upload Failures**
   - Check file size limits
   - Verify file formats
   - Network connectivity

## Development Guidelines

1. **TypeScript**
   - Strict mode enabled
   - All API responses typed
   - No `any` types in production code

2. **Component Guidelines**
   - Functional components with hooks
   - Proper error boundaries
   - Loading states for async operations

3. **Code Style**
   - ESLint configuration
   - Prettier formatting
   - Consistent naming conventions

## Deployment

### Production Build
```bash
npm run build
```

### Environment Variables
Ensure all `REACT_APP_*` variables are set in the deployment environment.

### Hosting
- Static hosting (Vercel, Netlify, AWS S3)
- Configure redirects for SPA routing
- Enable HTTPS

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review backend logs
3. Contact the development team

---

Last Updated: Current Date
Version: 1.0.0
