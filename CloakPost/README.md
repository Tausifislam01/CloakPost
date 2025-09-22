CloakPost
Secure social platform for CSE447 Cryptography Lab, implementing encrypted posts, messaging, and social features.
Features

Authentication: Register, login, logout with PBKDF2-derived session keys.
Posts: Create, edit, delete, search, filter, paginate with Fernet encryption and visibility controls (Global/Friends Only).
Messaging: RSA-encrypted messages.
Friend Requests: Secure relationship management with notifications.
Profiles: View user info, friends, and link to posts.
UI: Responsive, styled with Bootstrap 5.3 and Font Awesome.

Setup

Clone the repository:git clone https://github.com/your-username/CloakPost.git
cd CloakPost


Create a virtual environment:python -m venv env
source env/bin/activate  # Windows: env\Scripts\activate


Install dependencies:pip install -r requirements.txt


Create a .env file based on .env.example:cp .env.example .env

Edit .env with secure values for SECRET_KEY and DATA_ENCRYPTION_KEY.
Run migrations:python manage.py migrate


Start the server:python manage.py runserver


Access at http://localhost:8000.

Security Measures

.env is ignored by .gitignore to protect secrets.
Post content is encrypted with Fernet.
Messages use RSA encryption.
Passwords are hashed with Django’s PBKDF2.
Private repository recommended for submission.

Lab Checkpoints (CSE447)

Login/Register: Implemented at /users/login/ and /users/register/.
Encrypt User Info: RSA keys stored; private key encryption planned.
Hash/Salt Password: Django PBKDF2 and custom PBKDF2HMAC.
Credential Check: Separate login_view.
Key Management: Fernet, RSA, and session keys.
Post/View Encryption: Fernet for posts.
Encrypt Database: Post content and messages encrypted; private key encryption needed.
MAC (Optional): Not implemented but planned.

Future Improvements

Encrypt CustomUser.encrypted_private_key.
Implement key rotation.
Add HMAC for integrity.

