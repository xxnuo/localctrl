package config

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"log"
	"os"
	"path/filepath"

	"gopkg.in/yaml.v3"
)

type TLSConfig struct {
	Cert string `yaml:"cert"`
	Key  string `yaml:"key"`
}

type DefaultUser struct {
	Username string `yaml:"username"`
	Password string `yaml:"password"`
}

type Config struct {
	Port        int         `yaml:"port"`
	Password    string      `yaml:"password"`
	JWTSecret   string      `yaml:"jwt_secret"`
	DefaultUser DefaultUser `yaml:"default_user"`
	TLS         TLSConfig   `yaml:"tls"`
}

func configDir() string {
	home, _ := os.UserHomeDir()
	return filepath.Join(home, ".localctrl")
}

func ConfigDir() string {
	return configDir()
}

func ConfigPath() string {
	return filepath.Join(configDir(), "config.yaml")
}

func randomString(n int) string {
	b := make([]byte, n)
	rand.Read(b)
	return hex.EncodeToString(b)[:n]
}

func generateDefault() *Config {
	return &Config{
		Port:      2001,
		Password:  randomString(16),
		JWTSecret: randomString(32),
		DefaultUser: DefaultUser{
			Username: "admin",
			Password: randomString(12),
		},
		TLS: TLSConfig{},
	}
}

func Load() (*Config, error) {
	dir := configDir()
	os.MkdirAll(dir, 0700)
	path := ConfigPath()

	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			cfg := generateDefault()
			if saveErr := save(cfg, path); saveErr != nil {
				return nil, fmt.Errorf("failed to save default config: %w", saveErr)
			}
			log.Println("===========================================")
			log.Println("  Generated default configuration")
			log.Printf("  Config: %s", path)
			log.Printf("  Access Password: %s", cfg.Password)
			log.Printf("  Admin User: %s", cfg.DefaultUser.Username)
			log.Printf("  Admin Password: %s", cfg.DefaultUser.Password)
			log.Println("===========================================")
			return cfg, nil
		}
		return nil, fmt.Errorf("failed to read config: %w", err)
	}

	var cfg Config
	if err := yaml.Unmarshal(data, &cfg); err != nil {
		return nil, fmt.Errorf("failed to parse config: %w", err)
	}

	if cfg.Port == 0 {
		cfg.Port = 2001
	}
	if cfg.JWTSecret == "" {
		cfg.JWTSecret = randomString(32)
	}

	return &cfg, nil
}

func save(cfg *Config, path string) error {
	data, err := yaml.Marshal(cfg)
	if err != nil {
		return err
	}
	return os.WriteFile(path, data, 0600)
}
