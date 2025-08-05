# Echo Authentication Implementation Plan

## Overview
Implement local-first authentication system with multiple recovery options for Echo journaling app.

## Authentication Strategy

### 1. Multi-User Architecture
- **Separate Database Files**: Each user gets their own complete `diary.db` file
- **User Registry**: Shared `user_registry.db` for authentication and user management
- **File Structure**: `app_data/users/{username}/diary.db` + `emergency.key`
- **Privacy**: Complete data separation between users
- **Performance**: Smaller, faster databases per user

### 2. Primary Authentication
- **Password**: Main authentication method using bcrypt hashing
- **Username**: Unique identifier for each user
- Stored in shared user registry database

### 3. Recovery Methods
- **Secret Phrase**: Memorable backup authentication (e.g., "I miss her banana pancakes")
- **Emergency Recovery Key**: UUID-based unlock file stored in user's directory

### 4. Development Safety
- Master override during development (`DEV_MODE` environment variable)
- Database reset capabilities
- Multiple testing approaches

## Database Architecture

### Multi-User File Structure
```
app_data/
  users/
    john_doe/
      diary.db              -- John's complete diary database (existing schema)
      emergency.key         -- John's recovery key file
    jane_smith/
      diary.db              -- Jane's complete diary database
      emergency.key         -- Jane's recovery key file
  shared/
    user_registry.db        -- Shared authentication database
    app_settings.db         -- Global app preferences (optional)
```

### User Registry Database (New)
```sql
-- user_registry.db - Shared authentication database
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,        -- Unique identifier
    display_name TEXT NOT NULL,           -- User's display name
    password_hash TEXT NOT NULL,          -- bcrypt hash of password
    secret_phrase_hash TEXT,              -- bcrypt hash of recovery phrase
    recovery_key TEXT,                    -- UUID for emergency unlock
    database_path TEXT NOT NULL,          -- Path to user's diary.db
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME,
    failed_login_attempts INTEGER DEFAULT 0,
    account_locked_until DATETIME,
    is_active BOOLEAN DEFAULT TRUE
);

-- Index for fast username lookups
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_active ON users(is_active);
```

### Individual User Databases (Existing Schema)
Each user gets their own complete `diary.db` with existing schema:
- `entries` table (unchanged)
- `patterns` table (unchanged) 
- `conversations` table (unchanged)
- `preferences` table (unchanged - user-specific settings)

**Key Benefits:**
- ✅ **Zero changes** to existing diary database schema
- ✅ **Complete privacy** - users cannot access each other's data
- ✅ **Better performance** - smaller databases per user
- ✅ **Easy backup** - copy user's folder
- ✅ **Simple migration** - current single-user setups work as-is

## File Structure

### Frontend Components
```
src/
  components/
    auth/
      LoginScreen.tsx           -- Main login interface
      SignupScreen.tsx          -- First-time setup
      RecoveryScreen.tsx        -- Password recovery options
      EmergencyRecovery.tsx     -- Unlock file upload
  hooks/
    useAuth.tsx                 -- Authentication state management
  utils/
    authUtils.ts               -- Client-side auth helpers
```

### Backend Implementation
```
backend/
  app/
    services/
      auth_service.py           -- Core authentication logic
      user_registry_service.py  -- User registry database operations
      database_manager.py       -- Multi-user database switching
    api/
      routes/
        auth.py                 -- Auth API endpoints
    models/
      auth_models.py            -- Pydantic models for auth
      user_models.py            -- User registry models
    utils/
      security.py               -- Password hashing, validation
      file_utils.py             -- Emergency key file handling
      database_utils.py         -- Database path management
```

## API Endpoints

### Authentication Endpoints
```python
# User Management
GET  /api/auth/users          -- List existing users (usernames only)
POST /api/auth/register       -- Register new user account
POST /api/auth/login          -- Primary login with username/password
POST /api/auth/logout         -- End current session

# Recovery Methods  
POST /api/auth/verify-phrase  -- Recovery phrase validation
POST /api/auth/emergency      -- Emergency key validation
POST /api/auth/reset-password -- Reset password after recovery

# System Status
GET  /api/auth/status         -- Check if any users exist
GET  /api/auth/session        -- Get current authenticated user info

# Development Only
POST /api/auth/dev/reset      -- Reset entire user registry (dev only)
POST /api/auth/dev/create-test-user -- Create test user (dev only)
```

