from config.config import PAGE_NUM_LIMIT
import time
import os

class General():

    def timer(self, func):
        def inner(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            finish = round(time.time() - start, 5)
            print(f"\n<{func.__name__.upper()}> finished in {finish} seconds.\n")
            return result 
        return inner


    def get_base_url(self, request) -> str:
        return request.get_host().strip(" ")
    

    def configure_relative_file_path(self, file_name:str, max_depth:int) -> str:
        path = file_name
        while True:
            if os.path.exists(path):
                return path
            path = '../' + path

            if path.count('../') >= max_depth:
                raise Exception(f'File {file_name} not found')


    def clean_html_codes(self, string:str):
        codes = {
            "&#41;":")", 
            "&#40;":"(",
            "&#39;": "'"
        }

        for k, v in codes.items():
            if k in string:
                string = string.replace(k ,v)
        return string
    

    def split_capitalize(self, string:str, split_value:str):
        return " ".join(
            list(map(str.capitalize, string.split(split_value)))
        )
    

    def sort_items(self, items, sort , **order) -> list[dict]:
        sort_field = sort.split("-")[0]
        order = {"asc":False, "desc":True}[sort.split("-")[1]]
        items = sorted(items, key=lambda field:field[sort_field], reverse=order)
        return items


    def sort_dropdown_options(self, options:list[dict[str,str]], field:str) -> list[dict[str,str]]:
        #loop through all options. If options["value"] matches to desired sort field, assign to variable
        selected_field = [option for option in options if option["value"] == field]

        #default, if code above fails 
        if selected_field == []:
            print("\n\nFAILS - <sort_dropdown_options>\n\n")
            selected_field = options[0]
        else:
            selected_field = selected_field[0]
        
        #push selected element to front of list, remove its old position
        options.insert(0, options.pop(options.index(selected_field)))
        
        return options
    
    
    def check_page_boundaries(self, current_page, list_len:int, items_per_page:int) -> int:
        try:
            current_page = int(current_page)
        except:
            return 1

        conditions = [
            current_page <= list_len // items_per_page,
            current_page > 0,
        ]

        if not all(conditions):
            return 1
        
        return current_page


    def slice_num_pages(self, list_len:int, current_page:int, items_per_page:int):
        num_pages = [i+1 for i in range((list_len // items_per_page ) + 1)]
        last_page = num_pages[-1] -1

        list_slice_start = current_page - (PAGE_NUM_LIMIT // 2)
        list_slice_end = current_page - (PAGE_NUM_LIMIT // 2) + PAGE_NUM_LIMIT 

        if list_slice_end > len(num_pages):
            list_slice_end = len(num_pages) -1
            list_slice_start = list_slice_end - PAGE_NUM_LIMIT
        if list_slice_start < 0 :
            list_slice_end -= list_slice_start
            list_slice_start = 0

        num_pages = num_pages[list_slice_start:list_slice_end]

        #remove last page. if len(items) % != 0 by ITEMS_PER_PAGE -> blank page with no items
        if list_len % items_per_page == 0:
            num_pages.pop(-1)

        if 1 not in num_pages:
            num_pages.insert(0, 1)

        if last_page not in num_pages:
            num_pages.append(last_page)

        if 0 in num_pages:
            num_pages.remove(0)

        if len(num_pages) == 1:
            return []

        return num_pages
        

    def save_post_params(self, request, post_params:list[str]) -> dict:
        for param in post_params:
            if request.POST.get(param) != None:
                request.session[param] = request.POST.get(param)
        request.session.modified = True
        return request
    

    def clear_post_params(self, request, post_params:list[str]):
        for param in post_params:
            if param in request.session:
                del request.session[param]
        request.session.modified = True
        return request
    