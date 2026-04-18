import zipfile, sys

path = sys.argv[1] if len(sys.argv) > 1 else "ziBoQ5hq"
try:
    with zipfile.ZipFile(path, "r") as zf:
        print(f"Valid ZIP with {len(zf.namelist())} entries:\n")
        for i, info in enumerate(zf.infolist()[:30]):
            print(f"  {info.file_size:>10,} bytes  {info.filename}")
        if len(zf.namelist()) > 30:
            print(f"  ... and {len(zf.namelist()) - 30} more")
except zipfile.BadZipFile:
    print("Not a valid ZIP file (corrupted or truncated)")
    with open(path, "rb") as f:
        header = f.read(4)
        print(f"Magic bytes: {header.hex()}")
except Exception as e:
    print(f"Error: {e}")
