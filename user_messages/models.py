from django.db import models
from django.conf import settings

from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.exceptions import InvalidSignature

from CloakPost.key_management import encrypt_aes, decrypt_aes

import secrets
import base64


class Message(models.Model):
    """
    Hybrid-encrypted direct message:
      - AES-256-GCM encrypts the content (random 32-byte key)
      - RSA-OAEP (SHA-256) encrypts the AES key to the recipient
      - RSA-PSS (SHA-256) signs a stable transcript for authenticity

    Stored fields are BINARY (no plaintext at rest):
      - encrypted_key: RSA-OAEP ciphertext of the AES key
      - encrypted_content: AES-GCM blob (iv + ciphertext + tag)
      - signature: RSA-PSS signature over the transcript
    """
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="sent_messages",
        on_delete=models.CASCADE,
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="received_messages",
        on_delete=models.CASCADE,
    )

    # RSA-encrypted AES key (Binary)
    encrypted_key = models.BinaryField()

    # AES-GCM blob: iv (12B) + ciphertext + tag (16B)
    encrypted_content = models.BinaryField()

    # RSA-PSS signature over transcript (Binary)
    signature = models.BinaryField()

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Message #{self.pk} from {self.sender} to {self.recipient}"

    # ---------------------------------------------------------------------
    # Helpers (no DB changes)
    # ---------------------------------------------------------------------

    @property
    def encrypted_key_b64(self) -> str:
        """Base64 view for JSON/WebSocket payloads."""
        return base64.b64encode(self.encrypted_key).decode()

    @property
    def encrypted_content_b64(self) -> str:
        """Base64 view for JSON/WebSocket payloads."""
        return base64.b64encode(self.encrypted_content).decode()

    @property
    def signature_b64(self) -> str:
        """Base64 view for JSON/WebSocket payloads."""
        return base64.b64encode(self.signature).decode()

    # ---------------------------------------------------------------------
    # Crypto core
    # ---------------------------------------------------------------------

    def _transcript(self) -> bytes:
        """
        Stable bytes to sign/verify:

            sender_id | recipient_id | encrypted_key | encrypted_content

        This binds the signature to the identity tuple and the exact ciphertexts.
        """
        sid = str(self.sender_id).encode()
        rid = str(self.recipient_id).encode()
        return b"|".join([sid, rid, self.encrypted_key, self.encrypted_content])

    def encrypt_and_sign(
        self,
        content: str,
        recipient_public_key_pem: str,
        sender_private_key,
    ) -> None:
        """
        Hybrid encryption + sender authenticity:

        1) Generate random 32-byte AES key.
        2) Encrypt content with AES-256-GCM -> iv + ciphertext + tag.
        3) Encrypt AES key to recipient using RSA-OAEP(SHA-256).
        4) Sign transcript with sender RSA-PSS(SHA-256).

        Args:
            content: plaintext message to encrypt.
            recipient_public_key_pem: PEM string of the recipient's RSA public key.
            sender_private_key: a cryptography RSA private key object
                                (already decrypted/unlocked in-memory).
        """
        # 1) Random symmetric key
        sym_key = secrets.token_bytes(32)

        # 2) Encrypt message with AES-256-GCM
        blob = encrypt_aes(content.encode(), sym_key)

        # 3) Encrypt symmetric key to recipient (RSA-OAEP)
        public_key = serialization.load_pem_public_key(
            recipient_public_key_pem.encode()
        )
        encrypted_sym_key = public_key.encrypt(
            sym_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )

        self.encrypted_key = encrypted_sym_key
        self.encrypted_content = blob

        # 4) Sign transcript with sender's private key (RSA-PSS)
        signature = sender_private_key.sign(
            self._transcript(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )
        self.signature = signature

    def verify_signature(self) -> bool:
        """
        Verify RSA-PSS signature using sender's public key (stored in DB as PEM).
        Returns:
            True if signature is valid, else False.
        """
        try:
            public_key = serialization.load_pem_public_key(
                self.sender.public_key.encode()
            )
            public_key.verify(
                self.signature,
                self._transcript(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )
            return True
        except (InvalidSignature, ValueError, TypeError):
            return False

    def decrypt_content(self, private_key) -> str:
        """
        Decrypt the hybrid-encrypted message:

        1) RSA-OAEP decrypt the symmetric AES key with recipient's private key.
        2) AES-GCM decrypt the content blob.

        Args:
            private_key: a cryptography RSA private key object belonging to the recipient.

        Returns:
            Decrypted plaintext as UTF-8 string.
        """
        sym_key = private_key.decrypt(
            self.encrypted_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        pt = decrypt_aes(self.encrypted_content, sym_key)
        return pt.decode()