#!/usr/local/bin/python3.9
import asyncio
from helpers import Status
from helpers import GlobInfo
import helpers as Utils
import os
import progressbar
import json
import sys
from compiler_abstraction import Compiler_abstraction
import argparse
from collections import namedtuple

global_references ={}
global_pathes ={}
linkage_lists ={}
extra_cpp_files = []
queue = []
compiling = 0
precompiling = 0

glob_metadata_list = {}
glob_extra_cpp_list = []

cmdline = argparse.ArgumentParser(prog="autopcm",
                                  description="This utility analyse \
                                  dependencies in your C++ modules and \
                                  precompile with your own settings")

cmdline.add_argument('--settings', required=True, help="*.json file with build configuration")
cmdline.add_argument('--output', required=False, help="File for compiler output [not supported]")
if sys.version_info >= (3, 9):
    cmdline.add_argument('--parallel', required=False, action=argparse.BooleanOptionalAction, default=True, help="enable multithread build process")
else: 
    cmdline.add_argument('--parallel', required=False, action='store_true', default=True, help="enable multithread build process")
    cmdline.add_argument('--no-parallel', required=False, action='store_true', default=False, help="disable multithread build process")

cmdline.add_argument('--rebuild', required=False, action='store_true', help="Boolean flag indicate full rebuild [not supported]")
cmdline.add_argument('--clean', required=False, action='store_true', help="Clean build files [not supported]")

args = cmdline.parse_args()
settings = json.load(open(args.settings))
compiler = Compiler_abstraction(settings)
stdout =[]
stderr =[]
Output = namedtuple("Output", ["stdout", "stderr"])
compiler_output=Output(stdout, stderr)

# /todo: provide target to class which cpllect data of target(all in *json)

def init_global_metadata(root, type, target):
    for name in os.listdir(root):
        path = os.path.join(root, name)
        if os.path.isfile(path):
            metadata = Utils.get_meta_data(path)
            if metadata.type != Utils.FileType.ExtraCxx:
                glob_metadata_list[metadata.name] = metadata
            else: glob_extra_cpp_list.append(metadata)
        else: init_global_metadata(path, type, target)


def init_global_pathes(root, type, target):
        for name in os.listdir(root):
            path = os.path.join(root, name)
            if os.path.isfile(path):
                if path[path.rindex('.'):] == '.cpp':
                    input = open(path)
                    isImplUnit = False
                    for line in input.readlines():
                        if line.find('module') != -1:
                            isImplUnit = True
                            module = Utils.name_of_impl(line)
                            if module != 'invalid':
                                if module in global_pathes.keys(): global_pathes[module].add_path(path)
                                else: global_pathes[module] = GlobInfo(path, type, target)
                            else: extra_cpp_files.extend(GlobInfo(path, type, target))
                            break
                    if not isImplUnit: extra_cpp_files.extend(GlobInfo(path, type, target))
                if path[path.rindex('.'):] == '.cppm':
                    input = open(path)
                    for line in input.readlines():
                        if line.find('export module') != -1:
                            module = Utils.name_of_module(line)
                            if module != 'invalid':
                                if module in global_pathes.keys(): global_pathes[module].add_path(path)
                                else: global_pathes[module] = GlobInfo(path, type, target)
                            break
            else: init_global_pathes(path, type, target)

for target in settings['targets']:
    global_pathes[target['name']] = GlobInfo(target['entry_point'], target['type'], target['name'])

    for root in target['root_directory']:
        init_global_pathes(root, target['type'], target['name'])

