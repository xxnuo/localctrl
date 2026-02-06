package config

import (
	"os"
	"path/filepath"
	"testing"
)

func TestRandomString(t *testing.T) {
	s1 := randomString(16)
	s2 := randomString(16)
	if len(s1) != 16 {
		t.Errorf("expected length 16, got %d", len(s1))
	}
	if s1 == s2 {
		t.Error("two random strings should not be equal")
	}
}

func TestGenerateDefault(t *testing.T) {
	cfg := generateDefault()
	if cfg.Port != 2001 {
		t.Errorf("expected port 2001, got %d", cfg.Port)
	}
	if cfg.DefaultUser.Username != "admin" {
		t.Errorf("expected admin user, got %s", cfg.DefaultUser.Username)
	}
	if cfg.Password == "" || cfg.JWTSecret == "" || cfg.DefaultUser.Password == "" {
		t.Error("generated secrets should not be empty")
	}
}

func TestSaveAndLoad(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "config.yaml")

	cfg := generateDefault()
	cfg.Port = 9999

	err := save(cfg, path)
	if err != nil {
		t.Fatalf("save failed: %v", err)
	}

	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("read failed: %v", err)
	}
	if len(data) == 0 {
		t.Error("saved file should not be empty")
	}
}
