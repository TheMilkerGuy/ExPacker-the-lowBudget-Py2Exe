from __future__ import print_function, division, absolute_import
import os
import sys
import tempfile
import shutil
from pathlib import Path
import importlib.util

def parse_imports(script_path):
    import ast
    with open(script_path, "r") as file:
        tree = ast.parse(file.read(), filename=script_path)
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)
            for alias in node.names:
                imports.add(f"{node.module}.{alias.name}")
    return imports

def collect_modules(imports):
    modules = {}
    for module in imports:
        try:
            spec = importlib.util.find_spec(module)
            if spec and spec.origin:
                modules[module] = spec.origin
        except ImportError:
            print(f"Module {module} not found.")
    return modules

def package_script_and_modules(script_path, modules, base_exe_path):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        script_dest = temp_path / 'script.py'
        with open(script_path, "r") as script_file:
            script_content = script_file.read()
        with open(script_dest, "w") as script_file:
            script_file.write(script_content)
            script_file.write("\nexit()")
            script_file.write("\n#")
        
        for module, path in modules.items():
            if path and os.path.isfile(path):
                shutil.copy(path, temp_path / Path(path).name)

        with open(base_exe_path, "rb") as base_exe_file:
            base_exe_content = base_exe_file.read()

        output_exe_name = os.path.splitext(os.path.basename(script_path))[0] + '.exe'

        with open(output_exe_name, "wb") as exe_file:
            exe_file.write(base_exe_content)
            exe_file.write(b'# Start embedded files\n')
            
            with open(script_dest, "rb") as script_file:
                exe_file.write(script_file.read())

            for module, path in modules.items():
                if path and os.path.isfile(path):
                    with open(path, "rb") as module_file:
                        exe_file.write(module_file.read())

        os.chmod(output_exe_name, 0o775)
        print(f"Executable created as {output_exe_name}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print('Usage: ExPacker.py -<mode> <file>.py')
        exit(-1)
    
    script_path = sys.argv[2]
    
    if sys.argv[1] == '-con':
        base_exe_path = "structure/_con.exe"
    elif sys.argv[1] == '-win':
        base_exe_path = "structure/_win.exe"
    else:
        print('''
Invalid parameter!
Parameter list:
 -con
 -win
 ''')
        exit(-1)
    
    imports = parse_imports(script_path)
    modules = collect_modules(imports)
    package_script_and_modules(script_path, modules, base_exe_path)
    exit(-1)