class Module():
    def __init__(self, info) -> None:
        self.path = info.path[0]
        self.type = info.type
        self.target = info.target
        self.status = Status.Undefined
        self.dependency =[]

        metadata = Utils.get_meta_data(self.path)
        self.name       = metadata.name
        self.objname = self.name + '.o'

        for name in metadata.imports:
            if not Utils.ignore_module(name, compiler.ignore_list):
                if not name in global_references:
                    global_references[name] = Module(global_pathes[name])
                self.dependency.append(global_references[name])
    
        # print(Utils.get_meta_data(self.path).__dict__)


        
        # input = open(self.path)

        # for line in input.readlines():
        #     if line.find('export module') != -1:
        #         self.name = Utils.name_of_module(line)
                
        #     if line.find('import') != -1:
        #         name = Utils.name_of_import(line)
        #         if name == 'invalid': print('line contained uncorect import' , line)
        #         else:
        #             if not Utils.ignore_module(name, compiler.ignore_list):
        #                 if not name in global_references:
        #                     global_references[name] = Module(global_pathes[name])
        #                 self.dependency.append(global_references[name])
            
    def update_existed(self):
        for dep in self.dependency:
            dep.update_existed()
        all_dependency_ready = True
        for dep in self.dependency:
            if not (dep.status == Status.Precompiled or dep.status == Status.Done): 
                all_dependency_ready = False
        if all_dependency_ready:
            if os.path.exists(os.path.join(compiler.prebuild_directory, self.name + '.pcm')):
                pcm_mod = os.path.getmtime(os.path.join(compiler.prebuild_directory, self.name + '.pcm'))
                origin_mod = os.path.getmtime(self.path)
                if pcm_mod > origin_mod: self.status = Status.Precompiled
                if os.path.exists(os.path.join(compiler.bin_directory, self.name + '.o')):
                    obj_mod = os.path.getmtime(os.path.join(compiler.bin_directory, self.name + '.o'))
                    if obj_mod > origin_mod: self.status = Status.Done
            

    def start_if_ready(self):
        if self.status == Status.Precompiling: return
        if self.status == Status.Compiling:    return
        if self.status == Status.Done:         return
        if self.status == Status.Precompiled:
            self.status = Status.Compiling
            task = asyncio.create_task(self.compile())
            queue.append(task)
            return

        ready = True
        for depend in self.dependency:
            if not (depend.status == Status.Precompiled\
            or depend.status == Status.Compiling\
            or depend.status == Status.Done):
                ready = False
        if ready:
            self.status = Status.Precompiling
            task = asyncio.create_task(self.precompile())
            queue.append(task)

    async def precompile(self):
        proc = await asyncio.create_subprocess_exec(
            *compiler.precompile(self.name, self.path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
        out, err = await proc.communicate()
        bar.message(out.decode().strip())
        bar.message(err.decode().strip())
        bar.increment(self.name)
        self.status = Status.Precompiled

    async def compile(self):
        if self.type != 'Header-only':
            proc = await asyncio.create_subprocess_exec(
                *compiler.compile(self.name, self.path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
            out, err = await proc.communicate()
            bar.message(out.decode().strip())
            bar.message(err.decode().strip())
            bar.increment2(self.path)
        self.status = Status.Done

    async def link(self):
        isTarget = False

        for target in settings['targets']:
            if target['name'] == self.name:
                isTarget = True
                break
        
        if not isTarget: return

        if self.type != 'Header-only':
            proc 
            if self.type == "Executable":     
                proc = await asyncio.create_subprocess_exec(
                    *compiler.link_executable(target),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE)
            if self.type == "Dynamic_library":
                proc = await asyncio.create_subprocess_exec(
                    *compiler.link_dynamic(target),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE)
            if self.type == "Static_library": 
                proc = await asyncio.create_subprocess_exec(
                    *compiler.link_static(target),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE)        
            out, err = await proc.communicate()
            bar.message(out.decode().strip())
            bar.message(err.decode().strip())

for target in settings['targets']:
    global_references[target['name']] = Module(global_pathes[target['name']])
    global_references[target['name']].update_existed()

for ref in global_references:
    if global_references[ref].status != Status.Done:
        if global_references[ref].status != Status.Precompiled:
            precompiling += 1
        if global_references[ref].type != 'Header-only':
            compiling += 1

print("nested pcm:", precompiling)
print("nested obj:", compiling)

bar = progressbar.ProgressBar(precompiling, compiling)

async def loop():
    global queue
    is_repeat = compiling != 0
    while(is_repeat):
        for ref in global_references:
            global_references[ref].start_if_ready()
            if not args.parallel:
                for q in queue:
                    await q

        if args.parallel:
            done, pending = await asyncio.wait(queue, return_when=asyncio.FIRST_COMPLETED)
            queue = [x for x in queue if x not in done]

        is_repeat = False
        for target in settings['targets']:
            if global_references[target['name']].status != Status.Done:
                is_repeat = True
            else:
                if target['type'] != "Header-only":
                    if target['type'] == "Executable":
                        obj = [global_references[target['name']].objname]
                        dep = global_references[target['name']]
                        def allobj(obj, dep):
                            for d in dep.dependency:
                                allobj(obj, d)
                                obj.append(d.objname)
                        allobj(obj, dep)
                        compiler.link_executable(target, obj)
                    if target['type'] == "Dynamic_library": compiler.link_dynamic(target)
                    if target['type'] == "Static_library":  compiler.link_static(target)

async def main():
    task1 = asyncio.create_task(bar.launch())
    task2 = asyncio.create_task(bar.update_symbol())
    task3 = asyncio.create_task(loop())
    await task1
    await task2
    await task3

asyncio.run(main())