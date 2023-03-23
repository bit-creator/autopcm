import os

class Compiler_abstraction:
    def __init__(self, settings) -> None:
        self.build_directory    = settings['build_directory']
        self.prebuild_directory = settings['build_directory'] + 'precompiled/'
        self.prebuild_cache     = settings['build_directory'] + 'cache/'
        self.bin_directory      = settings['build_directory'] + 'bin/'
        self.targets            = settings['targets']

        if not os.path.exists(self.build_directory):
            os.mkdir(os.path.join(os.getcwd(), self.build_directory))
        if not os.path.exists(self.prebuild_directory):
            os.mkdir(os.path.join(os.getcwd(), self.prebuild_directory))
        if not os.path.exists(self.prebuild_cache):
            os.mkdir(os.path.join(os.getcwd(), self.prebuild_cache))
        if not os.path.exists(self.bin_directory):
            os.mkdir(os.path.join(os.getcwd(), self.bin_directory))

        self.static_line = [
            settings['compiler'],
            '-std=c++' + str(settings['standart']),
            '-stdlib=' + settings['stdlib'],
            '-g3' if settings['build'] == 'Debug' else '-O3',
            '-fmodules'
        ]

        self.static_line.extend(settings['flags'])

        self.ignore_list =[]

        for target in settings['targets']:
            if 'extra_pcm_dir' in target:
                for dir in target['extra_pcm_dir']:
                    self.static_line.extend(['-fprebuilt-module-path=' + dir])
                    for name in os.listdir(dir):
                        path = os.path.join(dir, name)
                        if os.path.isfile(path):
                            if path[path.rindex('.'):] == '.pcm':
                                self.ignore_list.extend([name.partition('.pcm')[0]])

        self.static_line.extend([
            '-fprebuilt-module-path=' + self.prebuild_directory,
            '-fmodules-cache-path=' + self.prebuild_cache
        ])

    def precompile(self, module, module_path):
        call = [*self.static_line]

        call.extend([
            '-c', '--precompile', module_path, '-o',
            self.prebuild_directory + module + '.pcm'
        ])

        return call

    def compile(self, module, module_path, no_import=False):
        call = [*self.static_line]
        if no_import: call.remove('-fmodules')

        call.extend([
            '-c', module_path, '-o', self.bin_directory +
            module + '.o'
        ])

        return call

    def link_static(self, target):
        pass

    def link_dynamic(self, target):
        pass

    def link_executable(self, target, obj):
        output_path = target['output_path']
        if not len(output_path) > 0:
            output_path = '.'
        if output_path[-1] != '/': output_path += '/'
        output_name = target['output_name']
        call = [*self.static_line]
        libraries =[]
        if 'link_libraries' in target:
            libraries = target['link_libraries']
            libraries = ["-l" + l for l in libraries]

        call.extend([
            *libraries, *obj, '-o', output_path + output_name
        ])

        return call
