#!/usr/bin/env python3

# Pipe any text to this program, and it will replace every GUID it finds with its name, if known.
# For example, an input of
#  CoCreateInstance({e436ebb3-524f-11ce-9f53-0020af0ba770}, NULL, 1, {56a868a9-0ad4-11ce-b03a-0020af0ba770}, 0x4150f060)
# will return
#  CoCreateInstance(CLSID_FilgraphManager, NULL, 1, IID_IGraphBuilder, 0x4150f060)
# Alternatively, you can pass one or more GUIDs as arguments.
# can't put that example in argparse's epilog, it word wraps things in weird ways

# guidbox.bin is sourced from
# https://winlibs.com/
# https://dl.winehq.org/wine/source/
# https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/
# https://www.microsoft.com/en-us/download/details.aspx?id=6812
# there are also GUID lists at
# https://hexacorn.com/d/guids.txt
# https://gist.github.com/stevemk14ebr/af8053c506ef895cd520f8017a81f913
# but I chose to not use them, due to unclear sourcing and occasional dubious entries

import os, sys, re, argparse, uuid, binascii, struct

parser = argparse.ArgumentParser(prog='guidfilt', description='replaces GUIDs in input with their names')
parser.add_argument('args', nargs='*', default=['-'])
parser.add_argument('-b', '--guidbox', default=os.path.dirname(os.path.realpath(__file__))+'/guidbox.bin')
parser.add_argument('-c', '--create', action='store_true')
parser.add_argument('-d', '--dump', action='store_true')
args = parser.parse_args()

def regex_backwards(exp:str):
	def stringify_literal_char(ch):
		if chr(ch).isalnum(): return chr(ch)
		else: return '\\x'+hex(ch)[2:]
	def stringify(ast):
		return ''.join(stringify_elem(*e) for e in ast)
	def stringify_elem(ty, body):
		c = re._constants
		if False: pass
		elif ty == c.AT:
			if body == c.AT_BEGINNING: return '^'
			if body == c.AT_END: return '$'
			if body == c.AT_BOUNDARY: return '\\b'
			assert False, str(body)
		elif ty == c.LITERAL:
			return stringify_literal_char(body)
		elif ty == c.NOT_LITERAL:
			return '[^'+stringify_literal_char(body)+']'
		elif ty == c.BRANCH:
			return '(?:' + '|'.join(stringify(e) for e in body[1]) + ')'
		elif ty == c.ANY:
			return '.'
		elif ty == c.IN:
			def stringify_ccls(ty,body):
				if ty == c.LITERAL:
					return stringify_literal_char(body)
				elif ty == c.CATEGORY and body == c.CATEGORY_WORD:
					return '\\w'
				elif ty == c.CATEGORY and body == c.CATEGORY_SPACE:
					return '\\s'
				elif ty == c.CATEGORY and body == c.CATEGORY_NOT_SPACE:
					return '\\S'
				else:
					assert False, str(ty)+str(body)
			return '[' + ''.join(stringify_ccls(*e) for e in body) + ']'
		elif ty == c.SUBPATTERN:
			return '(' + stringify(body[3]) + ')'
		elif ty in (c.MIN_REPEAT, c.MAX_REPEAT, c.POSSESSIVE_REPEAT):
			m,n,body = body
			ret = '(?:'+stringify(body)+')'
			tail = '{'+str(m)+','
			if n != c.MAXREPEAT: tail += str(n)
			tail += '}'
			if ty == c.MIN_REPEAT: tail += '?'
			if ty == c.POSSESSIVE_REPEAT: tail += '+'
			return ret+tail
		else:
			assert False, str(ty)+str(body)
	
	ast = re._parser.parse(exp, 0).data
	exp2 = stringify(ast)
	ast2 = re._parser.parse(exp2, 0).data
	assert str(ast) == str(ast2)
	
	def reverse(ast):
		return [ reverse_elem(*e) for e in ast[::-1] ]
	def reverse_elem(ty, body):
		c = re._constants
		if ty in ( c.LITERAL, c.NOT_LITERAL, c.ANY, c.IN ):
			return ( ty, body )
		elif ty == c.AT:
			if body == c.AT_BEGINNING: return ( c.AT, c.AT_END )
			if body == c.AT_END: return ( c.AT, c.AT_BEGINNING )
			return ( c.AT, body )
		elif ty == c.BRANCH:
			return ( c.BRANCH, ( None, [ reverse(e) for e in body[1] ] ) )
		elif ty == c.SUBPATTERN:
			return ( c.SUBPATTERN, ( body[0], body[1], body[2], reverse(body[3]) ) )
		elif ty in (c.MIN_REPEAT, c.MAX_REPEAT, c.POSSESSIVE_REPEAT):
			return ( ty, ( body[0], body[1], reverse(body[2]) ) )
		else:
			assert False, str(ty)+str(body)
	
	exp3 = stringify(reverse(reverse(ast)))
	ast3 = re._parser.parse(exp3, 0).data
	assert str(ast) == str(ast3)
	
	return stringify(reverse(ast))


#########################
# Finding GUIDs in text #
#########################

re_dashed_guid = '[0-9A-Fa-f]{8}-(?:[0-9A-Fa-f]{4}-){3}[0-9A-Fa-f]{12}'
re_0x_guid = '0[xX][0-9A-Fa-f]{5,8}L?,\s*0(?:[xX][0-9A-Fa-f]{2,4})?,\s*0(?:[xX][0-9A-Fa-f]{2,4})?' + ',\s*0(?:[xX][0-9A-Fa-f]{1,3})?'*8
re_braced_0x_guid = '0[xX][0-9A-Fa-f]{6,8}L?,\s*0(?:[xX][0-9A-Fa-f]{2,4})?,\s*0(?:[xX][0-9A-Fa-f]{2,4})?,\s*{\s*0(?:[xX][0-9A-Fa-f]{1,2})?' + ',\s*0(?:[xX][0-9A-Fa-f]{1,2})?'*7 + '\s*}'
# braced_0x_guid will consume a {} around it if one exists, but 0x_guid will not

def parse_0x_guid(text):
	parts = text.split(",")
	parts = [p.replace("{","").replace("}","").replace("L","").lower().strip() for p in parts]
	assert len(parts)==11 and all(p=='0' or p.startswith('0x') for p in parts)
	for i,partlen in enumerate((8,4,4,2,2,2,2,2,2,2,2)):
		parts[i] = ("00000000"+parts[i][2:])[-partlen:]
	guid = ''.join(parts)
	return uuid.UUID(guid)

