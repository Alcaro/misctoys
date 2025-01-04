#!/usr/bin/env python3
import gzip
import sys
import struct
import io
import mmap

# much of this is based on https://github.com/HearthSim/UnityPack/wiki/Format-Documentation

class bytestream:
	def __init__(self, by):
		self._full_by = by
		self._by = memoryview(self._full_by)
	
	def bytes(self, n):
		ret = bytes(self._by[0:n])
		self._by = self._by[n:]
		return ret
	
	def peekbytes(self, n):
		return bytes(self._by[0:n])
	
	def signature(self, s):
		if isinstance(s, str):
			s = s.encode("ascii")
		if self.peekbytes(len(s)) == s:
			self.bytes(len(s))
			return True
		return False
	
	def u8(self): return self.bytes(1)[0]
	def u8l(self): return self.u8()
	def u8b(self): return self.u8()
	def u16l(self): return struct.unpack("<H", self.bytes(2))[0]
	def u16b(self): return struct.unpack(">H", self.bytes(2))[0]
	def u32l(self): return struct.unpack("<I", self.bytes(4))[0]
	def u32b(self): return struct.unpack(">I", self.bytes(4))[0]
	def uu64l(self): return struct.unpack("<Q", self.bytes(8))[0]  # unaligned - rarely used by Unity
	def uu64b(self): return struct.unpack(">Q", self.bytes(8))[0]
	
	def f32l(self): return struct.unpack("<f", self.bytes(4))[0]
	def f32b(self): return struct.unpack(">f", self.bytes(4))[0]
	def f64l(self): return struct.unpack("<d", self.bytes(8))[0]
	def f64b(self): return struct.unpack(">d", self.bytes(8))[0]
	
	def align(self, n):
		skip = (-self.tell())&(n-1)
		assert self.zeroes(skip)
	
	def a32(self):
		self.align(4)
	
	def au64l(self):
		self.a32()
		return self.uu64l()
	
	def au64b(self):
		self.a32()
		return self.uu64b()
	
	def str(self, n):
		return self.bytes(n).decode("utf-8")
	
	def strnul(self):
		l = self.peekbytes(256).index(b'\0')
		ret = self.str(l)
		self.bytes(1)
		return ret
	
	def str32la(self):
		ret = self.bytes(self.u32l()).decode("utf-8")
		self.a32()
		return ret
	def str32ba(self):
		ret = self.bytes(self.u32b()).decode("utf-8")
		self.a32()
		return ret
	def str32lu(self):
		return self.bytes(self.u32l()).decode("utf-8")
	def str32bu(self):
		return self.bytes(self.u32b()).decode("utf-8")
	def str32lx(self):
		ret = self.bytes(self.u32l()).decode("utf-8")
		assert self.tell()&3 == 0
		return ret
	def str32bx(self):
		ret = self.bytes(self.u32b()).decode("utf-8")
		assert self.tell()&3 == 0
		return ret
	
	def zeroes(self, n):
		if sum(self.peekbytes(n)) == 0:
			self.bytes(n)
			return True
		return False
	
	def pptrl(self):
		return self.u32l(), self.au64l()
	def pptrb(self):
		return self.u32b(), self.au64b()
	
	def tell(self):
		return len(self._full_by) - len(self._by)
	def size(self):
		return len(self._full_by)
	def remaining(self):
		return len(self._by)

files = {}
remaining_files = []
unity_objects = {}  # filename -> list (unsorted)

class UnityObject:
	def __init__(self, obj_id, obj_type, by_src, references):
		self.id = obj_id
		self.type = obj_type
		self.bytes_src = by_src
		self.references = references
	
	def bytes(self):
		return self.bytes_src()
	
	def follow_pptr(self, pptr):
		file_id, obj_id = pptr
		ret, = ( obj for obj in unity_objects[self.references[file_id]] if obj.id == obj_id )
		return ret

t_Texture2D = 28
t_TextAsset = 49
t_AudioClip = 83
t_MonoBehavior = 114
t_AssetBundle = 142
t_ResourceManager = 147
t_Sprite = 213
t_VideoClip = 329

