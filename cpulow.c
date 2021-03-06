//This program sits in the background and listens for a certain keyboard event, and flips the CPU frequency in the power options.
//On another keyboard event, it turns off the screen, as if the computer has been inactive for a few minutes. No screensaver because screens no longer need saving.
//Finally, it logs all keyboard events to a file. This file is rotated each time the program is started, and the previous one is kept.
//Win32 only, only tested on 7. Defaults to a key that probably doesn't exist for you, chosen because it does absolutely nothing by default on my machine.

#define _WIN32_WINNT 0x0601
#define INITGUID
#include <windows.h>
#include <powrprof.h>

const GUID MaxCpuFreq={0xbc5038f7, 0x23e0, 0x4960, {0x96,0xda,0x33,0xab,0xaf,0x59,0x35,0xec}};
void SetCPUSpeed(int percent)
{
	GUID* CurrentScheme;
	PowerGetActiveScheme(NULL, &CurrentScheme);
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
	PowerReadACValue(NULL, CurrentScheme, &GUID_PROCESSOR_SETTINGS_SUBGROUP, &MaxCpuFreq, NULL, (LPBYTE)&out, &size);
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
}

void turn_off_monitor()
{
	SendMessage(HWND_BROADCAST, WM_SYSCOMMAND, SC_MONITORPOWER, 2 /*POWER_OFF*/);
}

HANDLE keylog;
MSG msg;
HWND hwndRI; // reusing this window for two completely unrelated tasks makes me a bad person, but who cares

void init_keylog()
{
	MoveFileEx("keylog.bin", "keylog-prev.bin", MOVEFILE_REPLACE_EXISTING);
	keylog=CreateFile("keylog.bin", GENERIC_WRITE, FILE_SHARE_READ, NULL, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
}

char keylogbuf[4096];
int keylogbufpos;

VOID CALLBACK TimerProc(HWND hwnd, UINT uMsg, UINT_PTR idEvent, DWORD dwTime);
void log_key(RAWKEYBOARD* key, DWORD time)
{
	if (keylogbufpos>0 && (!key || sizeof(keylogbuf)-keylogbufpos < sizeof(DWORD)+sizeof(RAWKEYBOARD)))
	{
		DWORD stfu;
		WriteFile(keylog, keylogbuf, keylogbufpos, &stfu, NULL);
		keylogbufpos=0;
	}
	if (key)
	{
		memcpy(keylogbuf+keylogbufpos, &time, sizeof(DWORD)); keylogbufpos+=sizeof(DWORD);
		memcpy(keylogbuf+keylogbufpos, key, sizeof(RAWKEYBOARD)); keylogbufpos+=sizeof(RAWKEYBOARD);
		
		//https://msdn.microsoft.com/en-us/library/windows/desktop/ms644906%28v=vs.85%29.aspx
		//If the hWnd parameter is not NULL and the window specified by hWnd already has a timer
		//with the value nIDEvent, then the existing timer is replaced by the new timer.
		//
		//doesn't matter which window I use, so just pick whatever
		SetTimer(hwndRI, 1, 1000, TimerProc);
	}
}
VOID CALLBACK TimerProc(HWND hwnd, UINT uMsg, UINT_PTR idEvent, DWORD dwTime)
{
	log_key(NULL, 0);
}

MSG msg;
void handle_event(RAWINPUT* input)
{
	if (input->header.dwType==RIM_TYPEKEYBOARD)//unneeded check, we only ask for keyboard; could be relevant later, though.
	{
		//USHORT scan=input->data.keyboard.MakeCode;
		//USHORT vkey=input->data.keyboard.VKey;
		//BOOL down=!(input->data.keyboard.Flags&RI_KEY_BREAK);
		
//printf("%.4X %.4X %.4X %.4X %.8X %.8X\n",
//input->data.keyboard.MakeCode,
//input->data.keyboard.Flags,
//input->data.keyboard.Reserved,
//input->data.keyboard.VKey,
//input->data.keyboard.Message,
//input->data.keyboard.ExtraInformation);
		if (input->data.keyboard.MakeCode==0x1A && (input->data.keyboard.Flags&RI_KEY_E0) && input->data.keyboard.VKey == 0xFF &&
		    (input->data.keyboard.Flags&RI_KEY_BREAK))
		{
			if (GetKeyState(VK_LCONTROL)&0x8000)
			{
				toggle_speed();
			}
			else
			{
				turn_off_monitor();
				Beep(1000, 80);
				Beep(1000, 80);
				Beep(1000, 80);
				Beep(1000, 80);
			}
		}
		log_key(&input->data.keyboard, msg.time);
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
	
	hwndRI=CreateWindow("RawInputClass", "RawInputClass", WS_POPUP, 0, 0, 64, 64, HWND_MESSAGE, NULL, GetModuleHandle(NULL), NULL);
	
	RAWINPUTDEVICE device[1];
	//capture all keyboard input
	device[0].usUsagePage=1;
	device[0].usUsage=6;
	device[0].dwFlags=RIDEV_INPUTSINK/*|RIDEV_DEVNOTIFY*/;
	device[0].hwndTarget=hwndRI;
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
	
	init_keylog();
	InitRawInput();
	
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
