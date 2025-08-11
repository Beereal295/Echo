# Authentication Implementation Tasklist

## Overview
Implement local-first authentication with personalized user experience. Each user gets their own database and personalized interaction with Echo.

## Phase 1: Database Architecture & User Registry

### Multi-User Database Setup
1. [ ] Create `app_data/shared/` directory structure
2. [ ] Create `app_data/users/` directory structure  
3. [ ] Design user registry database schema (`user_registry.db`)
4. [ ] Create user registry SQL migration scripts
5. [ ] Implement `UserRegistryService` for database operations
6. [ ] Add database indexes for performance (username, active users)
7. [ ] Create database initialization and migration utilities
8. [ ] Test user registry creation and basic CRUD operations

### Database Manager & Session Handling
9. [ ] Implement `DatabaseManager` service for switching user databases
10. [ ] Create `SessionManager` for in-memory session handling
11. [ ] Add database path resolution logic for multi-user
12. [ ] Implement user database initialization (copy existing schema)
13. [ ] Create backward compatibility migration (single-user → multi-user)
14. [ ] Test database switching between multiple users
15. [ ] Test session creation, validation, and cleanup

## Phase 2: Backend Authentication Service

### Core Authentication Logic
16. [ ] Install bcrypt dependency for password hashing
17. [ ] Create `auth_service.py` with core authentication logic
18. [ ] Implement password hashing and validation
19. [ ] Create secret phrase hashing and validation
20. [ ] Generate and validate emergency recovery keys (UUID)
21. [ ] Add rate limiting for login attempts (5 per hour)
22. [ ] Implement temporary account lockouts on failed attempts
23. [ ] Test all authentication methods with various inputs

### API Routes & Models  
24. [ ] Create `auth.py` API routes file
25. [ ] Create `auth_models.py` and `user_models.py` Pydantic models
26. [ ] Implement user registration endpoint (`POST /api/auth/register`)
27. [ ] Implement login endpoint (`POST /api/auth/login`)
28. [ ] Implement user listing endpoint (`GET /api/auth/users`)
29. [ ] Implement recovery phrase validation (`POST /api/auth/verify-phrase`)
30. [ ] Implement emergency key validation (`POST /api/auth/emergency`)
31. [ ] Implement session status endpoint (`GET /api/auth/session`)
32. [ ] Add logout endpoint (`POST /api/auth/logout`)

### Development & Security Tools
33. [ ] Implement development override system (DEV_MODE environment variable)
34. [ ] Create development reset endpoint (`POST /api/auth/dev/reset`)
35. [ ] Create test user creation endpoint (`POST /api/auth/dev/create-test-user`)
36. [ ] Add security utilities (`security.py`) for hashing and validation
37. [ ] Create file utilities (`file_utils.py`) for emergency key handling
38. [ ] Implement database utilities (`database_utils.py`) for path management
39. [ ] Test development safety nets and override systems

## Phase 3: Frontend Authentication UI

### Landing Page & Auth Modals
40. [x] Create `LandingPage.tsx` with Echo logo and tagline
41. [x] Add "Sign Up" and "Sign In" buttons on landing page
42. [x] Create `SignupModal.tsx` with name, password, recovery phrase, emergency key generation
43. [x] Create `LoginModal.tsx` with name/password/recovery phrase/emergency key upload
44. [x] Integrated recovery options into LoginModal (tabbed interface)
45. [x] Emergency key file upload integrated into LoginModal
46. [x] Add form validation and password strength indicator
47. [x] Style modals with consistent Echo design
48. [x] Test all modals with mock data

### Authentication State Management
49. [ ] Create `useAuth.tsx` hook for authentication state
50. [ ] Create `AuthContext` with user's display name
51. [ ] Implement `authUtils.ts` for client-side auth helpers
52. [ ] Add session management to API service (`api.ts`)  
53. [ ] Store user's display name in session for personalization
54. [ ] Add authentication middleware for protected routes
55. [ ] Test authentication state across component tree

