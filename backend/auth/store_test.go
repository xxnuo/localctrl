package auth

import (
	"path/filepath"
	"testing"
)

func newTestStore(t *testing.T) *Store {
	t.Helper()
	dbPath := filepath.Join(t.TempDir(), "test.db")
	store, err := NewStore(dbPath)
	if err != nil {
		t.Fatalf("NewStore failed: %v", err)
	}
	t.Cleanup(func() { store.Close() })
	return store
}

func TestCreateAndAuthenticate(t *testing.T) {
	store := newTestStore(t)

	err := store.CreateUser("alice", "password123")
	if err != nil {
		t.Fatalf("CreateUser failed: %v", err)
	}

	user, err := store.Authenticate("alice", "password123")
	if err != nil {
		t.Fatalf("Authenticate failed: %v", err)
	}
	if user.Username != "alice" {
		t.Errorf("expected alice, got %s", user.Username)
	}
}

func TestAuthenticateWrongPassword(t *testing.T) {
	store := newTestStore(t)
	store.CreateUser("bob", "correct")

	_, err := store.Authenticate("bob", "wrong")
	if err == nil {
		t.Error("expected error for wrong password")
	}
}

func TestDuplicateUser(t *testing.T) {
	store := newTestStore(t)
	store.CreateUser("dup", "pass1")
	err := store.CreateUser("dup", "pass2")
	if err == nil {
		t.Error("expected error for duplicate username")
	}
}

func TestUserExists(t *testing.T) {
	store := newTestStore(t)
	if store.UserExists("ghost") {
		t.Error("user should not exist")
	}
	store.CreateUser("ghost", "pass")
	if !store.UserExists("ghost") {
		t.Error("user should exist")
	}
}

func TestEnsureDefaultUser(t *testing.T) {
	store := newTestStore(t)
	err := store.EnsureDefaultUser("admin", "adminpass")
	if err != nil {
		t.Fatalf("EnsureDefaultUser failed: %v", err)
	}
	if !store.UserExists("admin") {
		t.Error("admin should exist")
	}
	err = store.EnsureDefaultUser("admin", "different")
	if err != nil {
		t.Fatalf("second EnsureDefaultUser failed: %v", err)
	}
}
