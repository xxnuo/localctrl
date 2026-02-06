package main

import (
	"log"

	"github.com/xxnuo/localctrl/config"
	"github.com/xxnuo/localctrl/server"
)

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

	if err := srv.Run(); err != nil {
		log.Fatalf("Server error: %v", err)
	}
}