def add_file(fn, by, source, scan_file=True):
	if isinstance(fn, bytes):
		fn = fn.decode("utf-8")
	files[fn] = by
	if scan_file:
		remaining_files.append(fn)
	if source is not None:
		print("("+source+") ->", fn)

def gzip_fname(by):
	if by[0:2] != b"\x1F\x8B": 1/0  # should've been checked already
	if by[3] & 8:
		by = by[10:]
		return by[0:by.index(b'\0')]

def lz4_decompress(by):
	# https://ticki.github.io/blog/how-lz4-works/
	
	s = bytestream(by)
	
	def getnum():
		ret = 15
		while True:
			last = s.u8()
			ret += last
			if last != 255:
				return ret
	
	ret = bytearray()
	
	while True:
		token = s.u8()
		copy = token >> 4
		if copy == 15:
			copy = getnum()
		ret += s.bytes(copy)
		
		if not s.remaining():
			return ret
		
		rlepos = len(ret) - s.u16l()
		rle = token & 15
		if rle == 15:
			rle = getnum()
		rle += 4
		
		while rle:
			ret.append(ret[rlepos])
			rlepos += 1
			rle -= 1

def unity_decompress(by, flags):
	if flags&63 == 0:
		return by
	# https://imbushuo.net/blog/archives/505/ says 1 is LZMA
	if flags&63 == 2:
		return lz4_decompress(by)
	if flags&63 == 3:
		return lz4_decompress(by)
	print(flags)
	1/0

