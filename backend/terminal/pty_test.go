package terminal

import (
	"runtime"
	"testing"
)

func TestGetDefaultShell(t *testing.T) {
	shell := getDefaultShell()
	if shell == "" {
		t.Error("default shell should not be empty")
	}
	if runtime.GOOS == "windows" {
		if shell != "powershell.exe" {
			t.Errorf("expected powershell.exe on windows, got %s", shell)
		}
	}
}

func TestManagerCreateAndClose(t *testing.T) {
	if runtime.GOOS == "windows" {
		t.Skip("pty not supported on windows in test")
	}

	mgr := NewManager()
	sess, err := mgr.Create("test-1")
	if err != nil {
		t.Fatalf("Create failed: %v", err)
	}
	if sess.ID != "test-1" {
		t.Errorf("expected id test-1, got %s", sess.ID)
	}

	got := mgr.Get("test-1")
	if got == nil {
		t.Error("Get should return session")
	}

	mgr.Close("test-1")
	got = mgr.Get("test-1")
	if got != nil {
		t.Error("Get should return nil after close")
	}
}
