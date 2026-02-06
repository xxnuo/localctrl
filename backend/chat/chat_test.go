package chat

import (
	"testing"
)

func TestAddAndHistory(t *testing.T) {
	var received []Message
	mgr := NewManager(func(msg Message) {
		received = append(received, msg)
	})

	mgr.Add("alice", "hello")
	mgr.Add("bob", "hi")

	history := mgr.History()
	if len(history) != 2 {
		t.Errorf("expected 2 messages, got %d", len(history))
	}
	if history[0].Sender != "alice" || history[0].Text != "hello" {
		t.Error("first message mismatch")
	}
	if len(received) != 2 {
		t.Errorf("callback expected 2, got %d", len(received))
	}
}

func TestHistoryLimit(t *testing.T) {
	mgr := NewManager(nil)
	for i := 0; i < 600; i++ {
		mgr.Add("user", "msg")
	}
	history := mgr.History()
	if len(history) != 500 {
		t.Errorf("expected 500 messages (capped), got %d", len(history))
	}
}
