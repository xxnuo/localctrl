package auth

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"path/filepath"
	"testing"

	"github.com/gin-gonic/gin"
)

func setupTestRouter(t *testing.T) (*gin.Engine, *Handler) {
	t.Helper()
	gin.SetMode(gin.TestMode)

	dbPath := filepath.Join(t.TempDir(), "test.db")
	store, err := NewStore(dbPath)
	if err != nil {
		t.Fatalf("NewStore: %v", err)
	}
	t.Cleanup(func() { store.Close() })

	h := NewHandler(store, "test-secret", "access123")

	r := gin.New()
	r.POST("/api/auth/login", h.Login)
	r.POST("/api/auth/register", h.Register)
	return r, h
}

func TestPasswordLogin(t *testing.T) {
	r, _ := setupTestRouter(t)

	body, _ := json.Marshal(loginRequest{Type: "password", Password: "access123"})
	req := httptest.NewRequest("POST", "/api/auth/login", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d: %s", w.Code, w.Body.String())
	}
	var resp authResponse
	json.Unmarshal(w.Body.Bytes(), &resp)
	if resp.Token == "" {
		t.Error("expected token")
	}
}

func TestPasswordLoginWrong(t *testing.T) {
	r, _ := setupTestRouter(t)

	body, _ := json.Marshal(loginRequest{Type: "password", Password: "wrong"})
	req := httptest.NewRequest("POST", "/api/auth/login", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	if w.Code != http.StatusUnauthorized {
		t.Fatalf("expected 401, got %d", w.Code)
	}
}

func TestRegisterAndAccountLogin(t *testing.T) {
	r, _ := setupTestRouter(t)

	body, _ := json.Marshal(registerRequest{Username: "newuser", Password: "password123"})
	req := httptest.NewRequest("POST", "/api/auth/register", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	if w.Code != http.StatusCreated {
		t.Fatalf("register expected 201, got %d: %s", w.Code, w.Body.String())
	}

	body, _ = json.Marshal(loginRequest{Type: "account", Username: "newuser", Password: "password123"})
	req = httptest.NewRequest("POST", "/api/auth/login", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w = httptest.NewRecorder()
	r.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("login expected 200, got %d", w.Code)
	}
}
