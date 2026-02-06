package clipboard

import (
	"sync"
	"time"

	"github.com/atotto/clipboard"
)

type Manager struct {
	mu       sync.Mutex
	lastText string
	onChange func(text string)
	stopCh   chan struct{}
}

func NewManager(onChange func(text string)) *Manager {
	return &Manager{
		onChange: onChange,
		stopCh:   make(chan struct{}),
	}
}

func (m *Manager) StartWatching() {
	go func() {
		ticker := time.NewTicker(500 * time.Millisecond)
		defer ticker.Stop()
		for {
			select {
			case <-m.stopCh:
				return
			case <-ticker.C:
				text, err := clipboard.ReadAll()
				if err != nil {
					continue
				}
				m.mu.Lock()
				if text != m.lastText && text != "" {
					m.lastText = text
					m.mu.Unlock()
					if m.onChange != nil {
						m.onChange(text)
					}
				} else {
					m.mu.Unlock()
				}
			}
		}
	}()
}

func (m *Manager) Stop() {
	close(m.stopCh)
}

func (m *Manager) SetText(text string) error {
	m.mu.Lock()
	m.lastText = text
	m.mu.Unlock()
	return clipboard.WriteAll(text)
}

func (m *Manager) GetText() (string, error) {
	return clipboard.ReadAll()
}
