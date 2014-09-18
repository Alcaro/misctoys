//This program sits in the background and listens for a certain keyboard event, and flips the CPU frequency in the power options.
//Win32 only, only tested on 7.

#define _WIN32_WINNT 0x0601
#define INITGUID
#include <windows.h>
#include <powrprof.h>

void SetCPUSpeed(int percent)
{
	GUID* CurrentScheme;
	PowerGetActiveScheme(NULL, &CurrentScheme);
	GUID MaxCpuFreq={0xbc5038f7, 0x23e0, 0x4960, {0x96,0xda,0x33,0xab,0xaf,0x59,0x35,0xec}};
	PowerWriteACValueIndex(NULL, CurrentScheme, &GUID_PROCESSOR_SETTINGS_SUBGROUP, &MaxCpuFreq, percent);
	PowerWriteDCValueIndex(NULL, CurrentScheme, &GUID_PROCESSOR_SETTINGS_SUBGROUP, &MaxCpuFreq, percent);
	PowerSetActiveScheme(NULL, CurrentScheme);
	LocalFree(CurrentScheme);
}

int GetCPUSpeed()
{
	DWORD out;
	DWORD size=sizeof(out);
	GUID* CurrentScheme;
	PowerGetActiveScheme(NULL, &CurrentScheme);
	GUID MaxCpuFreq={0xbc5038f7, 0x23e0, 0x4960, {0x96,0xda,0x33,0xab,0xaf,0x59,0x35,0xec}};
	PowerReadACValue(NULL, CurrentScheme, &GUID_PROCESSOR_SETTINGS_SUBGROUP, &MaxCpuFreq, NULL, (LPBYTE)&out, &size);
	PowerSetActiveScheme(NULL, CurrentScheme);
	LocalFree(CurrentScheme);
	return out;
}

void toggle_speed()
{
	BOOL fast=(GetCPUSpeed()==100);
	fast=!fast;
	SetCPUSpeed(fast ? 100 : 0);
	
	if (fast)
	{
		Beep(1000, 80);
		Beep(1250, 80);
		Beep(1500, 80);
		Beep(2000, 80);
	}
	else
	{
		Beep(2000, 80);
		Beep(1500, 80);
		Beep(1250, 80);
		Beep(1000, 80);
	}
	//Beep(fast ? 1000 : 2000, 200);
	//Beep(fast ? 2000 : 1000, 200);
}

void handle_event(RAWINPUT* input)
{
	if (input->header.dwType==RIM_TYPEKEYBOARD)//unneeded check, we only ask for keyboard; could be relevant later, though.
	{
		//USHORT scan=input->data.keyboard.MakeCode;
		//USHORT vkey=input->data.keyboard.VKey;
		//BOOL down=!(input->data.keyboard.Flags&RI_KEY_BREAK);
		
		if (input->data.keyboard.MakeCode==0x1A && (input->data.keyboard.Flags&RI_KEY_BREAK) && (GetKeyState(VK_LCONTROL)&0x8000))
		{
			toggle_speed();
		}
	}
}

static LRESULT CALLBACK window_proc(HWND hwnd, UINT msg, WPARAM wparam, LPARAM lparam)
{
	if (msg==WM_INPUT)
	{
		UINT size=0;
		GetRawInputData((HRAWINPUT)lparam, RID_INPUT, NULL, &size, sizeof(RAWINPUTHEADER));
		char * data=malloc(size);
		GetRawInputData((HRAWINPUT)lparam, RID_INPUT, data, &size, sizeof(RAWINPUTHEADER));
		
		handle_event((RAWINPUT*)data);
		
		LRESULT result=DefRawInputProc((RAWINPUT**)&data, size, sizeof(RAWINPUTHEADER));
		free(data);
		return result;
	}
	return DefWindowProc(hwnd, msg, wparam, lparam);
}

void InitRawInput()
{
	WNDCLASS wc;
	wc.style=0;
	wc.lpfnWndProc=window_proc;
	wc.cbClsExtra=0;
	wc.cbWndExtra=0;
	wc.hInstance=GetModuleHandle(NULL);
	wc.hIcon=LoadIcon(GetModuleHandle(NULL), MAKEINTRESOURCE(1));
	wc.hCursor=LoadCursor(NULL, IDC_ARROW);
	wc.hbrBackground=GetSysColorBrush(COLOR_3DFACE);
	wc.lpszMenuName=NULL;
	wc.lpszClassName="RawInputClass";
	RegisterClass(&wc);//this could fail if it's already regged, but in that case, the previous registration remains so who cares.
	
	HWND hwnd=CreateWindow("RawInputClass", "RawInputClass", WS_POPUP, 0, 0, 64, 64, HWND_MESSAGE, NULL, GetModuleHandle(NULL), NULL);
	
	RAWINPUTDEVICE device[1];
	//capture all keyboard input
	device[0].usUsagePage=1;
	device[0].usUsage=6;
	device[0].dwFlags=RIDEV_INPUTSINK/*|RIDEV_DEVNOTIFY*/;
	device[0].hwndTarget=hwnd;
	RegisterRawInputDevices(device, 1, sizeof(RAWINPUTDEVICE));
}

int main(int argc, char * argv[])
{
	CreateMutex(NULL, FALSE, "Global\\alcaro-cpulow");
	if (GetLastError()==ERROR_ALREADY_EXISTS)
	{
		Beep(200, 900);
		Sleep(100);
		return 0;
	}
	
	InitRawInput();
	
	WNDCLASS wc;
	wc.style=0;
	wc.lpfnWndProc=window_proc;
	wc.cbClsExtra=0;
	wc.cbWndExtra=0;
	wc.hInstance=GetModuleHandle(NULL);
	wc.hIcon=LoadIcon(GetModuleHandle(NULL), MAKEINTRESOURCE(1));
	wc.hCursor=LoadCursor(NULL, IDC_ARROW);
	wc.hbrBackground=GetSysColorBrush(COLOR_3DFACE);
	wc.lpszMenuName=NULL;
	wc.lpszClassName="RawInputClass";
	RegisterClass(&wc);//this could fail if it's already regged, but in that case, the previous registration remains so who cares.
	
	MSG msg;
	while (GetMessage(&msg, NULL, 0, 0))
	{
		TranslateMessage(&msg);
		DispatchMessage(&msg);
	}
	
	//printf("%i", GetCPUSpeed());
	//if (argv[1])
	//{
	//	int a=atoi(argv[1]);
	//	SetCPUSpeed(a);
	//}
}
