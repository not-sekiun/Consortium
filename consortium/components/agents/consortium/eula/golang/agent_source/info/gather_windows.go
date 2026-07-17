package info

import (
	"fmt"
	"syscall"
	"unsafe"

	"golang.org/x/sys/windows"
)

func IsAdmin() bool {
	var sid *windows.SID
	err := windows.AllocateAndInitializeSid(
		&windows.SECURITY_NT_AUTHORITY,
		2,
		windows.SECURITY_BUILTIN_DOMAIN_RID,
		windows.DOMAIN_ALIAS_RID_ADMINS,
		0, 0, 0, 0, 0, 0,
		&sid,
	)
	if err != nil {
		return false
	}
	defer windows.FreeSid(sid)

	token := windows.Token(0)
	member, _ := token.IsMember(sid)
	return member
}

func GetLocale() string {
	const LOCALE_NAME_MAX_LENGTH = 85
	kernel32 := windows.NewLazySystemDLL("kernel32.dll")
	getUserDefaultLocaleName := kernel32.NewProc("GetUserDefaultLocaleName")
	buf := make([]uint16, LOCALE_NAME_MAX_LENGTH)

	returnVal, _, _ := getUserDefaultLocaleName.Call(
		uintptr(unsafe.Pointer(&buf[0])),
		uintptr(LOCALE_NAME_MAX_LENGTH),
	)

	if returnVal == 0 {
		return ""
	}

	return syscall.UTF16ToString(buf)
}

func GetVersion() string {
	version := windows.RtlGetVersion()
	fmt.Println(version.MajorVersion, version.MinorVersion, version.BuildNumber)
	return ""
}