# Returns list(tuple( start, end, guid, anchor )), sorted in ascending order.
# The anchor is one of re_dashed_guid, re_0x_guid and re_braced_0x_guid.
def find_guids(text:str) -> list[tuple[int,int,uuid.UUID]]:
	ret = []
	for m in re.finditer(re_0x_guid, text):
		st = m.start(0)
		en = m.end(0)
		ret.append(( st, en, parse_0x_guid(text[st:en]), re_0x_guid ))
	for m in re.finditer(re_braced_0x_guid, text):
		st = m.start(0)
		en = m.end(0)
		try_st = st
		try_en = en
		while text[try_st-1].isspace():
			try_st -= 1
		while text[try_en].isspace():
			try_en += 1
		if text[try_st-1] == '{' and text[try_en] == '}':
			st = try_st-1
			en = try_en+1
		ret.append(( st, en, parse_0x_guid(text[st:en]), re_braced_0x_guid ))
	for m in re.finditer(r'-[0-9A-Fa-f]{12}', text):
		st = m.start(0)-len("12345678-1234-1234-1234")
		en = m.end(0)
		if re.fullmatch(re_dashed_guid, text[st:en]):
			if text[st-1] == '{' and text[en] == '}':
				st -= 1
				en += 1
			ret.append(( st, en, uuid.UUID(text[st:en]), re_dashed_guid ))
	return sorted(ret)

rules = [
	r'(?:DEFINE_\w*GUID|EXTERN_GUID|OUR_GUID_ENTRY|DEFINE_KNOWN_FOLDER)\s*\(\s*(\w+)\s*,\s*'+re_0x_guid+r'\s*\)',
	(r'__CRT_UUID_DECL\s*\(\s*(\w+)\s*,\s*'+re_0x_guid+r'\s*\)', '<IID_'),
	r'(DEFINE_PROPERTYKEY|DEFINE_DEVPROPKEY)\(\s*(\w+)\s*,\s*'+re_0x_guid+r'\s*,\s*\d',
	r'DEFINE_API_PKEY\(\s*(\w+)\s*,\s*\w+\s*,\s*'+re_0x_guid+r'\s*,\s*\d',
	r'MIDL_DEFINE_GUID\(\w+,\s*(\w+)\s*,\s*'+re_0x_guid+r'\s*\)',
	r'DEFINE_GUIDSTRUCT\("'+re_dashed_guid+r'",\s*(\w+)\)',
	r'CROSS_PLATFORM_UUIDOF\((\w+), "'+re_dashed_guid+r'"\)',
	(r'DWRITE_BEGIN_INTERFACE\((\w+), "'+re_dashed_guid+r'"\)', 'IID_'),
	(r'(?:MIDL_INTERFACE|DECLARE_INTERFACE)\s*\("'+re_dashed_guid+r'"\)\s*(\w+)', 'IID_'),
	(r'(?:class|struct)\s+DECLSPEC_UUID\s*\("'+re_dashed_guid+r'"\)\s*([^I\s]\w*|ImageTranscode)', 'CLSID_'),
	(r'typedef\s+DECLSPEC_UUID\s*\("'+re_dashed_guid+r'"\)\s*(\w+)Enum\b', 'IID_Enum'),
	r'typedef\s+DECLSPEC_UUID\s*\("'+re_dashed_guid+r'"\)\s*(enum \w+)',
	(r'interface DECLSPEC_UUID\(\s*"'+re_dashed_guid+r'"\s*\)\s*(?:DECLSPEC_NOVTABLE\s*)?(\w+)', 'IID_'),
	(r'(?:class|struct)\s+__declspec\(uuid\("'+re_dashed_guid+r'"\)\)\s*(?:__declspec\(novtable\)\s*)?(I[A-Z]\w*)', 'IID_'),
	(r'class\s+__declspec\(uuid\("'+re_dashed_guid+r'"\)\)\s*([^I\s]\w*)', 'CLSID_'),
	(r'class\s+__declspec\(uuid\("'+re_dashed_guid+r'"\)\)\s*(\w+)\b[\s\S]+\b\1\(', 'CLSID_'),
	r'typedef\s*\[[^\]]*uuid\('+re_dashed_guid+'\)[^\]]*\]\s*(?!enum)\w+\s*(\w+)',
	r'typedef\s*\[[^\]]*uuid\('+re_dashed_guid+'\)[^\]]*\]\s*(enum\s+\w+)',
	(r'\[[^\]]*uuid\(\s*'+re_dashed_guid+'\s*\)[^\]]*\]\s*interface\s*(\w+)', 'IID_'),
	(r'\[[^\]]*uuid\('+re_dashed_guid+'\)[^\]]*\]\s*coclass\s+(\w+)', 'CLSID_'),
	(r'\[[^\]]*uuid\('+re_dashed_guid+'\)[^\]]*\]\s*library\s+(\w+)', 'LIBID_'),
	(r'\[[^\]]*uuid\('+re_dashed_guid+'\)[^\]]*\]\s*delegate\s+\w+\s+(\w+)', 'IID_'),
	(r'(?:LOCAL|REMOTED)_INTERFACE\('+re_dashed_guid+'\)\s*(?:#endif\s*)?interface\s*(\w+)', 'IID_'),
	(r'DECLARE_INTERFACE_IID_\s*\(\s*(\w+),\s*\w+,\s*"'+re_dashed_guid+'"\s*\)', 'IID_'),
	(r'DECLARE_INTERFACE_IID\s*\(\s*(\w+),\s*"'+re_dashed_guid+'"\s*\)', 'IID_'),
	r'#define\s+(?:STATIC_)?(\w+?)\s+'+re_dashed_guid+r'\s*\n',
	r'#define\s+(?:STATIC_)?(\w+?)\s+\(?\s*L?"'+re_dashed_guid+r'"\s*\)?\s*\n',
	r'#define\s+(?:STATIC_)?(\w+?)\s+(?:TEXT|OLESTR)\("\{?'+re_dashed_guid+r'\}?"\)\n',
	r'#define\s+(?:STATIC_)?(\w+?)\s+uuid\('+re_dashed_guid+r'\)\n',
	r'#define\s+(?:STATIC_)?(\w+?)\s+\{?\s*'+re_0x_guid+r'\s*\}?\s*\n',
	r'#define\s+(?:STATIC_)?(\w+?)\s+\{?\s*'+re_braced_0x_guid+r'\s*\}?;?\s*\n',
	r'#define\s+(?:STATIC_)?(\w+?)\s+__uuidof\(\(struct __declspec\(uuid\("'+re_dashed_guid+r'"\)\)',
	r'\b(?:GUID|UUID|CLSID|IID)\s+(?:OLEDBDECLSPEC\s+|DECLSPEC_SELECTANY\s+)?_?(\w+?)\s*=\s*'+re_braced_0x_guid+r';',
	r'\b(?:GUID|UUID|CLSID|IID)\s+(?:OLEDBDECLSPEC\s+|DECLSPEC_SELECTANY\s+)?_?(\w+?)\s*=\s*\{?'+re_0x_guid+r'\}?;',
	r'\bPROPERTYKEY\s+(\w+)\s*=\s*\{\s*'+re_braced_0x_guid+r'\s*,',
	r'\bPROPERTYKEY\s+(\w+)\s*=\s*\{\s*\{\s*'+re_0x_guid+r'\s*\}\s*,',
	r'\w+\s+(\w+)\s*=\s*L?"\{?'+re_dashed_guid+r'\}?";',
	r'Reserved GUIDS for our use[\s\S]*//\s*'+re_dashed_guid+r'\s+(\w+)\s*\n',
	(r'DMANIP_CLSID\(\s*(\w+),\s*\{?\s*'+re_dashed_guid, 'CLSID_'),
	(r'DMANIP_CLSID\(\s*(\w+),\s*\{[^}]+\},\s*"[^"]+",\s*\{?\s*'+re_dashed_guid, 'CLSID_Microsoft_'),
	(r'DMANIP_INTERFACE\(\s*'+re_dashed_guid+r',\s*[^,]+,\s*"[^"]+"\)\s*interface (\w+)', 'IID_'),
	(r'DMANIP_INTERFACE\(\s*[^,]+,\s*'+re_dashed_guid+r',\s*"[^"]+"\)\s*interface (\w+)', 'IID_Microsoft_'), # IID_Microsoft_ isn't a thing, just guessing
	(r'DMANIP_LIBRARY\(\s*'+re_dashed_guid+r',\s*[^,]+,\s*"[^"]+"\)\s*library (\w+)', 'LIBID_'),
	(r'DMANIP_LIBRARY\(\s*[^,]+,\s*'+re_dashed_guid+r',\s*"[^"]+"\)\s*library (\w+)', 'LIBID_Microsoft_'),
	(r'DMANIP_(?:INTEROP_)?CLASS\(\s*'+re_dashed_guid+r',\s*[^,]+,\s*"[^"]+",\s*(\w+)\)', 'CLSID_'),
	(r'DMANIP_(?:INTEROP_)?CLASS\(\s*[^,]+,\s*'+re_dashed_guid+r',\s*"[^"]+",\s*(\w+)\)', 'CLSID_Microsoft_'),
	(r'IMMPID_START_LIST\((\w+),0x.000,"'+re_dashed_guid+r'"\)', 'tagIMMPID_', '_STRUCT'),
	r'template <>\s*struct __declspec\(uuid\("'+re_dashed_guid+r'"\)\)\s*(\w+[\s\S]+?)\s+:',
	(r'> inline constexpr guid (?:generic_)?guid_v<(?:\w+::)*(\w+(?:<[\w\s,]+>)?)>'+re_braced_0x_guid+r';', 'IID_'),
	(r'()#define DEFINE_PCI_DEVICE_DEVPKEY\(\w+, \w+\)\s*DEFINE_DEVPROPKEY\s*\(\(\w+\), '+re_0x_guid, 'DEVPKEY_PciDevice'),
	(r'()#define DEFINE_PCI_ROOT_BUS_DEVPKEY\(\w+, \w+\)\s*DEFINE_DEVPROPKEY\s*\(\(\w+\), '+re_0x_guid, 'DEVPKEY_PciRootBus'),
]

