//This program takes a key log from cpulow and prints the text entered.
//Should be easily portable to everything, but since the parent is Win32 only, I don't care.
//Also hardcoded to decoding according to Swedish keyboard layout, into the codepage 850 (Windows console) charset.
//It works for me, that's all I care about.

#define _WIN32_WINNT 0x0501
#include <windows.h>
#include <stdio.h>
#include <stdbool.h>
#include <ctype.h>

//typedef struct tagRAWKEYBOARD {
//  USHORT MakeCode;
//  USHORT Flags;
//  USHORT Reserved;
//  USHORT VKey;
//  UINT   Message;
//  ULONG  ExtraInformation;
//} RAWKEYBOARD, *PRAWKEYBOARD, *LPRAWKEYBOARD;

FILE* outfile;
char outbuf[4096];
int outbufpos;
void out(char ch)
{
	if (ch) outbuf[outbufpos++]=ch;
	if (outbufpos==sizeof(outbuf) || !ch)
	{
		fwrite(outbuf, 1,outbufpos, outfile);
		outbufpos=0;
	}
}

int main(int argc, char * argv[])
{
	outfile=stdout;
	
	FILE* raw=fopen(argv[1] ? argv[1] : "keylog.bin", "rb");
	typedef struct event_t {
		DWORD time; // timestamp is in milliseconds, likely since device boot
		RAWKEYBOARD key;
	} event;
	fseek(raw, 0, SEEK_END);
	int len=ftell(raw)/sizeof(event);
	event* evs=malloc(len*sizeof(event));
	fseek(raw, 0, SEEK_SET);
	fread(evs, sizeof(event),len, raw);
	
	bool* st_vk=calloc(65536,1);
	bool* st_sc=calloc(65536,1);
	
	//keymaps: [altgr*2 + shift][vkey];
	static char keymaps[4][0x100]={};
	memset(keymaps, 0, sizeof(keymaps));
	
	for (int i='A';i<='Z';i++)
	{
		keymaps[0][i]=tolower(i);
		keymaps[1][i]=i;
	}
	for (int i='0';i<='9';i++)
	{
		keymaps[0][i]=i;
	}
	memcpy(&keymaps[1]['0'], "=!\"#\0%&/()", 10);
	keymaps[0][' ']=' ';
	keymaps[1][' ']=' ';
	
	keymaps[2]['2']='@';
	keymaps[2]['4']='$';
	keymaps[2]['7']='{';
	keymaps[2]['8']='[';
	keymaps[2]['9']=']';
	keymaps[2]['0']='}';
	
	keymaps[0][VK_OEM_PLUS]='+'; keymaps[1][VK_OEM_PLUS]='?'; keymaps[2][VK_OEM_PLUS]='\\';
	keymaps[0][VK_OEM_COMMA]=','; keymaps[1][VK_OEM_COMMA]=';';
	keymaps[0][VK_OEM_MINUS]='-'; keymaps[1][VK_OEM_MINUS]='_';
	keymaps[0][VK_OEM_PERIOD]='.'; keymaps[1][VK_OEM_PERIOD]=':';
	keymaps[0][VK_OEM_2]='\''; keymaps[1][VK_OEM_2]='*';
	keymaps[0][VK_OEM_3]=0x94; keymaps[1][VK_OEM_3]=0x99; //ö
	keymaps[0][VK_OEM_6]=0x86; keymaps[1][VK_OEM_6]=0x8F; //å
	keymaps[0][VK_OEM_7]=0x84; keymaps[1][VK_OEM_7]=0x8E; //ä
	keymaps[0][VK_OEM_102]='<'; keymaps[1][VK_OEM_102]='>'; keymaps[2][VK_OEM_102]='|';
	
	keymaps[0][VK_RETURN]=0x14;//¶
	keymaps[1][VK_RETURN]=0x14;
	keymaps[0][VK_BACK]=0x1B;//<-
	keymaps[1][VK_BACK]=0x1B;
	keymaps[0][VK_TAB]=0x1A;//->
	keymaps[1][VK_TAB]=0x1A;
	
	keymaps[0][VK_LEFT]=0x11;
	keymaps[0][VK_UP]=0x1E;
	keymaps[0][VK_RIGHT]=0x10;
	keymaps[0][VK_DOWN]=0x1F;
	
	keymaps[0][VK_SHIFT]=-1;
	keymaps[1][VK_SHIFT]=-1;
	keymaps[2][VK_SHIFT]=-1;
	keymaps[3][VK_SHIFT]=-1;
	keymaps[0][VK_MENU]=-1;
	keymaps[1][VK_MENU]=-1;
	keymaps[2][VK_MENU]=-1;
	keymaps[3][VK_MENU]=-1;
	
	for (int i=0;i<len;i++)
	{
		event* ev=&evs[i];
		bool down=(!(ev->key.Flags&RI_KEY_BREAK));
		
		if (down)
		{
			int vk=ev->key.VKey;
			int sc=ev->key.MakeCode;
			bool shift=(st_vk[VK_SHIFT]);
			
			//can't differentiate between alt and altgr
			//there are the E0/E1 bits in Flags, but they're not in st_vk/sc
			//but nobody types stuff while holding alt anyways. except alt-f4 and that is not part of your password.
			bool altgr=(st_vk[VK_MENU]);
			
			int ch=0;
			if (vk<=0x100) ch=keymaps[altgr*2+shift][vk];
			if (ch==0) ch=0xDB;//in codepage 850, this is U+2588 █
			if (ch!=-1) out(ch);
		}
		//printf("\tvk=%.2X sc=%.2X dn=%i\n",ev->key.VKey,ev->key.MakeCode, down);
//printf("\t%i %.4X %.4X %.4X %.4X %.8X %.8X\n",
//ev->time,
//ev->key.MakeCode,
//ev->key.Flags,
//ev->key.Reserved,
//ev->key.VKey,
//ev->key.Message,
//ev->key.ExtraInformation);
		
		st_vk[ev->key.VKey]=down;
		st_sc[ev->key.MakeCode]=down;
	}
	
	out(0);
}
