package filemanager

import (
	"bytes"
	"encoding/json"
	"io"
	"mime/multipart"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"

	"github.com/gin-gonic/gin"
)

func setupRouter() *gin.Engine {
	gin.SetMode(gin.TestMode)
	r := gin.New()
	h := NewHandler()
	r.GET("/api/files", h.List)
	r.POST("/api/files/mkdir", h.Mkdir)
	r.POST("/api/files/delete", h.Delete)
	r.POST("/api/files/rename", h.Rename)
	r.POST("/api/files/move", h.Move)
	r.POST("/api/files/upload", h.Upload)
	r.GET("/api/files/download", h.Download)
	return r
}

func TestListDir(t *testing.T) {
	r := setupRouter()
	dir := t.TempDir()
	os.WriteFile(filepath.Join(dir, "test.txt"), []byte("hello"), 0644)

	req := httptest.NewRequest("GET", "/api/files?path="+dir, nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", w.Code)
	}

	var resp map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &resp)
	files := resp["files"].([]interface{})
	if len(files) != 1 {
		t.Errorf("expected 1 file, got %d", len(files))
	}
}

func TestMkdirAndDelete(t *testing.T) {
	r := setupRouter()
	dir := filepath.Join(t.TempDir(), "newdir")

	body, _ := json.Marshal(map[string]string{"path": dir})
	req := httptest.NewRequest("POST", "/api/files/mkdir", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if w.Code != http.StatusOK {
		t.Fatalf("mkdir expected 200, got %d", w.Code)
	}

	info, err := os.Stat(dir)
	if err != nil || !info.IsDir() {
		t.Error("directory should exist")
	}

	body, _ = json.Marshal(map[string]string{"path": dir})
	req = httptest.NewRequest("POST", "/api/files/delete", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w = httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if w.Code != http.StatusOK {
		t.Fatalf("delete expected 200, got %d", w.Code)
	}
}

func TestUploadAndDownload(t *testing.T) {
	r := setupRouter()
	dir := t.TempDir()

	var buf bytes.Buffer
	writer := multipart.NewWriter(&buf)
	part, _ := writer.CreateFormFile("file", "upload.txt")
	part.Write([]byte("uploaded content"))
	writer.Close()

	req := httptest.NewRequest("POST", "/api/files/upload?path="+dir, &buf)
	req.Header.Set("Content-Type", writer.FormDataContentType())
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if w.Code != http.StatusOK {
		t.Fatalf("upload expected 200, got %d: %s", w.Code, w.Body.String())
	}

	filePath := filepath.Join(dir, "upload.txt")
	req = httptest.NewRequest("GET", "/api/files/download?path="+filePath, nil)
	w = httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if w.Code != http.StatusOK {
		t.Fatalf("download expected 200, got %d", w.Code)
	}
	body, _ := io.ReadAll(w.Body)
	if string(body) != "uploaded content" {
		t.Errorf("expected 'uploaded content', got '%s'", string(body))
	}
}