## Multi-User Implementation Details

### Database Switching Logic
```python
# Database Manager Service
class DatabaseManager:
    def __init__(self):
        self.current_user_id: Optional[int] = None
        self.user_db_path: Optional[str] = None
        
    async def switch_to_user(self, user_id: int):
        """Switch active database to specified user"""
        user = await UserRegistryService.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
            
        self.current_user_id = user_id
        self.user_db_path = user.database_path
        
        # Ensure user's database directory exists
        os.makedirs(os.path.dirname(self.user_db_path), exist_ok=True)
        
        # Initialize user's database if it doesn't exist
        if not os.path.exists(self.user_db_path):
            await self._initialize_user_database(self.user_db_path)
    
    def get_current_db_path(self) -> str:
        """Get current user's database path"""
        if not self.user_db_path:
            raise ValueError("No user session active")
        return self.user_db_path
    
    async def _initialize_user_database(self, db_path: str):
        """Create new user database with existing schema"""
        # Copy schema from template or run migration scripts
        # This creates entries, patterns, conversations, preferences tables
        pass
```

### Session Management
```python
# Session state (in-memory or Redis for production)
class SessionManager:
    def __init__(self):
        self.active_sessions: Dict[str, UserSession] = {}
    
    def create_session(self, user_id: int, username: str) -> str:
        """Create new user session"""
        session_id = str(uuid.uuid4())
        self.active_sessions[session_id] = UserSession(
            user_id=user_id,
            username=username,
            created_at=datetime.now(),
            last_activity=datetime.now()
        )
        return session_id
    
    def get_session(self, session_id: str) -> Optional[UserSession]:
        """Get active session"""
        return self.active_sessions.get(session_id)
    
    def end_session(self, session_id: str):
        """End user session"""
        self.active_sessions.pop(session_id, None)
```

### Backward Compatibility
```python
# Migration for existing single-user installations
async def migrate_single_user_to_multi_user():
    """Migrate existing diary.db to multi-user structure"""
    
    if os.path.exists("diary.db") and not os.path.exists("app_data/shared/user_registry.db"):
        # Create user registry
        await UserRegistryService.initialize()
        
        # Create default user from existing data
        display_name = "Default User"  # Could prompt user
        username = "user1"
        
        # Move existing database to user folder
        user_path = f"app_data/users/{username}/"
        os.makedirs(user_path, exist_ok=True)
        shutil.move("diary.db", f"{user_path}diary.db")
        
        # Create registry entry (without password initially)
        await UserRegistryService.create_user(
            username=username,
            display_name=display_name,
            database_path=f"{user_path}diary.db",
            requires_setup=True  # Force auth setup on first login
        )
```

### Frontend State Management
```typescript
// Auth context for React
interface AuthState {
  isAuthenticated: boolean
  currentUser: User | null
  sessionId: string | null
  isLoading: boolean
}

const AuthContext = createContext<AuthState | null>(null)

// Database service updates
class ApiService {
  private sessionId: string | null = null
  
  setSession(sessionId: string) {
    this.sessionId = sessionId
    // All API calls now include session header
  }
  
  private getHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json'
    }
    
    if (this.sessionId) {
      headers['X-Session-ID'] = this.sessionId
    }
    
    return headers
  }
}
```

## Implementation Phases

### Phase 1: UI Foundation (No Auth Logic)
**Goal**: Build and test UI components without authentication logic

**Tasks**:
1. Create signup form UI with validation
2. Create login form UI
3. Create recovery options UI
4. Test form interactions and validation
5. Design auth flow navigation

**Safety**: No database changes, pure UI development

### Phase 2: Backend Auth Service
**Goal**: Implement core authentication logic with safety nets

**Tasks**:
1. Create auth service with bcrypt integration
2. Add auth API endpoints
3. Implement development override system
4. Create database reset utilities
5. Test with temporary database files

**Safety**: Master override always available, separate test databases

### Phase 3: Basic Password Authentication
**Goal**: Implement primary login/signup flow

**Tasks**:
1. Connect signup UI to backend
2. Implement password hashing and storage
3. Create login validation flow
4. Add session management
5. Test thoroughly with database resets

