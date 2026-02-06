package filemanager

import (
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"

	"github.com/gin-gonic/gin"
)

type FileEntry struct {
	Name    string `json:"name"`
	Path    string `json:"path"`
	IsDir   bool   `json:"isDir"`
	Size    int64  `json:"size"`
	ModTime string `json:"modTime"`
	Mode    string `json:"mode"`
}

type Handler struct{}

func NewHandler() *Handler {
	return &Handler{}
}

func sanitizePath(p string) (string, error) {
	cleaned := filepath.Clean(p)
	if !filepath.IsAbs(cleaned) {
		home, _ := os.UserHomeDir()
		cleaned = filepath.Join(home, cleaned)
	}
	return cleaned, nil
}

func (h *Handler) List(c *gin.Context) {
	path := c.Query("path")
	if path == "" {
		home, _ := os.UserHomeDir()
		path = home
	}

	absPath, err := sanitizePath(path)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid path"})
		return
	}

	entries, err := os.ReadDir(absPath)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	files := make([]FileEntry, 0, len(entries))
	for _, entry := range entries {
		info, err := entry.Info()
		if err != nil {
			continue
		}
		files = append(files, FileEntry{
			Name:    entry.Name(),
			Path:    filepath.Join(absPath, entry.Name()),
			IsDir:   entry.IsDir(),
			Size:    info.Size(),
			ModTime: info.ModTime().Format("2006-01-02 15:04:05"),
			Mode:    info.Mode().String(),
		})
	}

	c.JSON(http.StatusOK, gin.H{"path": absPath, "files": files})
}

func (h *Handler) Mkdir(c *gin.Context) {
	var req struct {
		Path string `json:"path"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid request"})
		return
	}
	absPath, _ := sanitizePath(req.Path)
	if err := os.MkdirAll(absPath, 0755); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"success": true})
}

func (h *Handler) Delete(c *gin.Context) {
	var req struct {
		Path string `json:"path"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid request"})
		return
	}
	absPath, _ := sanitizePath(req.Path)
	if err := os.RemoveAll(absPath); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"success": true})
}

func (h *Handler) Rename(c *gin.Context) {
	var req struct {
		OldPath string `json:"oldPath"`
		NewName string `json:"newName"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid request"})
		return
	}
	absOld, _ := sanitizePath(req.OldPath)
	newPath := filepath.Join(filepath.Dir(absOld), req.NewName)
	if err := os.Rename(absOld, newPath); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"success": true})
}

func (h *Handler) Move(c *gin.Context) {
	var req struct {
		Source string `json:"source"`
		Dest   string `json:"dest"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid request"})
		return
	}
	absSrc, _ := sanitizePath(req.Source)
	absDst, _ := sanitizePath(req.Dest)
	if err := os.Rename(absSrc, absDst); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"success": true})
}

func (h *Handler) Upload(c *gin.Context) {
	path := c.Query("path")
	if path == "" {
		home, _ := os.UserHomeDir()
		path = home
	}
	absPath, _ := sanitizePath(path)

	file, header, err := c.Request.FormFile("file")
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "no file provided"})
		return
	}
	defer file.Close()

	destPath := filepath.Join(absPath, header.Filename)
	out, err := os.Create(destPath)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer out.Close()

	if _, err := io.Copy(out, file); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"success": true, "path": destPath})
}

func (h *Handler) Download(c *gin.Context) {
	path := c.Query("path")
	if path == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "path required"})
		return
	}
	absPath, _ := sanitizePath(path)

	info, err := os.Stat(absPath)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "file not found"})
		return
	}
	if info.IsDir() {
		c.JSON(http.StatusBadRequest, gin.H{"error": "cannot download directory"})
		return
	}

	fileName := filepath.Base(absPath)
	fileName = strings.ReplaceAll(fileName, "\"", "")
	c.Header("Content-Disposition", fmt.Sprintf("attachment; filename=\"%s\"", fileName))
	c.Header("Content-Type", "application/octet-stream")
	c.File(absPath)
}