### Personalization Integration
56. [ ] Replace "Welcome to Echo Journal" with "Welcome back, {name}"
57. [ ] Inject user name into diary chat service system prompt
58. [ ] Add user name to memory context displays
59. [ ] Personalize toast notifications with user's name
60. [ ] Update pattern insights to show "{name}'s patterns"
61. [ ] Test personalization across all components
62. [ ] Ensure name persists across sessions

## Phase 4: Integration & Recovery Systems

### Emergency Recovery System
60. [ ] Implement emergency key file generation (outside app directory)
61. [ ] Create emergency key file validation and parsing
62. [ ] Add file upload handling for emergency recovery
63. [ ] Store emergency keys in user directories (`app_data/users/{username}/`)
64. [ ] Test emergency key generation and recovery flow
65. [ ] Add clear user instructions for emergency key backup

### Password Recovery Flow
66. [ ] Connect secret phrase UI to backend validation
67. [ ] Implement password reset after successful recovery
68. [ ] Add confirmation steps for password changes
69. [ ] Test complete recovery flow (phrase → password reset)
70. [ ] Handle recovery failures and provide clear error messages
71. [ ] Test edge cases (expired keys, invalid phrases)

### Multi-User Integration
72. [ ] Connect signup modal to user registry backend
73. [ ] Implement user database creation on registration
74. [ ] Pass user context to all API calls via session
75. [ ] Update DatabaseManager on login to switch to user's DB
76. [ ] Verify complete data separation between users
77. [ ] Test database switching between different users
78. [ ] Implement display name update functionality

## Phase 5: Production Hardening & Testing

### Security Enhancements
79. [ ] Remove all development overrides and master passwords
80. [ ] Implement comprehensive input validation and sanitization
81. [ ] Add CSRF protection for auth endpoints
82. [ ] Implement secure session token generation
83. [ ] Add logging for security events (login attempts, failures)
84. [ ] Conduct security review of all auth code
85. [ ] Test against common attack vectors (brute force, injection)

### Performance & Reliability
86. [ ] Optimize database queries with proper indexing
87. [ ] Add connection pooling for database operations
88. [ ] Implement graceful error handling and recovery
89. [ ] Add comprehensive logging for debugging
90. [ ] Test performance with multiple users and large datasets
91. [ ] Optimize file I/O operations for emergency keys

### Comprehensive Testing
92. [ ] Create comprehensive test suite for all auth functions
93. [ ] Test backward compatibility migration thoroughly
94. [ ] Test with fresh database and existing user data
95. [ ] Conduct end-to-end testing of all user flows
96. [ ] Test error scenarios and edge cases
97. [ ] Performance testing with realistic user loads
98. [ ] Security penetration testing

### Documentation & Migration
99. [ ] Create user documentation for auth features
100. [ ] Document recovery procedures for users
101. [ ] Create admin documentation for multi-user management
102. [ ] Test automatic migration from single-user to multi-user
103. [ ] Create backup and restore procedures
104. [ ] Final production readiness checklist

## Development Safety Checklist

### Always Available During Development
- [ ] Master override password available via DEV_MODE
- [ ] Database backup created before auth implementation
- [ ] Multiple test database profiles set up
- [ ] Direct SQLite reset procedures documented and tested
- [ ] Recovery file generation tested and working
- [ ] Development reset endpoint functional
- [ ] Test user creation working

### Before Each Phase
- [ ] Current implementation backed up
- [ ] Test database prepared
- [ ] Development safety nets verified
- [ ] Rollback plan documented
- [ ] All previous phase tasks completed and tested

### Before Production Release
- [ ] All development overrides removed
- [ ] Security review completed
- [ ] Performance testing passed
- [ ] Backward compatibility verified
- [ ] User documentation complete
- [ ] Emergency procedures tested and documented