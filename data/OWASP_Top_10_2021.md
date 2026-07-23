# OWASP Top 10 - 2021 Security Knowledge Base

## A01:2021 - Broken Access Control
### Description
Access control enforces policy such that users cannot act outside of their intended permissions. Failures typically lead to unauthorized information disclosure, modification, or destruction of all data or performing a business function outside the user's limits.

### Common Vulnerabilities
- Bypassing access control checks by modifying the URL (parameter tampering), internal application state, or the HTML page.
- Permitting viewing or editing someone else's account, by providing its unique identifier (Insecure Direct Object References - IDOR).
- Accessing API with missing access controls for POST, PUT and DELETE.
- Elevation of privilege: Acting as a user without being logged in or acting as an admin when logged in as a user.

### Example Code (Vulnerable - PHP)
```php
// IDOR Vulnerability: Fetching user profile without verifying ownership
$user_id = $_GET['user_id'];
$query = "SELECT * FROM users WHERE id = '$user_id'";
$result = mysqli_query($conn, $query);
```

### Mitigation & Prevention
- Enforce access control in trusted server-side code or serverless API.
- Deny access by default (Principle of Least Privilege).
- Implement access control mechanisms once and re-use them throughout the application.
- Disable web server directory listing and ensure file metadata (e.g., .git) is not present within web roots.

---

## A02:2021 - Cryptographic Failures
### Description
Failures related to cryptography (or lack thereof), which frequently leads to sensitive data exposure or system compromise.

### Common Vulnerabilities
- Sensitive data transmitted in cleartext (HTTP, FTP, SMTP).
- Using old or weak cryptographic algorithms (e.g., MD5, SHA1, DES, RC4).
- Hardcoded encryption keys in source code.
- Improper key management and key rotation.

### Example Code (Vulnerable - JavaScript/Node.js)
```javascript
// Weak Hashing (MD5) for passwords
const crypto = require('crypto');
function hashPassword(password) {
    return crypto.createHash('md5').update(password).digest('hex');
}
```

### Mitigation & Prevention
- Encrypt all sensitive data in transit using strong TLS protocols (TLS 1.3).
- Encrypt data at rest using standard strong encryption algorithms (e.g., AES-256-GCM).
- Store passwords using strong salted password hashing algorithms such as Argon2id, bcrypt, or PBKDF2.

---

## A03:2021 - Injection (SQL, Command, Cross-Site Scripting)
### Description
An application is vulnerable to attack when user-supplied data is not validated, filtered, or sanitized by the application before sending to an interpreter.

### Common Vulnerabilities
- SQL Injection: User input concatenated directly into SQL queries.
- Command Injection: User input passed directly to system shell execution functions (`exec`, `system`).
- Cross-Site Scripting (XSS): Reflected or stored untrusted user data rendered directly into HTML without escaping.

### Example Code (Vulnerable - Python/SQL)
```python
# SQL Injection
user_input = request.args.get('username')
query = f"SELECT * FROM users WHERE username = '{user_input}'"
cursor.execute(query)
```

### Mitigation & Prevention
- Use safe APIs, prepared statements, or Parameterized Queries (PDO in PHP, parameterized SQL in Python).
- Use positive server-side input validation ("allow-listing").
- For XSS: Use context-aware HTML entity encoding before rendering user input.

---

## A04:2021 - Insecure Design
### Description
Insecure design is a broad category representing different weaknesses, expressed as "missing or ineffective control design". It is distinct from insecure implementation.

### Mitigation & Prevention
- Establish and use a secure development lifecycle with AppSec professionals.
- Use threat modeling for critical authentication, access control, key logic, and key flows.
- Integrate security checks and controls into user stories.

---

## A05:2021 - Security Misconfiguration
### Description
Security misconfiguration occurs when security controls are inaccurately configured or left as default values.

### Common Vulnerabilities
- Unnecessary features enabled (e.g., unneeded ports, services, pages, accounts).
- Default accounts and passwords unchanged.
- Detailed error messages displaying stack traces to end users.
- Missing security headers (e.g., Content-Security-Policy, X-Frame-Options).

---

## A07:2021 - Identification and Authentication Failures
### Description
Confirmation of the user's identity, authentication, and session management is critical to protect against authentication-related attacks.

### Common Vulnerabilities
- Permits automated attacks such as credential stuffing or brute force attacks.
- Weak or ineffective multi-factor authentication (MFA).
- Session IDs exposed in the URL or insecure storage (e.g., plain localStorage without HttpOnly flag).

### Mitigation & Prevention
- Implement Multi-Factor Authentication (MFA).
- Enforce strong password complexity and check against breached password lists.
- Secure session management with `HttpOnly`, `Secure`, `SameSite` flags on cookies.

---

## A10:2021 - Server-Side Request Forgery (SSRF)
### Description
SSRF flaws occur whenever a web application fetches a remote resource without validating the user-supplied URL.

### Example Code (Vulnerable - Node.js)
```javascript
// SSRF Vulnerability: Fetching arbitrary URL provided by user
app.get('/fetch-image', async (req, res) => {
    const imageUrl = req.query.url;
    const response = await fetch(imageUrl); // Attacker can pass 'http://169.254.169.254/latest/meta-data/'
    const data = await response.buffer();
    res.send(data);
});
```

### Mitigation & Prevention
- Segment remote resource access functionality in separate networks.
- Enforce strict URL parsing and allow-listing of allowed protocols and domain names/IPs.
