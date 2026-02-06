package proxy

import (
	"net/http"
	"net/http/httputil"
	"net/url"
	"strings"
	"sync"
)

type Rule struct {
	ID         string `json:"id"`
	PathPrefix string `json:"pathPrefix"`
	Target     string `json:"target"`
}

type Manager struct {
	mu    sync.RWMutex
	rules []Rule
}

func NewManager() *Manager {
	return &Manager{rules: []Rule{}}
}

func (m *Manager) AddRule(r Rule) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.rules = append(m.rules, r)
}

func (m *Manager) RemoveRule(id string) bool {
	m.mu.Lock()
	defer m.mu.Unlock()
	for i, r := range m.rules {
		if r.ID == id {
			m.rules = append(m.rules[:i], m.rules[i+1:]...)
			return true
		}
	}
	return false
}

func (m *Manager) GetRules() []Rule {
	m.mu.RLock()
	defer m.mu.RUnlock()
	result := make([]Rule, len(m.rules))
	copy(result, m.rules)
	return result
}

func (m *Manager) SetRules(rules []Rule) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.rules = rules
}

func (m *Manager) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	path := r.URL.Path
	for _, rule := range m.rules {
		prefix := "/proxy/" + rule.PathPrefix
		if strings.HasPrefix(path, prefix) {
			target, err := url.Parse(rule.Target)
			if err != nil {
				http.Error(w, "bad proxy target", http.StatusBadGateway)
				return
			}
			proxy := httputil.NewSingleHostReverseProxy(target)
			r.URL.Path = strings.TrimPrefix(path, prefix)
			if r.URL.Path == "" {
				r.URL.Path = "/"
			}
			r.Header.Set("X-Forwarded-Host", r.Host)
			proxy.ServeHTTP(w, r)
			return
		}
	}
	http.Error(w, "no matching proxy rule", http.StatusNotFound)
}
