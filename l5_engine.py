# Level-5 Games (Nintendo Switch and PC)
# Noesis script adapted by Daiki froms DKDave's Yokai Watch 4 script & AFGRocha
# Load meshes from both .G4PKM and .G4MD files
# Last updated: 9 November 2024

# TO DO LIST:
# Add skeleton


from inc_noesis import *

def registerNoesisTypes():
	handle = noesis.register("Level-5 Engine",".g4pkm;.g4md")
	noesis.setHandlerTypeCheck(handle, bcCheckType)
	noesis.setHandlerLoadModel(handle, bcLoadModel)
	noesis.logPopup()
	return 1


# Check file type

def bcCheckType(data):
	bs = NoeBitStream(data)
	file_id = bs.readUInt()

	if file_id == 0x4b503447 or file_id == 0x444d3447:
		return 1
	else:
		return 0


def bcLoadModel(data, mdlList):
	bs = NoeBitStream(data)
	ctx = rapi.rpgCreateContext()

	curr_folder = rapi.getDirForFilePath(rapi.getInputName()).lower()
	curr_file = rapi.getLocalFileName(rapi.getInputName()).lower()

	bones = []

	filename = curr_file.split(".")[0]
	vert_file = filename + ".g4mg"
	tex_file = filename + ".g4tx"

	if ".g4pkm" in curr_file:
		bs.seek(0x48)
		skel_size = bs.readUInt()
		bs.seek(0x80)
		sk = NoeBitStream(bs.readBytes(skel_size))

# For some models, the G4MD inside the G4PKM file doesn't work, but the separate G4MD file does (if it exists), so load that instead

		if rapi.checkFileExists(curr_folder + filename + ".g4md"):
			md = NoeBitStream(rapi.loadIntoByteArray(curr_folder + filename + ".g4md"))
			print("External G4MD file loaded")
		else:
			offset = data.find(b'G4MD')
			bs.seek(offset + 0x0c)
			md_size = bs.readUInt() + 0xa0
			bs.seek(offset)
			md = NoeBitStream(bs.readBytes(md_size))

	else:
		md = NoeBitStream(bs.readBytes(len(data)))



# Load vertex data file if it exists (or exit if not)

	if rapi.checkFileExists(curr_folder + vert_file):
		vf = NoeBitStream(rapi.loadIntoByteArray(curr_folder + vert_file))
		print("Geometry data file loaded.")
	else:
		print("Vertex data file " + vert_file + " doesn't exist.")
		return 1


# Read the mesh data

	md.seek(4)
	submesh_info = md.readUShort()
	md.seek(0x20)
	submesh_count = md.readUShort()
	mat_count = md.readUShort()
	md.seek(0x26)
	vlayout_count = md.readUByte()
	md.seek(0x5c)
	face_data = md.readUInt()

	vlayout_offs = []
	vnames = ["", "Verts", "Normals", "", "", "", "", "", "Colours", "", "UV", "UV2", "UV3", "UV4", "UV5", "UV6"]
	vlayout = (submesh_count * 0x50) + submesh_info
	md.seek(vlayout)

	for v in range(vlayout_count):
		vlayout_offs.append(md.tell())
		md.readUByte()
		entry_count = md.readUByte()
		md.readBytes(6)
		md.seek(entry_count * 8, 1)

	mat_table = md.tell()							# how to calculate this without reading vlayout table first?
	mat_table = Align(mat_table, 16)
	mat_table2 = mat_table + (mat_count * 0x10) + 0x30


