package ws

import (
	"testing"
)

func TestHubControlFlow(t *testing.T) {
	hub := NewHub(nil)

	if hub.ClientCount() != 0 {
		t.Error("initial count should be 0")
	}

	if hub.IsController("none") {
		t.Error("no one should be controller initially")
	}
}

func TestControlGrantMsg(t *testing.T) {
	msg := ControlGrantMsg{
		Type:       MsgControlGrant,
		Granted:    true,
		Controller: "alice",
	}
	if msg.Type != MsgControlGrant {
		t.Error("wrong type")
	}
	if !msg.Granted {
		t.Error("should be granted")
	}
}
