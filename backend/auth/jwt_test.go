package auth

import (
	"testing"
)

func TestGenerateAndValidateToken(t *testing.T) {
	secret := "test-secret-key"
	username := "testuser"

	token, err := GenerateToken(secret, username)
	if err != nil {
		t.Fatalf("GenerateToken failed: %v", err)
	}
	if token == "" {
		t.Fatal("token should not be empty")
	}

	claims, err := ValidateToken(secret, token)
	if err != nil {
		t.Fatalf("ValidateToken failed: %v", err)
	}
	if claims.Username != username {
		t.Errorf("expected username %s, got %s", username, claims.Username)
	}
}

func TestValidateTokenInvalidSecret(t *testing.T) {
	token, _ := GenerateToken("secret1", "user")
	_, err := ValidateToken("secret2", token)
	if err == nil {
		t.Error("expected error for wrong secret")
	}
}

func TestValidateTokenMalformed(t *testing.T) {
	_, err := ValidateToken("secret", "not-a-jwt")
	if err == nil {
		t.Error("expected error for malformed token")
	}
}
