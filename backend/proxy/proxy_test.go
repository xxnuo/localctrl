package proxy

import (
	"testing"
)

func TestAddAndRemoveRule(t *testing.T) {
	m := NewManager()

	m.AddRule(Rule{ID: "1", PathPrefix: "app1/", Target: "http://localhost:3000"})
	m.AddRule(Rule{ID: "2", PathPrefix: "app2/", Target: "http://localhost:4000"})

	rules := m.GetRules()
	if len(rules) != 2 {
		t.Errorf("expected 2 rules, got %d", len(rules))
	}

	if !m.RemoveRule("1") {
		t.Error("should return true for existing rule")
	}

	rules = m.GetRules()
	if len(rules) != 1 {
		t.Errorf("expected 1 rule, got %d", len(rules))
	}

	if m.RemoveRule("999") {
		t.Error("should return false for non-existing rule")
	}
}

func TestSetRules(t *testing.T) {
	m := NewManager()
	m.SetRules([]Rule{
		{ID: "a", PathPrefix: "svc/", Target: "http://localhost:5000"},
	})
	rules := m.GetRules()
	if len(rules) != 1 || rules[0].ID != "a" {
		t.Error("SetRules failed")
	}
}
