package main

import (
	"embed"
	"io/fs"
	"log"
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/xxnuo/localctrl/config"
	"github.com/xxnuo/localctrl/server"
)

//go:embed all:static
var frontendFS embed.FS

func serveFrontend() gin.HandlerFunc {
	stripped, _ := fs.Sub(frontendFS, "static")
	fileServer := http.FileServer(http.FS(stripped))

	return func(c *gin.Context) {
		path := c.Request.URL.Path
		if path == "/" || path == "" {
			path = "/index.html"
		}

		f, err := stripped.Open(path[1:])
		if err != nil {
			f, err = stripped.Open("index.html")
			if err != nil {
				c.Next()
				return
			}
		}
		f.Close()

		fileServer.ServeHTTP(c.Writer, c.Request)
	}
}

func main() {
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("Failed to load config: %v", err)
	}

	srv, err := server.New(cfg)
	if err != nil {
		log.Fatalf("Failed to create server: %v", err)
	}
	defer srv.Close()

	srv.SetStaticHandler(serveFrontend())

	if err := srv.Run(); err != nil {
		log.Fatalf("Server error: %v", err)
	}
}
