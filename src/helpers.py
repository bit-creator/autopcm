from enum import Enum, auto

class Status(Enum):
    Undefined    = auto() # status unknown
    Located      = auto() # modules inserted in tree
    Precompiling = auto() # modules under precompilation process
    Precompiled  = auto() # module precompiled and saved
    Compiling    = auto() # module under compilation process
    Done         = auto() # module precompiled and compiled

class FileType(Enum):
    ModuleDefinition     = auto() # defenition of module
    ModuleImplimentation = auto() # module implimentation unit
    ExtraCxx             = auto() # not module file

class Errors(Enum):
    UnknownError = auto() # unrecognized error
    InvalidName  = auto() # some name of module is invalid

class GlobInfo():
    def __init__(self, path, type, target):
        self.path = [path]
        self.type = type
        self.target = target

    def add_path(self, path):
        self.path.append(path)

class ModuleMetaInfo():
    def __init__(self):
        self.name    ="" # Name of module
        self.path    ="" # path to module source
        self.type    ="" # type of file, looks to FileType enum
        self.target  ="" # targets specified in *json for build control
        self.imports =[] # list of module which imported

class MetaDataDump():
    def __init__(self):
        self.file  = ""
        self.pos   = 0
        self.line  = ""

    def clear(self):
        self.file  = ""
        self.pos   = 0
        self.line  = ""

current = MetaDataDump()

class Error():
    def __init__(self):
        self.code  = Errors.UnknownError
        self.line  = ""

    def __init__(self, code):
        self.code  = code
        self.line  = ""

    def __init__(self, code, line):
        self.code  = code
        self.line  = line

    def code2line(self):
        if self.code == Errors.InvalidName: return "Invalid Name"
    
    def dump(self):
        error = current.file + ", " + str(current.pos) + \
        ": error: " + self.code2line() + '\n' + str(current.pos) + \
        "|\t" + self.line
        print(error)

def prefix_test(prefix) -> bool:
    if prefix[0:7] == 'export ': return True
    for ch in prefix:
        if ch != ' ':
            return False
    return True

def suffix_test(suffix) -> bool:
    if suffix == '' or suffix[0] != ';': return False
    return True

def name_test(name) -> bool:
    for ch in name:
        if ch == ' ':
            return False
    return True
    
def name_of_module(string):
    prefix = string.partition('export module ')[0]
    suffix = string.partition('export module ')[2].partition(';')[1]
    name   = string.partition('export module ')[2].partition(';')[0]
    if not prefix_test(prefix): return 'invalid'
    if not suffix_test(suffix): return 'invalid'
    if not name_test(name):     return 'invalid'
    return name

def name_of_import(string):
    prefix = string.partition('import ')[0]
    suffix = string.partition('import ')[2].partition(';')[1]
    name   = string.partition('import ')[2].partition(';')[0]
    if not prefix_test(prefix): return 'invalid'
    if not suffix_test(suffix): return 'invalid'
    if not name_test(name):     return 'invalid'
    return name

def name_of_impl(string):
    prefix = string.partition('module ')[0]
    suffix = string.partition('module ')[2].partition(';')[1]
    name   = string.partition('module ')[2].partition(';')[0]
    if not prefix_test(prefix): return 'invalid'
    if not suffix_test(suffix): return 'invalid'
    if not name_test(name):     return 'invalid'
    return name

def ignore_module(module, ignore_list):
    for mod in ignore_list:
        if module == mod:
            return True
    
    if module.find('<') != -1:
        return True
    if module.find('std') != -1:
        return True

end_preambula_flags = [
    "(", "{", "using=", "using ", "class ",
    "template ", "template<", "namespace ",
    "typedef ", "static ", "constexpr ",
    "inline ", "consteval ", "constinit "
]

def is_preambula_end(line):
    if line == "": return False
    for flag in end_preambula_flags:
        if line.find(flag) != -1: return True
    return False

def update_meta_data(data, line):
    if line.find("import ") != -1:
        name = name_of_import(line)
        if name != "invalid":
            data.imports.append(name)
        else: Error(Errors.InvalidName, line)
        
    if line.find("export module ") != -1:
        name = name_of_module(line)
        if name != "invalid":
            data.name = name
        else: Error(Errors.InvalidName, line)

    if data.type == FileType.ExtraCxx:
        if line.find("module ") != -1:
            name = name_of_impl(line)
            if name != "invalid":
                data.type = FileType.ModuleDefinition
                data.name = name
            else: Error(Errors.InvalidName, line)

def get_meta_data(file):
    global current
    input = open(file, "r")
    current.file = file
    data = ModuleMetaInfo()
    data.path = file
    if file[file.rindex('.'):] == "*cppm":
        data.type = FileType.ModuleDefinition
    elif file[file.rindex('.'):] == "*cpp":
        data.type = FileType.ExtraCxx
    preambula_end = False
    is_comment_line = False
    while not preambula_end:
        line = input.readline()
        if line == "": break
        ++current.pos
        if line.find("//") != -1:
            line = line.partition("//")[0]
        if line.find("/*") != -1:
            pre_comment = line.partition("/*")[0]
            if not is_preambula_end(pre_comment):
                update_meta_data(data, pre_comment)
            else: preambula_end = True
            line = line.partition("/*")[2]
            is_comment_line = True
        if line.find("*/") != -1:
            line = line.partition("*/")[2]
            is_comment_line = False
        if is_comment_line: continue
        if not is_preambula_end(line): update_meta_data(data, line)
        else: preambula_end = True
    return data