anchors = [ re_dashed_guid, re_0x_guid, re_braced_0x_guid ]

# { str : list[tuple[ rhs, lhs backwards, prefix, suffix ] ] }
rules_for = { a:[] for a in anchors }
for rule in rules:
	if isinstance(rule, str):
		rule = ( rule, '' )
	if len(rule) == 2:
		rule,prefix = rule
		suffix = ''
	else:
		rule,prefix,suffix = rule
	anchor_match = [a in rule for a in anchors]
	assert sum(anchor_match) == 1
	anchor = anchors[anchor_match.index(True)]
	lhs,rhs = rule.split(anchor)
	rules_for[anchor].append(( re.compile(rhs), re.compile(regex_backwards(lhs)), prefix, suffix ))

# The name can be None. The same GUID may show up multiple times. The return value is not sorted.
def find_guid_names(text) -> list[tuple[uuid.UUID,str]]:
	ret = []
	# GUID_BUILDER takes arguments without 0x, so none of the anchor regexes find them
	# just hardcode them instead
	for m in re.finditer(r'GUID_BUILDER\((\w+),([0-9A-Fa-f,]+)\)', text):
		ret.append(( uuid.UUID(m[2].replace(",","")), m[1] ))
	for m in re.finditer(r'OUR_GUID_ENTRY\((\w+),\s*\'(....)\',([0-9A-Fa-fx, ]+)\)', text):
		guid = m[2].encode("ascii").hex()
		guid += m[3].replace("0x","").replace(",","").replace(" ","")
		ret.append(( uuid.UUID(guid), m[1] ))
	
	text = text.replace('\\\r\n','   ').replace('\\\n','  ').replace('\r','\n')
	
	comment_pieces = []
	src_pieces = []
	last_end = 0
	for m in re.finditer(r'(?://.*?\n|/\*.*?\*/)', text):
		src_pieces.append(text[last_end:m.start()])
		comment_pieces.append(m[0])
		last_end = m.end()
	src_pieces.append(text[last_end:])
	text = ' '.join(src_pieces + comment_pieces)
	
	guids = find_guids(text)
	text_rev = text[::-1]
	
	for st, en, guid, anchor in guids:
		name = None
		for rhs, lhs, prefix, suffix in rules_for[anchor]:
			mr = rhs.match(text, en)
			if not mr: continue
			ml = lhs.match(text_rev, len(text)-st)
			if not ml: continue
			
			if len(mr.groups()) == 1:
				name = prefix+mr[1]+suffix
			else:
				name = prefix+ml[1][::-1]+suffix
			break
		if name == 'IID_IUnknown':  # there's an incorrect one in mingw ddk/punknown.h
			guid = uuid.UUID('00000000-0000-0000-c000-000000000046')
		if guid == uuid.UUID('00000000-0000-0000-0000-000000000000'):
			name = 'GUID_NULL'  # this one has five different names
		ret.append(( guid, name ))
	
	return ret


####################################
# Finding GUIDs in MSVC .lib files #
####################################

def strnul_from(by, off):
	return by[off : by.index(b'\x00', off)]

def parse_ar_file(by):
	assert by.startswith(b"!<arch>\n")
	by = memoryview(by)
	by = by[len(b"!<arch>\n"):]
	
	raw_files = []
	files = []
	filename_list = None
	
	while by:
		fn = bytes(by[0:16]).strip()
		# ignore file time at by[16:28]
		# ignore file owner at by[28:34]
		# ignore file group at by[34:40]
		# ignore file type at by[40:48]
		sz = int(bytes(by[48:58]).strip())
		assert by[58:60] == b'`\n'
		
		body = by[60 : 60+sz]
		raw_files.append(( fn, body ))
		by = by[60+sz+(sz&1):]
		
		if fn == b'//':
			filename_list = bytes(body).replace(b"\n",b"\0")
		if re.fullmatch(b'/\d+', fn):
			fn_off = int(fn[1:])
			fn = strnul_from(filename_list, fn_off)
		if fn != b'/' and fn != b'//':
			files.append(( fn, body ))
	
	return files