def unity_enumerate_objects(f):
	f.seek(0)
	s = bytestream(f.read(48))
	
	metasz = s.u32b()
	filesz = s.u32b()
	version = s.u32b()
	
	assert version in (17,21,22)
	if version <= 21:
		dataoffs = s.u32b()
		assert s.u32b() == 0  # big endian
	if version >= 22:
		assert metasz == 0
		assert filesz == 0
		assert s.u32b() == 0  # unknown, probably padding
		metasz = s.au64b()
		filesz = s.au64b()
		dataoffs = s.au64b()
		assert s.au64b() == 0  # big endian
	
	f.seek(s.tell())
	s = bytestream(f.read(metasz))
	
	s.strnul()  # 2022.1.11f1
	s.u32l()  # platform
	
	# types
	types = []
	type_trees = s.u8()
	for n in range(s.u32l()):
		cls = s.u32l()
		s.u8()  # unknown
		s.u16l()  # unknown
		if cls == t_MonoBehavior: s.bytes(16)  # script hash
		s.bytes(16)  # type hash
		types.append(cls)
		
		if type_trees:
			1/0  # untested
			n_nodes = s.u32l()
			len_strbuf = s.u32l()
			
			s_t = bytestream(s.bytes(n_nodes*32))
			local_strbuf = s.bytes(len_strbuf)
			
			global_strbuf = \
				b"AABB\0AnimationClip\0AnimationCurve\0AnimationState\0Array\0Base\0BitField\0bitset\0bool\0char\0ColorRGBA\0Comp" \
				b"onent\0data\0deque\0double\0dynamic_array\0FastPropertyName\0first\0float\0Font\0GameObject\0Generic Mono\0Grad" \
				b"ientNEW\0GUID\0GUIStyle\0int\0list\0long long\0map\0Matrix4x4f\0MdFour\0MonoBehaviour\0MonoScript\0m_ByteSize\0m" \
				b"_Curve\0m_EditorClassIdentifier\0m_EditorHideFlags\0m_Enabled\0m_ExtensionPtr\0m_GameObject\0m_Index\0m_IsA" \
				b"rray\0m_IsStatic\0m_MetaFlag\0m_Name\0m_ObjectHideFlags\0m_PrefabInternal\0m_PrefabParentObject\0m_Script\0m" \
				b"_StaticEditorFlags\0m_Type\0m_Version\0Object\0pair\0PPtr<Component>\0PPtr<GameObject>\0PPtr<Material>\0PPtr" \
				b"<MonoBehaviour>\0PPtr<MonoScript>\0PPtr<Object>\0PPtr<Prefab>\0PPtr<Sprite>\0PPtr<TextAsset>\0PPtr<Texture" \
				b">\0PPtr<Texture2D>\0PPtr<Transform>\0Prefab\0Quaternionf\0Rectf\0RectInt\0RectOffset\0second\0set\0short\0size\0" \
				b"SInt16\0SInt32\0SInt64\0SInt8\0staticvector\0string\0TextAsset\0TextMesh\0Texture\0Texture2D\0Transform\0Typele" \
				b"ssData\0UInt16\0UInt32\0UInt64\0UInt8\0unsigned int\0unsigned long long\0unsigned short\0vector\0Vector2f\0Vec" \
				b"tor3f\0Vector4f\0m_ScriptingClassIdentifier\0Gradient\0Type*\0int2_storage\0int3_storage\0BoundsInt\0m_Corre" \
				b"spondingSourceObject\0m_PrefabInstance\0m_PrefabAsset\0"
			
			def get_str(off):
				if off & 0x80000000:
					src = global_strbuf
				else:
					src = local_strbuf
				ret = src[off&0x7FFFFFFF:]
				ret = ret[:ret.index(b'\0')]
				return ret
			
			for n in range(n_nodes):
				version = s_t.u16l()
				depth = s_t.u8()
				is_array = s_t.u8()
				type_off = s_t.u32l()
				name_off = s_t.u32l()
				index = s_t.u32l()
				flags = s_t.u32l()  # 0x4000 means align stream after this field, others unknown
				unk1 = s_t.u32l()
				unk2 = s_t.u32l()
				
				print("version",version,"depth",depth,"is_array",is_array,"type",get_str(type_off),"name",get_str(name_off),
				      "index",index,"flags",flags,"unk1",unk1,"unk2",unk2)
			
			assert s.u32l() == 0
	
	ext_files = []
	objs = []
	
	def get_obj_bytes(obj_start, obj_len):
		def inner():
			f.seek(obj_start)
			return f.read(obj_len)
		return inner
	
	# objects
	for n in range(s.u32l()):
		obj_id = s.au64l()
		if version <= 21:
			local_start = s.u32l()
		if version >= 22:
			local_start = s.au64l()
		obj_start = dataoffs + local_start
		obj_len = s.u32l()
		type_idx = s.u32l()
		obj_type = types[type_idx]
		# this pokes ext_files before it's filled in - this is safe, it's passed by reference
		objs.append(UnityObject(obj_id, obj_type, get_obj_bytes(obj_start, obj_len), ext_files))
	
	# adds
	for n in range(s.u32l()):
		# unclear what these are
		s.u32l()
		s.au64l()
	
	# external files
	for n in range(s.u32l()):
		assert s.strnul() == ""
		s.bytes(16)
		assert s.u32l() == 0
		ext_files.append(s.strnul())
	
	if version >= 21:
		# unknown what this is
		# I've seen it only in a single game, containing the values
		# ffffffff0000000000000000000000000000000000000000000000000000000000000000000000
		# ffffffff0001000000000000000000000000000000000000000000000000000000000000000000
		for n in range(s.u32l()):
			print(s.bytes(39).hex())
	assert s.u8() == 0
	assert s.remaining() == 0
	
	return objs

def process_unitywebdata(by):
	# decompressing the entire thing isn't ideal, but random access is needed, and unitywebdata files tend to be relatively small
	s = bytestream(by)
	assert s.signature("UnityWebData1.0\0")
	files = {}
	head_len = s.u32l()
	while s.tell() != head_len:
		off = s.u32l()
		size = s.u32l()
		name = s.str(s.u32l())
		add_file(name, by[off:off+size], "UnityWebData")

