package terminal

import (
	"fmt"
	"io"
	"os"
	"os/exec"
	"runtime"
	"sync"

	"github.com/creack/pty"
)

type Session struct {
	ID     string
	cmd    *exec.Cmd
	ptmx   *os.File
	mu     sync.Mutex
	closed bool
}

type Manager struct {
	mu       sync.Mutex
	sessions map[string]*Session
}

func NewManager() *Manager {
	return &Manager{sessions: make(map[string]*Session)}
}

func (m *Manager) Create(id string) (*Session, error) {
	shell := getDefaultShell()
	cmd := exec.Command(shell)
	cmd.Env = append(os.Environ(), "TERM=xterm-256color")

	ptmx, err := pty.Start(cmd)
	if err != nil {
		return nil, fmt.Errorf("pty start: %w", err)
	}

	sess := &Session{
		ID:   id,
		cmd:  cmd,
		ptmx: ptmx,
	}

	m.mu.Lock()
	m.sessions[id] = sess
	m.mu.Unlock()

	return sess, nil
}

func (m *Manager) Get(id string) *Session {
	m.mu.Lock()
	defer m.mu.Unlock()
	return m.sessions[id]
}

func (m *Manager) Close(id string) {
	m.mu.Lock()
	sess, ok := m.sessions[id]
	if ok {
		delete(m.sessions, id)
	}
	m.mu.Unlock()
	if ok && sess != nil {
		sess.Close()
	}
}

func (m *Manager) CloseAll() {
	m.mu.Lock()
	ids := make([]string, 0, len(m.sessions))
	for id := range m.sessions {
		ids = append(ids, id)
	}
	m.mu.Unlock()
	for _, id := range ids {
		m.Close(id)
	}
}

func (s *Session) Read(p []byte) (int, error) {
	return s.ptmx.Read(p)
}

func (s *Session) Write(p []byte) (int, error) {
	return s.ptmx.Write(p)
}

func (s *Session) WriteTo(w io.Writer) {
	io.Copy(w, s.ptmx)
}

func (s *Session) Resize(rows, cols uint16) error {
	return pty.Setsize(s.ptmx, &pty.Winsize{
		Rows: rows,
		Cols: cols,
	})
}

func (s *Session) Close() {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.closed {
		return
	}
	s.closed = true
	s.ptmx.Close()
	s.cmd.Process.Kill()
	s.cmd.Wait()
}

func getDefaultShell() string {
	if runtime.GOOS == "windows" {
		return "powershell.exe"
	}
	shell := os.Getenv("SHELL")
	if shell == "" {
		return "/bin/sh"
	}
	return shell
}