def guids_from_coff_obj(by) -> list[tuple[uuid.UUID,str]]:
	ret = []
	by = bytes(by)
	machine,nsections,timestamp,symtab_ptr,symtab_sz,opthdr,characteristics = struct.unpack("<HHIIIHH", by[:20])
	
	sections = by[20 : 20+nsections*40]
	sections = list(struct.iter_unpack("<8sIIIIIIHHI", sections))
	
	guid_type_idx = []
	have_debug = False
	# the PDB format documentation is extremely weak and scattered
	# https://lists.llvm.org/pipermail/llvm-dev/2015-October/091847.html
	for s in sections:
		s_name,vsize,vaddr,raw_size,raw_ptr,reloc_p,linenum_p,reloc_num,linenum_num,characteristics = s
		body = by[raw_ptr : raw_ptr+raw_size]
		if s_name == b'.debug$T':
			have_debug = True
			# https://github.com/llvm/llvm-project/blob/main/llvm/include/llvm/DebugInfo/CodeView/CodeViewTypes.def
			assert body.startswith(b"\x04\x00\x00\x00")
			body = body[4:]
			type_idx = 0x1000
			while body:
				l,ty = struct.unpack("<HH",body[:4])
				ty_body = body[4:l+2]
				if ty == 0x1505: # LF_STRUCTURE
					# structure explained by ClassRecord ctor at
					# https://github.com/llvm/llvm-project/blob/main/llvm/include/llvm/DebugInfo/CodeView/TypeRecord.h
					# (TypeIndex is uint32, StringRef is strnul, everything else is uint16)
					# (even Size is uint16 - maybe there's some way to specify extended size, but GUID obviously doesn't need that)
					ty_name = strnul_from(ty_body, 18)
					if ty_name == b"_GUID" or ty_name == b"_IID":  # for some reason, one specific object file names it _IID and not _GUID
						guid_type_idx.append(type_idx)
				assert l+2 <= len(body)
				body = body[l+2:]
				type_idx += 1
	
	guid_names = set()
	
	for s in sections:
		# https://github.com/llvm/llvm-project/blob/main/llvm/docs/PDB/CodeViewSymbols.rst
		# https://github.com/llvm/llvm-project/blob/main/llvm/include/llvm/DebugInfo/CodeView/CodeViewSymbols.def
		# https://github.com/llvm/llvm-project/blob/main/llvm/include/llvm/DebugInfo/CodeView/CodeView.h
		s_name,vsize,vaddr,raw_size,raw_ptr,reloc_p,linenum_p,reloc_num,linenum_num,characteristics = s
		body = by[raw_ptr : raw_ptr+raw_size]
		if s_name == b'.debug$S':
			have_debug = True
			assert body.startswith(b"\x04\x00\x00\x00")
			body = body[4:]
			while body:
				major_type,size1 = struct.unpack("<II",body[:8])
				if major_type == 0xF1:  # DebugSubsectionKind::Symbols
					sub_body = body[8:8+size1]
					while sub_body:
						size2,minor_type = struct.unpack("<HH",sub_body[:4])
						if minor_type == 0x110D: # S_GDATA32
							# structure explained by DataSym members at
							# https://github.com/llvm/llvm-project/blob/main/llvm/include/llvm/DebugInfo/CodeView/SymbolRecord.h
							type_idx,dataoffs,segment = struct.unpack("<IIH",sub_body[4:14])
							if type_idx in guid_type_idx:
								guid_names.add(strnul_from(sub_body,14))
						assert size2+2 <= len(sub_body)
						sub_body = sub_body[size2+2:]
				while size1&3: size1 += 1
				assert size1+8 <= len(body)
				body = body[size1+8:]
	
	symtab = by[symtab_ptr : symtab_ptr+symtab_sz*18]
	symtab = list(struct.iter_unpack("<8sIHHBB", symtab))
	string_tab = by[symtab_ptr+symtab_sz*18:]
	i = 0
	while i < len(symtab):
		name,value,sect_num,ty,cls,num_aux = symtab[i]
		if name.startswith(b'\x00\x00\x00\x00'):
			name = strnul_from(string_tab, struct.unpack("<II",name)[1])
		else:
			name = name.rstrip(b"\x00")
		if cls == 2:  # IMAGE_SYM_CLASS_EXTERNAL - means visible beyond this translation unit
			s_name,vsize,vaddr,raw_size,raw_ptr,reloc_p,linenum_p,reloc_num,linenum_num,characteristics = sections[sect_num-1]
			# https://learn.microsoft.com/en-us/windows/win32/debug/pe-format#section-flags
			if name in guid_names:
				assert raw_size == 16
				ret.append(( uuid.UUID(bytes_le=by[raw_ptr : raw_ptr+16]), name.decode("ascii") ))
			elif name.startswith(b"IID_") or name.startswith(b"CLSID_") or name.startswith(b"GUID_"):
				# if there's anything starting with IID_, CLSID_ or GUID_ which isn't GUID type,
				# then either debug info is missing, or I want to know more about that symbol
				assert not have_debug
				assert raw_size == 16
				ret.append(( uuid.UUID(bytes_le=by[raw_ptr : raw_ptr+16]), name.decode("ascii") ))
		i += 1 + num_aux
	return ret

def guids_from_lib(by) -> list[tuple[uuid.UUID,str]]:
	ret = []
	for fn,by in parse_ar_file(by):
		if fn.lower().endswith(b".obj"):
			ret += guids_from_coff_obj(by)
	return ret


########################
# Multiple input files #
########################

def guids_from_files(fns):
	assert fns
	named_guids = []
	def process_file(fn):
		by = open(fn, "rb").read()
		if by.startswith(b"!<arch>\n"):
			named_guids.extend(guids_from_lib(by))
		else:
			try:
				named_guids.extend(find_guid_names(by.decode("utf-8")))
			except UnicodeDecodeError:
				named_guids.extend(find_guid_names(by.decode("latin-1")))
	
	for path in fns:
		if os.path.isdir(path):
			for dirpath, dirnames, filenames in os.walk(path):
				for filename in filenames:
					process_file(dirpath+"/"+filename)
		else:
			process_file(path)
	
	return named_guids

def decide_guid_names(named_guids):
	name_to_guids = {}
	guid_to_names = {}
	for guid,name in named_guids:
		lst = guid_to_names.setdefault(guid, [])
		if name and name not in lst:
			lst.append(name)
		if name is not None:
			lst = name_to_guids.setdefault(name, [])
			if guid not in lst:
				lst.append(guid)
	
	for guid,names in guid_to_names.items():
		if any(name.startswith("<") for name in names):
			if any(not name.startswith("<") for name in names):
				names[:] = [ name for name in names if not name.startswith("<") ]
			else:
				names[:] = [ name[1:] for name in names ]
		if len(names) >= 2 and all(name.startswith("PKEY_") for name in names):
			a_name = names[0]
			l = 0
			while all(l < len(n) and n[l] == a_name[l] for n in names):
				l += 1
			l -= 1
			while a_name[l] != '_':
				l -= 1
			if l > 5:
				names.clear()
				names.append(a_name[:l])
		if len(names) >= 2:
			min_uses = min(len(name_to_guids[n]) for n in names)
			names[:] = [n for n in names if len(name_to_guids[n]) == min_uses]
	
	named_guids = [( guid,names[0] ) for guid,names in guid_to_names.items() if names]
	return named_guids


####################
# guidbox handlers #
####################

guid_hash_buckets = 65536
def guid_hash(guid):
	# why is crc32 in binascii and zlib, and not in hashlib or something
	return binascii.crc32(guid.bytes) & 65535