def process_unityfs(by):
	head = bytestream(by)
	assert head.signature("UnityFS\0")
	version = head.u32b()
	assert version in (6,7,8)
	head.strnul()  # 5.x.x
	head.strnul()  # 2022.1.11f1
	assert head.uu64b() == len(by)
	
	ciblock = head.u32b()
	uiblock = head.u32b()
	flags = head.u32b()
	
	if version >= 7:
		head.align(16)
	
	block = unity_decompress(head.bytes(ciblock), flags)
	
	body = bytestream(block)
	body.bytes(16)  # guid
	
	in_pos = head.tell()
	
	BLOCK_SIZE = 131072
	class UnityFS:
		def __init__(self, blocks):
			self.blocks = blocks
		
		def read_single_from(self, pos):
			block_idx = pos//BLOCK_SIZE
			block_off = pos%BLOCK_SIZE
			block = self.blocks[block_idx]
			if isinstance(block, tuple):
				block = unity_decompress(*self.blocks[block_idx])
				self.blocks[block_idx] = block
			return block[block_off:]
		
		def read_from(self, pos, n):
			ret = self.read_single_from(pos)
			if len(ret) < n:
				ret = bytearray(ret)
				while len(ret) < n:
					ret += self.read_single_from(pos+len(ret))
			return ret[:n]
	
	class UnityFSFile:
		def __init__(self, fs, fs_pos, fs_len):
			self.fs = fs
			self.fs_pos = fs_pos
			self.fs_len = fs_len
			self.pos = 0
		def seek(self, pos):
			self.pos = pos
		def read(self, n=-1):
			pos = self.pos
			if n == -1:
				n = self.fs_len - pos
			self.pos += n
			return self.fs.read_from(self.fs_pos + pos, n)
	
	blocks = []
	nblocks = body.u32b()
	for n in range(nblocks):
		u_size = body.u32b()
		assert u_size == BLOCK_SIZE or n == nblocks-1
		c_size = body.u32b()
		flags = body.u16b()
		blocks.append(( head.bytes(c_size), flags ))
	
	fs = UnityFS(blocks)
	
	nfile = body.u32b()
	for n in range(nfile):
		offset = body.uu64b()
		size = body.uu64b()
		flags = body.u32b()
		name = body.strnul()
		assert flags&~4 == 0
		f = UnityFSFile(fs, offset, size)
		add_file(name, f, "UnityFS", False)
		if flags & 4:
			print("Extracting")
			unity_objects[name] = unity_enumerate_objects(f)
	
	assert body.tell() == uiblock

def process_bundle(by):
	print("todo: there's a reader in ~/x/ms/unity1.cpp function load_bundle()")

for fn in sys.argv[1:]:
	with open(fn, "rb") as f:
		add_file(fn, mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ), None)

while remaining_files:
	fn = remaining_files.pop(0)
	print(fn)
	by = files[fn]
	by_head = bytes(by[0:64])
	if b'UnityWeb Compressed Content (brotli)' in by_head:
		try:
			import brotli
			add_file(fn, brotli.decompress(by), "brotli")
		except ModuleNotFoundError:
			print("that file is compressed with Brotli; install your python brotli module")
			raise
	elif by_head.startswith(b"\x1F\x8B"):
		add_file(gzip_fname(by), gzip.open(io.BytesIO(by), mode='rb').read(), "gzip")
	elif by_head.startswith(b"UnityWebData1.0\0"):
		process_unitywebdata(by)
	elif by_head.startswith(b"UnityFS\0"):
		process_unityfs(by)
	elif by_head[4:8] == struct.pack(">L", len(by)):
		process_bundle(by)
	else:
		print("-> none ("+str(by[:64])+")")

def sanitize_filename(fn):
	return fn.replace("/", "_")  # will pass through . and .., but they'll just fail to open

resmgr_objs = {}
for objs in unity_objects.values():
	for obj in objs:
		if obj.type == t_ResourceManager:
			s = bytestream(obj.bytes())
			for n in range(s.u32l()):
				# todo: if this contains any music, use it
				name = s.str32la()
				body_ref = s.pptrl()
				
				# if name == "audiomanager":
					# body = obj.follow_pptr(body_ref)
					# print(body)
for objs in unity_objects.values():
	for obj in objs:
		# print(obj.type)
		if obj.type == t_AudioClip:
			s = bytestream(obj.bytes())
			outname = s.str32la()
			s.bytes(32)  # don't know what's in here
			srcfn = s.str32la()
			srcpos = s.au64l()
			srclen = s.au64l()
			by = files[srcfn][srcpos:srcpos+srclen]
			print(outname)
			open("out/"+sanitize_filename(outname)+".bin","wb").write(by)
			# unity3d music is often aac in mp4 container
			# to check contents, use
			#  ffprobe "$sfn" -loglevel warning -select_streams a:0 -show_entries stream=codec_name -of csv=p=0
			# and to transcode to a proper sound-only container,
			#  ffmpeg -loglevel warning -i "$sfn" -acodec copy -vcodec none "$tfn"