**Safety**: Keep dev bypass active, test with backup databases

### Phase 4: Recovery Systems
**Goal**: Add secret phrase and emergency key recovery

**Tasks**:
1. Implement secret phrase backup
2. Create emergency key file generation
3. Build recovery flow UI
4. Test all recovery methods
5. Handle edge cases and validation

**Safety**: Multiple recovery options prevent lockout

### Phase 5: Production Hardening
**Goal**: Security enhancements and final testing

**Tasks**:
1. Remove development overrides
2. Add rate limiting for login attempts
3. Implement temporary lockouts
4. Final security review
5. Comprehensive testing with fresh database

**Safety**: Thorough testing before removing safety nets

## Development Safety Nets

### 1. Master Override (Development Only)
```python
# Environment variable or config flag
DEV_MODE = os.getenv('DEV_MODE', 'false').lower() == 'true'
MASTER_PASSWORD = "dev_override_2024"

if DEV_MODE and password == MASTER_PASSWORD:
    return True  # Allow access
```

### 2. Database Reset Options
```python
# Development endpoint
@router.post("/dev/reset-auth")
async def reset_auth():
    if not DEV_MODE:
        raise HTTPException(404)
    
    # Clear all auth data
    await preferences_repo.delete_keys_like('auth_%')
    await preferences_repo.delete_key('setup_completed')
    return {"message": "Auth reset complete"}
```

### 3. Multiple Testing Strategies
- **Fresh Database**: Copy production DB, work with clean slate
- **Profile System**: Different database files for different test scenarios
- **SQLite Direct**: Manual database manipulation when needed

### 4. Emergency Recovery During Development
```sql
-- Direct database access to reset auth
DELETE FROM preferences WHERE key LIKE 'auth_%';
DELETE FROM preferences WHERE key = 'setup_completed';
```

## Security Considerations

### Password Security
- Use bcrypt with appropriate cost factor (12+)
- Never store plain text passwords
- Implement secure password requirements

### Recovery Security
- Hash secret phrases same as passwords
- Emergency keys should be cryptographically secure UUIDs
- Store emergency key files outside app directory

### Session Management
- Simple session tokens for frontend state
- Reasonable session timeouts
- Clear sessions on app close

### Rate Limiting
- Limit login attempts (5 attempts per hour)
- Temporary account lockouts
- Progressive delays on failed attempts

## User Experience Flow

### First Time Setup
1. Welcome screen explains auth purpose
2. Collect display name
3. Set primary password (with strength indicator)
4. Create recovery phrase (with examples/guidance)
5. Generate and save emergency key file
6. Confirmation screen with backup reminders

### Regular Login
1. Simple password entry
2. Optional "Remember for session" checkbox
3. "Forgot password?" link to recovery options

### Recovery Flow
1. Recovery options screen:
   - Try secret phrase
   - Upload emergency key file
2. Success redirects to main app
3. Option to update password after recovery

## Testing Strategy

### Unit Tests
- Password hashing/validation
- Secret phrase handling
- Emergency key generation/validation
- Database operations

### Integration Tests
- Full signup flow
- Login validation
- Recovery processes
- API endpoint responses

### Manual Testing Scenarios
- Happy path signup → login
- Password recovery via phrase
- Emergency key recovery
- Invalid credentials handling
- Database reset and retry

## Risk Mitigation

### Development Risks
- **Lockout**: Master override + database reset options
- **Data Loss**: Database backups before auth changes
- **Testing**: Multiple database profiles for testing

### Production Risks
- **Forgotten Credentials**: Multiple recovery options
- **File Loss**: Clear backup instructions during setup
- **Security**: Regular security reviews, rate limiting

### Recovery Documentation
- Clear user instructions for recovery methods
- Emergency procedures for complete lockout
- Backup and restore procedures

## Success Criteria

### Phase Completion Gates
- ✅ UI components render correctly
- ✅ Backend auth logic passes unit tests
- ✅ End-to-end flows work in development
- ✅ Recovery methods successfully tested
- ✅ Security review completed
- ✅ Production testing with fresh database

### User Experience Goals
- Setup takes < 5 minutes
- Login is instant and intuitive  
- Recovery options are clear and accessible
- Users never lose access to their data
- Security feels robust but not cumbersome