def create_guidbox(named_guids):
	buckets = [ [] for _ in range(guid_hash_buckets) ]
	for guid,name in named_guids:
		buckets[guid_hash(guid)].append(( guid,name ))
	
	parts = [ b'GUIDBOX\0' ]
	
	guid_at = 8 + (guid_hash_buckets+1)*4
	parts.append(guid_at)
	for bucket in buckets:
		bucket[:] = sorted(bucket)
		guid_at += len(bucket) * 20
		parts.append(guid_at)
	
	name_at = guid_at + 4
	parts.append(name_at)
	for bucket in buckets:
		for guid,name in bucket:
			parts.append(guid.bytes)
			name_at += len(name)
			parts.append(name_at)
	
	for bucket in buckets:
		for guid,name in bucket:
			parts.append(name.encode("ascii"))
	
	for i,p in enumerate(parts):
		if isinstance(p, int):
			parts[i] = struct.pack('<I', p)
	return b''.join(parts)

def find_in_guidbox(guidbox, guid):
	assert guidbox[:8] == b'GUIDBOX\0'
	
	bucket = guid_hash(guid)
	start,end = struct.unpack("<II", guidbox[8+bucket*4 : 8+bucket*4+8])
	
	guid = guid.bytes
	for n in range(start, end, 20):
		name1,myguid,name2 = struct.unpack("<I16sI", guidbox[n : n+24])
		if myguid == guid:
			return guidbox[name1:name2].decode("ascii")
	return None

def iterate_guidbox(guidbox):
	assert guidbox[:8] == b'GUIDBOX\0'
	
	start, = struct.unpack("<I", guidbox[8+0*4 : 8+0*4+4])
	end, = struct.unpack("<I", guidbox[8+65536*4 : 8+65536*4+4])
	
	for n in range(start, end, 20):
		name1,myguid,name2 = struct.unpack("<I16sI", guidbox[n : n+24])
		yield ( uuid.UUID(bytes=myguid), guidbox[name1:name2].decode("ascii") )


#############
# Top level #
#############

def filter_guids(guidbox, text):
	pieces = []
	last_end = 0
	
	for start,end,guid,_ in find_guids(text):
		pieces.append(text[last_end:start])
		name = find_in_guidbox(guidbox, guid)
		if name:
			pieces.append(name)
		else:
			pieces.append(text[start:end])
		last_end = end
	pieces.append(text[last_end:])
	return ''.join(pieces)

if args.create:
	assert args.args
	named_guids = guids_from_files(args.args)
	named_guids = decide_guid_names(named_guids)
	by = create_guidbox(named_guids)
	open(args.guidbox,"wb").write(by)
elif args.dump:
	guidbox = open(args.guidbox,"rb").read()
	for guid,name in iterate_guidbox(guidbox):
		print('DEFINE_GUIDSTRUCT("'+str(guid)+'", '+name+');')
else:
	guidbox = open(args.guidbox,"rb").read()
	text = ' '.join(args.args)
	if find_guids(text):
		print(filter_guids(guidbox, text))
	else:
		for fn in args.args:
			if fn == '-':
				for line in sys.stdin:
					print(filter_guids(guidbox, line), end='')
			else:
				print(filter_guids(guidbox, open(fn,"rt").read()), end='')


#######################
# Leftover debug code #
#######################

