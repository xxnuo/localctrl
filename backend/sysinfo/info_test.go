package sysinfo

import (
	"testing"
)

func TestCollect(t *testing.T) {
	info, err := Collect()
	if err != nil {
		t.Fatalf("Collect failed: %v", err)
	}
	if info.Hostname == "" {
		t.Error("hostname should not be empty")
	}
	if info.Arch == "" {
		t.Error("arch should not be empty")
	}
	if info.MemTotal == 0 {
		t.Error("memTotal should not be 0")
	}
}

func TestGetNetworkInterfaces(t *testing.T) {
	ifaces := getNetworkInterfaces()
	if len(ifaces) == 0 {
		t.Skip("no active network interfaces")
	}
	for _, iface := range ifaces {
		if iface.Name == "" || iface.IP == "" {
			t.Error("interface name and IP should not be empty")
		}
	}
}
