from selenium import webdriver
from selenium.webdriver.common.by import By
from database import DatabaseManagment


class Scraper():

    def __init__(self) -> None:
        self.driver = webdriver.Chrome()
        self.url = "https://www.bricklink.com/catalogTree.asp?itemType=S"
        self.db = DatabaseManagment()


    def setup(self) -> None:
        self.driver.get(self.url)
        #click cookies
        self.driver.find_element(By.XPATH, """//*[@id="js-btn-save"]/button[2]""").click()


    def get_item_ids(self, theme_link, item_type) -> dict:

        theme_details = {"M":[],"S":[]}

        self.driver.get(theme_link)
        #get the number of items for current theme
        try:
            num_items = int(self.driver.find_element(By.XPATH, '//*[@id="id-main-legacy-table"]/tbody/tr/td/table/tbody/tr[3]/td/div/div[2]/div[2]/b[1]').text)
        #if num items cannot be found there is one item in the theme
        except:
            #add the single item id to list and set num items to 0 so loop does not start
            path_containter = self.driver.find_element(By.XPATH, '/html/body/div[3]/center/table/tbody/tr/td/section/div/table/tbody/tr/td[1]').text
            item_id = path_containter.split(": ")[-1]
            theme_details[item_type].append(item_id)
            num_items = 0

        #reset values    
        page_counter = 1
        row_counter = 2

        for i in range(num_items):
            #click next page if 50th item on page is parsed
            if row_counter % 50 == 0 and num_items != 50:
                page_counter += 1
                row_counter = 2
                
                #select next page
            
                next_page_bar = self.driver.find_element(By.XPATH, '//*[@id="id-main-legacy-table"]/tbody/tr/td/table/tbody/tr[3]/td/div/div[2]/div[1]')
                next_page_link = next_page_bar.find_elements(By.CSS_SELECTOR, 'a')
                if len(next_page_link) != 0:
                    next_page_link[-1].click()

                #if not items where found. Should not happen! Code here for procossion
                page_not_found_check = self.driver.find_element(By.XPATH, '//*[@id="id-main-legacy-table"]/tbody/tr/td/table/tbody/tr[3]/td/div/div[1]/div').text
                if "No items were found." in page_not_found_check:
                    print(self.driver.current_url, theme_link, num_items)
                    
            #select the item id from current row
            try: 
                item_id = self.driver.find_element(By.XPATH, f'//*[@id="ItemEditForm"]/table[1]/tbody/tr/td/table/tbody/tr[{row_counter}]/td[2]/font/a[1]').text
                print(item_id)
                theme_details[item_type].append(item_id)
            except:pass
            #move onto the next item on the page
            row_counter += 1

        return theme_details


    def get_theme_ids(self) -> None:
        #call database functions
        db = DatabaseManagment()

        #get all entries from item table to check if themes data have already been recorded
        theme_entries = db.fetch_theme_details()
        
        #create empty list which will be populated with dicts containing {M:[...], S:[...], path:"..."}
        theme_details_list = []

        #loop through each item type
        for item_type in ["M"]: #,'S' 
            #get the catalog page for each item type
            if item_type == "S":
                self.driver.get(f'https://www.bricklink.com/catalogTree.asp?itemType=S#dacta')
            else:
                self.driver.get(f'https://www.bricklink.com/catalogTree.asp?itemType=M')

            #get all theme names from themes table.
            table = self.driver.find_element(By.XPATH, '//*[@id="id-main-legacy-table"]/tbody/tr/td/table/tbody/tr[3]/td/table/tbody/tr/td/table/tbody/tr[2]')
            themes = [theme for theme in table.text.rsplit("\n")]

            #remove {more} as it is not a url to a catalog page
            if r"     {more}" in themes:
                themes.remove(r"     {more}")

            #remove (num) of items in theme from theme name. Some themes have '(', ')' in their name e.g. '(other)'
            #loop backwards of each theme:str and find the first '(' char. Split the string at that position
            for theme_index, theme in enumerate(themes):
                for char_index, char in enumerate(theme[::-1].strip("     ")):
                    if char == "(":
                        theme_name = theme[:len(theme)-char_index-2]
                        #replace theme names with name without brackets
                        themes[theme_index] = theme_name
                        break

            #get all hyperlinks to all themes catalog page, displaying a list of all items 
            theme_links_table = self.driver.find_element(By.XPATH, '//*[@id="id-main-legacy-table"]/tbody/tr/td/table/tbody/tr[3]/td/table/tbody/tr/td/table/tbody/tr[2]')
            theme_links = theme_links_table.find_elements(By.CSS_SELECTOR, f'a[href*="catalogList.asp?catType="]')
            #remove any links which are '{...}'
            theme_links = [theme.get_attribute("href")for theme in theme_links if "{" not in theme.text]

            #set default lists
            parents = [] ; details = []
            print(len(themes), len(theme_links))

            #loop through each theme, create the path, click link then parse through all item ids.
            for index, theme in enumerate(themes):

                #find first char in theme name to split.
                for char in theme:
                    if char != " ":
                        first_letter = char
                        break
                
                #the number of spaces before each theme to determine if it is a child theme of a parent / sub theme.
                num_spaces = len(theme.split(first_letter)[0])

                #if a new parent theme, reset the list
                if num_spaces == 0:
                    parents = []

                #store a list of dicts storing "theme" and "num_spaces" to compare current theme with previous theme(s)
                details.append({"theme":theme.strip("     ") + "//", "num_spaces":num_spaces})

                #if a new level of indentaion is reached add the current theme as a new sub-parent theme
                if details[index]["num_spaces"] > details[index-1]["num_spaces"]:
                    parents.append(details[index-1]["theme"])

                #if the previous themes spaces is < than current themes spaces the remove last element from parents as it is not a parent to any sub themes
                elif details[index]["num_spaces"] < details[index-1]["num_spaces"] and len(parents) > 0:
                    parents.pop(-1)

                #complete the path "parent//sub/sub-sub"
                theme_path = "".join(parents) + theme.strip("     ")

                #some theme_paths have ' in theme causing errors in SQL statement
                if "'" in theme_path:
                    theme_path = theme_path.replace("'", "")

                #loop through results from database to see if theme details has already been recorded
                entry_in = False
                for theme_entries_details in theme_entries:
                    if theme_entries_details == (item_type, theme_path):
                        entry_in = True
                        break

                #if entry is not recored then record the data (get item ids)
                if not entry_in:
                    #SCRAPE ITEM IDS, adds all item ids to dict for the current item type. Also resets for each theme
                    theme_details = self.get_item_ids(theme_links[index], item_type)

                    #add the theme path to dict containing S / M list
                    theme_details.update({
                            "path": theme_path,
                        })
                    print(theme_details)

                    #ADD TO DATABASE
                    db.add_theme_details(theme_details, item_type)

                    #add path and id to the dict which already contains lists of sets and minifigs END OF LOOP
                    theme_details_list.append(theme_details)

class ImageScrape():

    def __init__(self) -> None:
        self.driver = webdriver.Chrome()
        self.url = "https://www.bricklink.com/catalogTree.asp?itemType=S"
        self.db = DatabaseManagment()


    def loop_through_images(self):
        self.item_ids = self.db.get_pieces_colours()[1901:]
        directory = r"C:\Users\logan\OneDrive\Documents\Programming\Python\apis\BL_API\Website\App\static\App\images"
        import time, requests, os
        for item in self.item_ids:
            #1 = type, #0 = item_id
            
            url = f"https://img.bricklink.com/ItemImage/PN/{item[1]}/{item[0]}.png"
            img_name = directory + fr"/{item[1]}_{item[0]}.png"
            if img_name not in os.listdir(directory):
                print(item[0])
                img_data = requests.get(url).content
                with open(img_name, "wb") as handler:
                    handler.write(img_data)

        self.driver.quit()


def main():
    '''
    cd OneDrive/Documents/programming/python/api's/bl_api/
    python -m pipenv shell
    '''
    scraper = ImageScrape()
    scraper.loop_through_images()
    # scrape = Scraper()
    # scrape.setup()
    # scrape.get_theme_ids()

if __name__ == "__main__":
    main()