if False:
	good_guids = [
		# 'e9f2d03a-747c-41c2-bb9a-02c62b6d5fcb',
	]
	for b in good_guids:
		print(b,guid_map.get(uuid.UUID(b)))
	# exit(0)
	
	bad_guids_msvcinc = [
		'7f9b00b3-f125-4890-876e-1cffbf697c4d', # typo in msvc-include directx/d3dx9mesh.h, last group should be 1C42BF...
		'77a6c36a-c7b1-4165-801e-cf320fec71b4', # mentioned only in a single comment
		'4fa050f0-f561-11cf-bdd9-00aa003a77b6', # sample guid, mentioned only in comments, explicitly points to nothing
		'12345678-1234-4667-1234-123456789abc', # sample guid, mentioned only in comments, points to nothing and also not random
		'E615A0E3-C4F1-11D1-A3A7-00AA00615092', # sample guid, mentioned only in comments
		'B0010000-AE6C-4804-98BA-C57B46965FE7', # sample guid, mentioned only in comments
		'C0010000-5738-4ff2-8445-BE3126691059', # sample guid, mentioned only in comments
		'c0b35736-ebf5-11d8-bbe9-505054503030', # Reserved GUIDS for our use (Network Diagnostics related)
		'c0b3573a-ebf5-11d8-bbe9-505054503030', # Reserved GUIDS for our use (Network Diagnostics related)
		'c0b3573b-ebf5-11d8-bbe9-505054503030', # Reserved GUIDS for our use (Network Diagnostics related)
		'c0b3573c-ebf5-11d8-bbe9-505054503030', # Reserved GUIDS for our use (Network Diagnostics related)
		'c0b3573d-ebf5-11d8-bbe9-505054503030', # Reserved GUIDS for our use (Network Diagnostics related)
		'c0b3573e-ebf5-11d8-bbe9-505054503030', # Reserved GUIDS for our use (Network Diagnostics related)
		'c0b3573f-ebf5-11d8-bbe9-505054503030', # Reserved GUIDS for our use (Network Diagnostics related)
		'c0b35742-ebf5-11d8-bbe9-505054503030', # Reserved GUIDS for our use (Network Diagnostics related)
		'c0b35743-ebf5-11d8-bbe9-505054503030', # Reserved GUIDS for our use (Network Diagnostics related)
		'c0b35744-ebf5-11d8-bbe9-505054503030', # Reserved GUIDS for our use (Network Diagnostics related)
		'c0b35745-ebf5-11d8-bbe9-505054503030', # Reserved GUIDS for our use (Network Diagnostics related)
		'c0b3575f-ebf5-11d8-bbe9-505054503030', # Reserved GUIDS for our use (Network Diagnostics related)
		'c0b35760-ebf5-11d8-bbe9-505054503030', # Reserved GUIDS for our use (Network Diagnostics related)
		'c0b35761-ebf5-11d8-bbe9-505054503030', # Reserved GUIDS for our use (Network Diagnostics related)
		'c0b35b15-ebf5-11d8-bbe9-505054503030', # Reserved GUIDS for our use (Network Diagnostics related)
		'c0b35b16-ebf5-11d8-bbe9-505054503030', # Reserved GUIDS for our use (Network Diagnostics related)
		'c0b35b17-ebf5-11d8-bbe9-505054503030', # Reserved GUIDS for our use (Network Diagnostics related)
		'c0b35b18-ebf5-11d8-bbe9-505054503030', # Reserved GUIDS for our use (Network Diagnostics related)
		'c0b35b19-ebf5-11d8-bbe9-505054503030', # Reserved GUIDS for our use (Network Diagnostics related)
		'c0b35b1a-ebf5-11d8-bbe9-505054503030', # Reserved GUIDS for our use (Network Diagnostics related)
		'c0b35b1b-ebf5-11d8-bbe9-505054503030', # Reserved GUIDS for our use (Network Diagnostics related)
		'c0b35b1c-ebf5-11d8-bbe9-505054503030', # Reserved GUIDS for our use (Network Diagnostics related)
		'c0b35b1d-ebf5-11d8-bbe9-505054503030', # Reserved GUIDS for our use (Network Diagnostics related)
		'12345678-4321-abcd-1234-9abcdef01234', # sample guid (malformed too, it has a 5678 after it)
		'A7654BA2-D4AB-4510-AADF-253EA74869C5', # sample guid
		'54a754c0-4bf1-11d1-83ee-00a0c90dc849', # typo of nnnnnnnn-4bf0-nnnn-nnnn-nnnnnnnnnnnn
		'5984FFE0-28D4-11CF-AE66-08002B2E1262', # in comments, doesn't seem to refer to anything
		'5D080304-FE2C-48fc-84CE-CF620B0F3C53', # in comments, doesn't seem to refer to anything
		'12345678-1234-1234-1234-123456789012', # sample guid, refers to nothing
		'EF8436C7-2512-4abd-AC73-20C8186D2B7F', # in comments, doesn't seem to refer to anything
		'AFE5B29D-50FA-46e8-B9BE-0C0C3CE4B3A5', # in comments, doesn't seem to refer to anything
		'494bbcea-b031-4e38-97c4-d5422dd618dc', # in comments, doesn't seem to refer to anything
		'57cd596f-ce47-11d9-92db-000bdb28ff98', # The GUID 57cd596f-ce47-11d9-92db-000bdb28ff98 is reserved for TMDS
		'57cd5976-ce47-11d9-92db-000bdb28ff98', # The GUID 57cd5976-ce47-11d9-92db-000bdb28ff98 is reserved
		'15320C45-FF80-484A-9DCB-0DF894E69A13', # typo of nnnnnnnn-nnnn-nnnn-nnnn-nnnnnnnn9a01
		'813b22ee-62f7-4200-9c85-73d139eaa579', # used only as include guard. And only half of it is the actual guard.
		'3bd1c4bf-004e-4e2f-8a4d-0bf633dcb074', # used only as part of a string
		'2ad99357-6fd2-11d3-8497-00c04f79dbc0', # include guard
		'8f10cc25-cf0d-42a0-acbe-e2de7007384d', # Reserved GUIDS for our use (adhoc networking related)
		'8f10cc30-cf0d-42a0-acbe-e2de7007384d', # Reserved GUIDS for our use (adhoc networking related)
		'8f10cc31-cf0d-42a0-acbe-e2de7007384d', # Reserved GUIDS for our use (adhoc networking related)
		'8f10cc32-cf0d-42a0-acbe-e2de7007384d', # Reserved GUIDS for our use (adhoc networking related)
		'8f10cc33-cf0d-42a0-acbe-e2de7007384d', # Reserved GUIDS for our use (adhoc networking related)
		'8f10cc34-cf0d-42a0-acbe-e2de7007384d', # Reserved GUIDS for our use (adhoc networking related)
		'8f10cc35-cf0d-42a0-acbe-e2de7007384d', # Reserved GUIDS for our use (adhoc networking related)
		'8f10cc36-cf0d-42a0-acbe-e2de7007384d', # Reserved GUIDS for our use (adhoc networking related)
		'DCB000FF-570F-4A9B-8D69-199FDBA5723B', # reserved
		'56FFCC31-D398-11d0-B2AE-00A0C908FA49', # typo of nnnnCC30-nnnn-nnnn-nnnn-nnnnnnnnnnnn
		'0000031A-0000-0000-C000-000000000046', # something authentication related, only in comments
		'0c733ac0-2a1c-11ce-ade5-00aa0044773d', # typo of nnnn3abf-nnnn-nnnn-nnnn-nnnnnnnnnnnn
		'effb7edb-0055-4f9a-a23a-4ff8131ad191', # typo of nnnnnnnn-nnnn-nnnn-a231-nnnnnnnnnnnn
		'd999e981-7948-4c8e-b742-c84e3b678f8f', # typo of nnnnnnnn-nnnn-4c83-nnnn-nnnnnnnnnnnn
		'e58442e4-0c80-402c-9559-867337a39765', # guid of a module. Don't know what prefix (CLSID_, IID_, etc) those have.
		'f3e092b2-6bdc-410f-bcb2-4c5ed4424180', # guid of a module. Don't know what prefix (CLSID_, IID_, etc) those have.
		'627bd890-ed54-11d2-b994-00c04f8ca82c', # Provider-specific columns for IColumnsRowset, only named in mingw (DBCOLUMN_SS_X_GUID)
		'B64784EB-D8D4-4d9b-9ACD-0E30806426F7', # unnamed custom attribute on something printer-related
		'0F21F359-AB84-41E8-9A78-36D110E6D2F9', # custom attribute on something Feeds-related
		'2ad99356-6fd2-11d3-8497-00c04f79dbc0', # include guard
		'B42CDE2B-6178-4a2c-A375-89DD3FD7F497', # in comments, doesn't seem to refer to anything
		'E77797C6-18AF-4458-BBDD-492D3F78FC8F', # in comments, doesn't seem to refer to anything
		'bb6df56d-cace-11dc-9992-0019b93a3a84', # sequential uuids that can be used for new interfaces, etc
		'bb6df56e-cace-11dc-9992-0019b93a3a84', # sequential uuids that can be used for new interfaces, etc
		'bb6df56f-cace-11dc-9992-0019b93a3a84', # sequential uuids that can be used for new interfaces, etc
		'bb6df570-cace-11dc-9992-0019b93a3a84', # sequential uuids that can be used for new interfaces, etc
		'bb6df571-cace-11dc-9992-0019b93a3a84', # sequential uuids that can be used for new interfaces, etc
		'bb6df572-cace-11dc-9992-0019b93a3a84', # sequential uuids that can be used for new interfaces, etc
		'bb6df573-cace-11dc-9992-0019b93a3a84', # sequential uuids that can be used for new interfaces, etc
		'e2ae82b7-229d-4428-b3d2-500000000002', # commented out uuid on IMAPI enum
		'e2ae82b7-229d-4428-b3d2-500000000003', # commented out uuid on IMAPI enum
		'e2ae82b7-229d-4428-b3d2-500000000004', # commented out uuid on IMAPI enum
		'e2ae82b7-229d-4428-b3d2-500000000005', # commented out uuid on IMAPI enum
		'e2ae82b7-229d-4428-b3d2-500000000006', # commented out uuid on IMAPI enums (five of em)
		'e2ae82b7-229d-4428-b3d2-500000000007', # commented out uuid on IMAPI enum
		'e2ae82b7-229d-4428-b3d2-500000000008', # commented out uuid on IMAPI enum
		'e2ae82b7-229d-4428-b3d2-500000000009', # commented out uuid on IMAPI enum
		'2598354f-9d65-49ce-b335-40630d901227', # commented out uuid on IMAPI enum
		'2598354e-9d65-49ce-b335-40630d901227', # commented out uuid on IMAPI enum
		'e2ae82b7-229d-4428-b3d2-00000001ffff', # commented out async_uuid on IMAPI enum
		'e2ae82b7-229d-4428-b3d2-000000010006', # commented out async_uuid on IMAPI enum
		'27354134-7F64-5B0F-8F00-5D77AFBE261E', # commented out DDiscRecorder2Events interface
		'204810bc-73b2-11d4-bf42-00b0d0118b56', # Reserved GUIDS for our use (UPNP related)
		'204810bd-73b2-11d4-bf42-00b0d0118b56', # Reserved GUIDS for our use (UPNP related)
		'204810be-73b2-11d4-bf42-00b0d0118b56', # Reserved GUIDS for our use (UPNP related)
		'204810bf-73b2-11d4-bf42-00b0d0118b56', # Reserved GUIDS for our use (UPNP related)
		'204810c0-73b2-11d4-bf42-00b0d0118b56', # Reserved GUIDS for our use (UPNP related)
		'204810c1-73b2-11d4-bf42-00b0d0118b56', # Reserved GUIDS for our use (UPNP related)
		'204810c2-73b2-11d4-bf42-00b0d0118b56', # Reserved GUIDS for our use (UPNP related)
		'204810c3-73b2-11d4-bf42-00b0d0118b56', # Reserved GUIDS for our use (UPNP related)
		'204810c4-73b2-11d4-bf42-00b0d0118b56', # Reserved GUIDS for our use (UPNP related)
		'204810c5-73b2-11d4-bf42-00b0d0118b56', # Reserved GUIDS for our use (UPNP related)
		'204810c6-73b2-11d4-bf42-00b0d0118b56', # Reserved GUIDS for our use (UPNP related)
		'204810c7-73b2-11d4-bf42-00b0d0118b56', # Reserved GUIDS for our use (UPNP related)
		'204810c8-73b2-11d4-bf42-00b0d0118b56', # Reserved GUIDS for our use (UPNP related)
		'204810c9-73b2-11d4-bf42-00b0d0118b56', # Reserved GUIDS for our use (UPNP related)
		'204810ca-73b2-11d4-bf42-00b0d0118b56', # Reserved GUIDS for our use (UPNP related)
		'204810cb-73b2-11d4-bf42-00b0d0118b56', # Reserved GUIDS for our use (UPNP related)
		'204810cc-73b2-11d4-bf42-00b0d0118b56', # Reserved GUIDS for our use (UPNP related)
		'204810cd-73b2-11d4-bf42-00b0d0118b56', # Reserved GUIDS for our use (UPNP related)
		'20481499-73b2-11d4-bf42-00b0d0118b56', # Reserved GUIDS for our use (UPNP related)
		'2048149a-73b2-11d4-bf42-00b0d0118b56', # Reserved GUIDS for our use (UPNP related)
		'c96fbd52-24dd-11d8-89fb-00904b2ea9c6', # Reserved GUIDS for our use (netprov related)
		'c96fbd53-24dd-11d8-89fb-00904b2ea9c6', # Reserved GUIDS for our use (netprov related)
		'c96fbd54-24dd-11d8-89fb-00904b2ea9c6', # Reserved GUIDS for our use (netprov related)
		'c96fbd55-24dd-11d8-89fb-00904b2ea9c6', # Reserved GUIDS for our use (netprov related)
		'c96fbd56-24dd-11d8-89fb-00904b2ea9c6', # Reserved GUIDS for our use (netprov related)
		'c96fbd57-24dd-11d8-89fb-00904b2ea9c6', # Reserved GUIDS for our use (netprov related)
		'c96fbd58-24dd-11d8-89fb-00904b2ea9c6', # Reserved GUIDS for our use (netprov related)
		'c96fbd59-24dd-11d8-89fb-00904b2ea9c6', # Reserved GUIDS for our use (netprov related)
		'6f11fe5c-2fc5-101b-9e45-00000b65c7ef', # sample guid
		'dcbbbab6-2fff-4bbb-aaee-338e368af6fa', # ranges in mbnapi.idl
		'dcbbbab6-4001-4bbb-aaee-338e368af6fa', # ranges in mbnapi.idl
		'dcbbbab6-4fff-4bbb-aaee-338e368af6fa', # ranges in mbnapi.idl
		'dcbbbab6-6001-4bbb-aaee-338e368af6fa', # ranges in mbnapi.idl
		'dcbbbab6-6fff-4bbb-aaee-338e368af6fa', # ranges in mbnapi.idl
		'dcbbbab6-7001-4bbb-aaee-338e368af6fa', # ranges in mbnapi.idl
		'dcbbbab6-7fff-4bbb-aaee-338e368af6fa', # ranges in mbnapi.idl
		'dcbbbab6-8001-4bbb-aaee-338e368af6fa', # ranges in mbnapi.idl
		'dcbbbab6-8fff-4bbb-aaee-338e368af6fa', # ranges in mbnapi.idl
		'dcbbbab6-9001-4bbb-aaee-338e368af6fa', # ranges in mbnapi.idl
		'dcbbbab6-9fff-4bbb-aaee-338e368af6fa', # ranges in mbnapi.idl
		'dcbbbab6-aaaa-4bbb-aaee-338e368af6fa', # ranges in mbnapi.idl
		'54bab802-bb0b-4b4a-9ce9-7360a0120b3e', # sample guid
		'74d557d9-4a8e-4a3f-9a32-3f1a0eab71ba', # sample guid
		'022150a0-113d-11df-bb61-001aa01bbc58', # commented out guid on an enum
		'A2382C3C-A108-11d2-B117-006008B0E5D2', # module guid
		'C0E8AE9B-306E-11D1-AACF-00805FC1270E', # Reserved GUIDS for Microsoft use
		'C0E8AE9C-306E-11D1-AACF-00805FC1270E', # Reserved GUIDS for Microsoft use
		'C0E8AEA1-306E-11D1-AACF-00805FC1270E', # Reserved GUIDS for Microsoft use
		'C0E8AEA2-306E-11D1-AACF-00805FC1270E', # Reserved GUIDS for Microsoft use
		'C0E8AEA3-306E-11D1-AACF-00805FC1270E', # Reserved GUIDS for Microsoft use
		'C0E8AEA4-306E-11D1-AACF-00805FC1270E', # Reserved GUIDS for Microsoft use
		'C0E8AEA5-306E-11D1-AACF-00805FC1270E', # Reserved GUIDS for Microsoft use
		'C0E8AEA6-306E-11D1-AACF-00805FC1270E', # Reserved GUIDS for Microsoft use
		'C0E8AEA7-306E-11D1-AACF-00805FC1270E', # Reserved GUIDS for Microsoft use
		'C0E8AEA8-306E-11D1-AACF-00805FC1270E', # Reserved GUIDS for Microsoft use
		'C0E8AEA9-306E-11D1-AACF-00805FC1270E', # Reserved GUIDS for Microsoft use
		'C0E8B266-306E-11D1-AACF-00805FC1270E', # Reserved GUIDS for Microsoft use
		'C0E8B267-306E-11D1-AACF-00805FC1270E', # Reserved GUIDS for Microsoft use
		'C0E8B268-306E-11D1-AACF-00805FC1270E', # Reserved GUIDS for Microsoft use
		'c6a4e9ef-432e-4f32-9107-71d2b6fd2c33', # commented out guid on ICOMAdminCatalog2
		'e2a26f78-ae07-4ee0-a30f-ce354f5a94cd', # typo of nnnnnnnn-nnnn-nnnn-nnnn-ce54f5nnnnnn
		'D1BAA1C7-BAEE-4ba9-AF20-FAF66AA4DCB8', # sample guid probably
		'4a354637-5649-4518-8a48-323c158bc02d', # sample guid
		'77e5b300-6a88-4f63-b490-e25b414bed4e', # sample guid
		'd57af411-737b-c042-abae-878b1e16adee', # namespace for a v5 guid generator
		'b3864c38-4273-58c5-545b-8b3608343471', # sample guid
		'af748dd4-d800-11db-9705-005056c00008', # typo of nnnnnnnn-0d80-nnnn-nnnn-nnnnnnnnnnnn
		'faaf2f61-9b26-4591-9bb1-b9b8bae2d34c', # sample guid
		'd5a47fa7-6d98-11d1-a21a-00a0c9223196', # guid range (add 0..=65535 to first group) named INIT_MMREG_MID
		'e36dc2ac-6d9a-11d1-a21a-00a0c9223196', # guid range (add 0..=65535 to first group) named INIT_MMREG_PID
		'00000001-facb-11e6-bd58-64006a7986d3', # guid range (set first group to 0..=0x7fffffff) named HV_GUID_VSOCK_TEMPLATE
		'00000032-facb-11e6-bd58-64006a7986d3', # guid range (set first group to 0..=0x7fffffff) named HV_GUID_VSOCK_TEMPLATE
		'7fffffff-facb-11e6-bd58-64006a7986d3', # guid range (set first group to 0..=0x7fffffff) named HV_GUID_VSOCK_TEMPLATE
		'4e1cecd2-1679-463b-a72f-a5bf64c86eba', # guid range (add 0..=65535 to first group) named INIT_USBAUDIO_MID
		'abcc5a5e-c263-463b-a72f-a5bf64c86eba', # guid range (add 0..=65535 to first group) named INIT_USBAUDIO_PID
		'FC575048-2E08-463B-A72F-A5BF64C86EBA', # guid range (add 0..=65535 to first three groups) named INIT_USBAUDIO_PRODUCT_NAME
	]
	bad_guids_mingwinc = [
		'214A0F28-B737-4026-B847-4F9E37D79529', # IID_IVssDifferentialSoftwareSnapshotMgmt - only mentioned in mingw in a comment
		'01954E6B-9254-4e6e-808C-C9E05D007696', # IID_IVssEnumMgmtObject - only mentioned in mingw in a comment
		'FA7DF749-66E7-4986-A27F-E2F04AE53772', # IID_IVssSnapshotMgmt - only mentioned in mingw in a comment
		'27016870-8e02-11d1-924e-00c04fbbbfb3', # CLSID_MSRemote - initializer is behind an ifdef in mingw
		'27016871-8e02-11d1-924e-00c04fbbbfb3', # CLSID_MSRemoteSession - initializer is behind an ifdef in mingw
		'27016872-8e02-11d1-924e-00c04fbbbfb3', # CLSID_MSRemoteCommand - initializer is behind an ifdef in mingw
		'27016873-8e02-11d1-924e-00c04fbbbfb3', # DBPROPSET_MSREMOTE_DBINIT - initializer is behind an ifdef in mingw
		'27016874-8e02-11d1-924e-00c04fbbbfb3', # DBPROPSET_MSREMOTE_DATASOURCE - initializer is behind an ifdef in mingw
		'DC44BE78-B18D-4399-B210-641BF67A002C', # IID_IWTSSBPlugin - only mentioned in mingw in a comment
		'3d6fa8d4-fe05-11d0-9dda-00c04fd7ba7c', # DiskIoGuid https://learn.microsoft.com/en-us/windows/win32/etw/nt-kernel-logger-constants
		'e2011457-1546-43c5-a5fe-008deee3d3f0', # <supportedOS> for Vista https://stackoverflow.com/a/41855901
		'35138b9a-5d96-4fbd-8e2d-a2440225f93a', # <supportedOS> for 7
		'F6B96EDA-1A94-4476-A85F-4D3DC7B39C3F', # comment suggesting it's IID_IDvbSiParser2 (it's actually CLSID_DvbSiParser I think)
		'7c07e0d0-4418-11d2-9212-00c04fbbbfb3', # CLSID_MSPersist - initializer is behind an ifdef in mingw
		'4d7839a0-5b8e-11d1-a6b3-00a0c9138c66', # DBPROPSET_PERSIST - initializer is behind an ifdef in mingw
		'53bfae52-b167-4e2f-a258-0a37b57ff845', # #define DISM_ONLINE_IMAGE L"DISM_{53BFAE52-B167-4E2F-A258-0A37B57FF845}"
		'D02C95CC-EDBA-4305-9B5D-1820D7704BBF', # typo of nnnnnnnn-nnnn-nnnn-nnnn-nnnnnnnn4DBF
		'f2e455dc-09b3-4316-8260-676ada32481c', # EncoderChrominanceTable - only mentioned in mingw in a comment
		'66087055-ad66-4c7c-9a18-38a2310b8337', # EncoderColorDepth - only mentioned in mingw in a comment
		'e09d739d-ccd4-44ee-8eba-3fbf8be4fc58', # EncoderCompression - only mentioned in mingw in a comment
		'edb33bce-0266-4a77-b904-27216099e717', # EncoderLuminanceTable - only mentioned in mingw in a comment
		'1d5be4b5-fa4a-452d-9cdd-5db35105e7eb', # EncoderQuality - only mentioned in mingw in a comment
		'6d42c53a-229a-4825-8bb7-5c99e2b9a8b8', # EncoderRenderMethod - only mentioned in mingw in a comment
		'292266fc-ac40-47bf-8cfc-a85b89a655de', # EncoderSaveFlag - only mentioned in mingw in a comment
		'3a4e2661-3109-4e56-8536-42c156e7dcfa', # EncoderScanMethod - only mentioned in mingw in a comment
		'8d0eb2d1-a58e-4ea8-aa14-108074b7b6f9', # EncoderTransformation - only mentioned in mingw in a comment
		'24d18c76-814a-41a4-bf53-1c219cccf797', # EncoderVersion - only mentioned in mingw in a comment
		'7462dc86-6180-4c7e-8e3f-ee7333a7a483', # FrameDimensionPage - only mentioned in mingw in a comment
		'6aedbd6d-3fb5-418a-83a6-7f45229dc872', # FrameDimensionTime - only mentioned in mingw in a comment
	]
	bad_guids = []
	
	
	bad_guids = [ uuid.UUID(guid) for guid in bad_guids ]
	empty=0
	good=0
	multi=0
	p=0
	for guid,names in guid_map.items():
		if guid in bad_guids:
			bad_guids.remove(guid)
			continue
		if len(names) == 1:
			good+=1
		if len(names) != 1 and p < 100000:
			print(guid,sorted(names))
			# print(found_guids_frag[guid])
			p+=1
		if len(names) < 1:
			empty+=1
		if len(names) > 1:
			multi+=1
	print(empty,good,multi)
	if bad_guids:
		if len(bad_guids) < 10:
			print(bad_guids)
		assert not bad_guids
	# print(guid_map)
