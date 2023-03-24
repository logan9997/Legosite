

def get_star_wars_fig_ids() -> list[str]:
    path = r"C:\Users\logan\OneDrive\Documents\Programming\Python\WebScraping\BricklinkPriceDataTracker\data\itemIDsList.txt"
    with open(path, "r") as file:
        fig_ids = file.readlines()
    return [f.rstrip("\n") for f in fig_ids]


def get_price_colour(change) -> str:
    if change > 0:
        return "green"
    elif change < 0:
        return "red"
    else:
        return "gray"