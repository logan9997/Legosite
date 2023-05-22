import os


class FunctionUsage():

    def __init__(self, parent_folder: str, **kwargs: list[str]) -> None:
        self.parent_folder = parent_folder
        self.skipped_folders = kwargs.get('skipped_folders', [])
        self.files: list = []
        self.functions: list = []

    def extract_folders(self, directories: list, path: str):
        for directory in directories:
            full_path = path + '\\' + directory

            if os.path.isdir(full_path):
                yield directory
            else:
                if directory[-3:] == '.py' and directory != '__init__.py' and full_path != __file__:
                    self.files.append(full_path)

    def parse_through_folders(self, initial_path: str, folders):

        folders = self.extract_folders(folders, initial_path)

        for folder in folders:
            path = initial_path + '\\' + folder

            if folder in self.skipped_folders:
                continue

            try:
                folder_content = os.listdir(path)
                if os.path.isdir(path):
                    folder_content = os.listdir(path)
                    folder_content = self.extract_folders(folder_content, path)

                path: str = path.replace(f'\\{folder}', '')
                try:
                    self.parse_through_folders(
                        path + '\\' + folder, folder_content)
                except RecursionError:
                    pass
            except PermissionError:
                pass

    def get_files(self):
        return self.files

    def get_functions(self):
        for file in self.get_files():
            with open(file, 'r') as read_file:
                lines = read_file.readlines()
                for line in lines:
                    if 'DatabaseManagment' in line:
                        function_name = line.rstrip(r'\n')
                        function_name = function_name.split('(')[0]
                        function_name = function_name.replace('def ', '')
                        function_name = function_name.replace(' ', '')
                        self.functions.append(
                            {
                                'file': file, 
                                'function_name': function_name,
                                'count': 0
                            }
                        )

    def find_function(self, function: str):
        for file in self.get_files():
            with open(file, 'r') as read_file:
                try:
                    lines = read_file.readlines()
                except UnicodeDecodeError:
                    continue
                for line in lines:
                    if function in line:
                        print('FOUND IN - ', file)

    def count_occurances(self):
        for file in self.get_files():
            with open(file, 'r') as read_file:
                lines = read_file.readlines()

                for line in lines:
                    for function in self.functions:
                        if function['function_name'] in line:
                            function['count'] += 1

        for function in self.functions:
            if function['count'] <= 1:
                file = function['file'].replace(self.parent_folder, '')
                print(file, function['function_name'])


def main():
    parent_folder = r'C:\Users\logan\OneDrive\Documents\Programming\Python\apis\BL_API\legosite'
    skipped_folders = ['__pycache__', 'migrations', 'env',
                       'build', 'staticfiles', 'templatetags', '__init__']

    action = input(
        'Find unused functions / Find function location - (U / L): ').upper()

    if action == 'U':

        f = FunctionUsage(parent_folder, skipped_folders=skipped_folders)
        f.parse_through_folders(parent_folder, os.listdir(parent_folder))
        f.get_functions()
        f.count_occurances()

    elif action == 'L':
        function_to_find = input('Function name: ')
        f = FunctionUsage(parent_folder)
        f.parse_through_folders(parent_folder, os.listdir(parent_folder))
        f.find_function(function_to_find)


if __name__ == '__main__':
    main()