# Load texture archive if it exists, and create materials
# Some of this could be completely wrong ...

	if rapi.checkFileExists(curr_folder + filename + ".g4tx"):
		tx = NoeBitStream(rapi.loadIntoByteArray(curr_folder + tex_file))
		print("Texture data file loaded.")
		tex_list, tex_names = ReadTextures(tx)
		mat_list = []

		for m in range(mat_count):
			md.seek(mat_table + (m * 0x10) + 12)
			mcount = md.readUShort()
			mstart = md.readUShort()

			temp_list = []
			for x in range(mcount):
				md.seek(mat_table2 + (mstart * 6) + (x * 6))
				mnum = md.readUByte()
				temp_list.append(mnum)

			material = NoeMaterial("Mat_" + str(m), "")
			print(temp_list)
			
			base_texture = None
			normal_texture = None
			spec_texture = None
			occ_texture = None
			
			if len(temp_list) == 6:
				diff = temp_list[5]
				spec = temp_list[4]
				occ =  temp_list[3]
				base_texture = tex_names[diff]
				spec_texture = tex_names[spec]
				occ_texture = tex_names[occ]

			if len(temp_list) == 5:
				diff = temp_list[1] if filename[0] == "c" else temp_list[4]
				spec = temp_list[0]
				occ =  temp_list[2]
				base_texture = tex_names[diff]
				spec_texture = tex_names[spec]
				occ_texture = tex_names[occ]
			
			if len(temp_list) == 4:
				diff = temp_list[3]
				base_texture = tex_names[diff]

			if len(temp_list) == 3:
				diff = temp_list[2]
				base_texture = tex_names[0]

			# Ensure no special files are used as the base texture
			def truncate_texture_name(tex_name):
				if tex_name.endswith("oc"):
					return tex_name[:-2]
				elif tex_name.endswith("line"):
					return tex_name[:-4]
				elif tex_name.endswith("msk"):
					return tex_name[:-3]
				elif tex_name.endswith("sp"):
					return tex_name[:-2]
				elif tex_name.endswith("spm"):
					return tex_name[:-3] 
				return tex_name

			# This code fixes shadow/normal maps from being used as main textures. You're welcome.
			if base_texture:
				base_texture = truncate_texture_name(base_texture)
				if base_texture.endswith("oc"):
					base_texture = None

			# Asign textures
			if base_texture:
				material.setTexture(base_texture)
			if normal_texture:
				material.setSpecularTexture(normal_texture)
			if spec_texture:
				material.setSpecularTexture(spec_texture)
			if occ_texture:
				material.setOcclTexture(occ_texture)

			mat_list.append(material)
	else:
		print("Texture data file " + tex_file + " doesn't exist.  No textures will be available.")
		tex_list = []
		mat_list = []


	for a in range(submesh_count):
		md.seek(submesh_info + (a * 0x50))
		misc1 = md.tell()
		vert_offset = md.readUInt()
		face_offset = md.readUInt() + face_data
		vert_count = md.readUInt()
		face_count = md.readUInt()
		md.seek(0x2e, 1)
		stride = md.readUByte()
		md.seek(3, 1)
		layout_num = md.readUByte()
		mat_num = md.readUByte()

		print("--------------------------------------------------------------------------------")
		print(a, "\t", hex(vert_offset), "\t", hex(face_offset), "\t", vert_count, "\t", face_count, "\t", hex(stride), mat_num, layout_num)
		print("--------------------------------------------------------------------------------")

		if face_count != 0:
			vf.seek(vert_offset)
			vertices = vf.readBytes(vert_count * stride)

			rapi.rpgSetName(filename + "_" + str(a))
			rapi.rpgSetMaterial("Mat_" + str(mat_num))

			layout_offset = vlayout_offs[layout_num]			# doesn't always work?
			md.seek(layout_offset+1)
			entry_count = md.readUByte()
			md.readBytes(6)

			for x in range(entry_count):
				vtype = md.readUByte()
				vtype_off = md.readUShort()
				md.readUByte()
				vtype_num = md.readUInt()

				print(x, "\t", vnames[vtype], "\t", vtype_off, "\t", vtype_num)

				if vtype_num == 2 or vtype_num == 3:
					vert_num = noesis.RPGEODATA_FLOAT
				elif vtype_num == 12:
					vert_num = noesis.RPGEODATA_UBYTE
				elif vtype_num == 14:
					vert_num = noesis.RPGEODATA_USHORT
				elif vtype_num == 20 or vtype_num == 18:
					vert_num = noesis.RPGEODATA_SHORT


				if vtype == 1:
					rapi.rpgBindPositionBufferOfs(vertices, vert_num, stride, vtype_off)
				elif vtype == 2:
					rapi.rpgBindNormalBufferOfs(vertices, vert_num, stride, vtype_off)
#				elif vtype == 8:
#					rapi.rpgBindColorBufferOfs(vertices, vert_num, stride, vtype_off, 4)
				elif vtype == 10:				
						rapi.rpgBindUV1BufferOfs(vertices, vert_num, stride, vtype_off)



			vf.seek(face_offset)

			if vert_count > 65535:
				faces = vf.readBytes(face_count * 4)
				rapi.rpgCommitTriangles(faces, noesis.RPGEODATA_UINT, face_count, noesis.RPGEO_TRIANGLE)
			else:
				faces = vf.readBytes(face_count * 2)
				rapi.rpgCommitTriangles(faces, noesis.RPGEODATA_USHORT, face_count, noesis.RPGEO_TRIANGLE)

			rapi.rpgClearBufferBinds()

	try:
		mdl = rapi.rpgConstructModel()
	except:
		mdl = NoeModel()

	mdl.setModelMaterials(NoeModelMaterials(tex_list, mat_list))
#	mdl.setBones(bones)
	mdlList.append(mdl)

	return 1

def Align(value, div):
	mod = value % div

	if mod > 0:
		value += (div - mod)

	return value

def ReadTextures(bs):
    print("Reading textures")

    tex_list = []
    tex_names = []

    bs.seek(0x20)
    tex_count = bs.readUShort()

    name_off = (tex_count * 0x30) + 0x60 + (tex_count * 4) + tex_count
    name_off = Align(name_off, 4)
    bs.seek(name_off)

    for n in range(tex_count):
        bs.seek(name_off + (n * 2))
        text_off = bs.readUShort() + name_off
        bs.seek(text_off)
        tex_names.append(bs.readString())

    bs.seek(0x0c)
    data_start = bs.readUInt() + 0x60
    data_start = Align(data_start, 0x10)

    for t in range(tex_count):
        bs.seek((t * 0x30) + 0x64)
        offset = bs.readUInt() + data_start
        size = bs.readUInt()
        bs.seek(offset)

        # Check if DDS format (header starts with 'DDS ')
        format_check = bs.readBytes(4)
        if format_check == b'DDS ':
            # Use loadTexByHandler to load DDS texture
            bs.seek(offset)  # Ensure pointer is at the start of DDS data
            raw_image_data = bs.readBytes(size)
            texture = rapi.loadTexByHandler(raw_image_data, ".dds")
            if texture:
                texture.name = tex_names[t]
                tex_list.append(texture)
        else:
            bs.seek(offset + 0x100)
            data_size = bs.readUInt()
            width = bs.readUInt()
            height = bs.readUInt()
            raw_image = bs.readBytes(data_size)

            # Assuming BC7 for NXTCH, apply the same decoding
            raw_image = rapi.imageDecodeDXT(raw_image, width, height, noesis.FOURCC_BC7)
            texture = NoeTexture(tex_names[t], width, height, raw_image, noesis.NOESISTEX_RGBA32)
            tex_list.append(texture)

    return tex_list, tex_names
