#!/usr/local/bin/python3.9
import asyncio
from helpers import Status
import helpers as Utils
import os
import progressbar
import json
import sys
from compiler_abstraction import Compiler_abstraction
import argparse
import subprocess

global_references ={}
queue = []
compiling = 0
precompiling = 0

glob_metadata_list = {}

# /todo: provide target to class which cpllect data of target(all in *json)

class Module():
    def __init__(self, meta) -> None:
        glob_metadata_list.pop(meta.name)
        self.path = meta.path
        self.type = meta.target_t
        self.file_type = meta.type
        self.target = meta.target
        self.status = Status.Undefined
        self.name = meta.name
        self.dependency =[]

        if self.file_type >= Utils.FileType.ExtraCxx:
            self.status = Status.Precompiled

        for name in meta.imports:
            if Utils.ignore_module(name, compiler.ignore_list):
                continue

            if name not in global_references:
                global_references[name] = Module(glob_metadata_list[name])

            self.dependency.append(global_references[name])


    def update_existed(self):
        for dep in self.dependency:
            dep.update_existed()
        if all(dep.status in (Status.Precompiled, Status.Done) for dep in self.dependency):
            pcm_file_path = os.path.join(compiler.prebuild_directory, self.name + '.pcm')
            obj_file_path = os.path.join(compiler.bin_directory, self.name + '.o')
            if os.path.exists(pcm_file_path):
                pcm_mod = os.path.getmtime(pcm_file_path)
                origin_mod = os.path.getmtime(self.path)
                if pcm_mod > origin_mod:
                    self.status = Status.Precompiled
            if os.path.exists(obj_file_path):
                obj_mod = os.path.getmtime(obj_file_path)
                origin_mod = os.path.getmtime(self.path)
                if obj_mod > origin_mod:
                    self.status = Status.Done
            
    def start_if_ready(self):
        if self.status in (Status.Precompiling, Status.Compiling, Status.Done):
            return

        if self.file_type >= Utils.FileType.ExtraCxx:
            if all(depend.status in (Status.Precompiled, Status.Compiling, Status.Done) \
                   for depend in self.dependency):
                self.status = Status.Compiling
                task = asyncio.create_task(self.compile())
                queue.append(task)
        elif self.status == Status.Precompiled:
            self.status = Status.Compiling
            task = asyncio.create_task(self.compile())
            queue.append(task)
        else:
            if all(depend.status in (Status.Precompiled, Status.Compiling, Status.Done) \
                   for depend in self.dependency):
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
                *compiler.compile(self.name, self.path, \
                                  self.file_type == Utils.FileType.PureCxx),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
            out, err = await proc.communicate()
            bar.message(out.decode().strip())
            bar.message(err.decode().strip())
            bar.increment2(self.path)
        self.status = Status.Done

def init_global_metadata(root, target, type):
    for name in os.listdir(root):
        path = os.path.join(root, name)

        if not os.path.isfile(path):
            init_global_metadata(path, target, type)
        elif path.endswith(".cppm") or path.endswith(".cpp"):
            metadata = Utils.get_meta_data(path, target, type)
            glob_metadata_list[metadata.name] = metadata

if __name__ == "__main__":
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

    cmdline.add_argument('--rebuild', required=False, action='store_true', help="Boolean flag indicate full rebuild")
    cmdline.add_argument('--clean', required=False, action='store_true', help="Clean build files [experimental support]")

    args = cmdline.parse_args()
    settings = json.load(open(args.settings))
    compiler = Compiler_abstraction(settings)

    if args.clean:
        if os.path.exists(settings["build_directory"]):
            subprocess.run(['rm', '-rf', settings["build_directory"]])
        exit()

    for target in settings['targets']:
        for root in target['root_directory']:
            init_global_metadata(root, target["name"], target["type"])

    for target in settings['targets']:
        global_references[target['name']] = \
            Module(Utils.get_meta_data(target["entry_point"], target['name'], target['type']))

    glob_metadata_list_tmp = glob_metadata_list.copy()
    for name, md in glob_metadata_list_tmp.items():
        if md.type >= Utils.FileType.ExtraCxx:
            global_references[name] = Module(md)

    for target in settings['targets']:
        if not args.rebuild: global_references[target['name']].update_existed()

    precompiling = sum(1 for ref in global_references.values() \
                       if ref.status not in (Status.Done, Status.Precompiled))
    compiling = sum(1 for ref in global_references.values() \
                    if ref.status is not Status.Done and ref.type != 'Header-only')

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
                        obj = []
                        for name, ref in global_references.items():
                            if ref.target == target['name']:
                                obj.append(compiler.bin_directory + ref.name + '.o')
                        proc = await asyncio.create_subprocess_exec(
                            *compiler.link_executable(target, obj),
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE)
                        out, err = await proc.communicate()
                        bar.message(out.decode().strip())
                        bar.message(err.decode().strip())
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