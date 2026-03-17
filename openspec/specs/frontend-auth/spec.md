## ADDED Requirements

### Requirement: User can register a new account
The system SHALL provide a registration page where users can create a new NodeVault account with email, username, and password.

#### Scenario: Successful registration
- **WHEN** user fills in valid email, username, and password (≥8 chars, uppercase + lowercase + digit) and submits
- **THEN** account is created, user is redirected to the dashboard, and JWT token is stored in localStorage

#### Scenario: Registration with duplicate email
- **WHEN** user submits a registration form with an email already in use
- **THEN** an inline error message is displayed: "该邮箱已被注册"

#### Scenario: Registration with weak password
- **WHEN** user submits a password that does not meet complexity requirements
- **THEN** form validation prevents submission and shows: "密码需包含大写字母、小写字母和数字，且至少8位"

### Requirement: User can log in with email and password
The system SHALL provide a login page where users authenticate with email and password.

#### Scenario: Successful login
- **WHEN** user enters a valid email and password and clicks "登录"
- **THEN** JWT access token is stored in localStorage, user is redirected to the dashboard

#### Scenario: Login with wrong credentials
- **WHEN** user enters incorrect email or password
- **THEN** an error message "邮箱或密码错误" is displayed; no redirect occurs

### Requirement: User remains authenticated across page refreshes
The system SHALL restore authentication state from localStorage on app load.

#### Scenario: Token persists on refresh
- **WHEN** user has a valid token in localStorage and refreshes the page
- **THEN** user remains logged in and is not redirected to login page

### Requirement: User can log out
The system SHALL provide a logout action that clears the session.

#### Scenario: Logout clears token
- **WHEN** user clicks the logout button in the navigation bar
- **THEN** token is removed from localStorage, Pinia auth store is cleared, and user is redirected to /login

### Requirement: Unauthenticated users are redirected to login
The system SHALL redirect unauthenticated users attempting to access protected routes.

#### Scenario: Accessing protected route without token
- **WHEN** user navigates to any route under / (dashboard, nodes, etc.) without a valid token
- **THEN** Vue Router guard redirects them to /login
