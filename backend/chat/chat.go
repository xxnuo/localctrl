package chat

import (
	"sync"
	"time"

	"github.com/google/uuid"
)

type Message struct {
	ID        string `json:"id"`
	Sender    string `json:"sender"`
	Text      string `json:"text"`
	Timestamp int64  `json:"timestamp"`
}

type Manager struct {
	mu       sync.RWMutex
	messages []Message
	onNew    func(Message)
}

func NewManager(onNew func(Message)) *Manager {
	return &Manager{
		messages: []Message{},
		onNew:    onNew,
	}
}

func (m *Manager) Add(sender, text string) Message {
	msg := Message{
		ID:        uuid.New().String(),
		Sender:    sender,
		Text:      text,
		Timestamp: time.Now().UnixMilli(),
	}
	m.mu.Lock()
	m.messages = append(m.messages, msg)
	if len(m.messages) > 500 {
		m.messages = m.messages[len(m.messages)-500:]
	}
	m.mu.Unlock()
	if m.onNew != nil {
		m.onNew(msg)
	}
	return msg
}

func (m *Manager) History() []Message {
	m.mu.RLock()
	defer m.mu.RUnlock()
	result := make([]Message, len(m.messages))
	copy(result, m.messages)
	return result
}
