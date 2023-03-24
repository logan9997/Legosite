items = [
    ('sw0001a', 'N', 1, 'Battle Droid Tan with Back Plate', None, None), 
    ('sw1024', 'N', 1, 'Luke Skywalker &#40;Pilot, 20th Anniversary Torso&#41;', None, None), 
    ('sw0036a', 'N', 4, 'Imperial Stormtrooper - Light Nougat Head, Solid Mouth Helmet', None, None), 
    ('sw0001c', 'N', 2, 'Battle Droid with One Straight Arm', None, None), 
    ('sw0174', 'N', 1, 'Obi-Wan Kenobi - Old, Light Nougat', None, None), 
    ('sw0001a', 'U', 1, 'Battle Droid Tan with Back Plate', None, None), 
    ('sw0171', 'N', 2, 'Imperial Probe Droid &#40;White Dish Stand, Lever on Top&#41;', None, None), 
    ('sw0100', 'N', 3, 'Anakin Skywalker &#40;Padawan&#41; - Yellow Head', None, None)
]

items = [{
    "item_id":item[0],
    "condition":item[1],
    "quantity":item[2],
    "item_name":item[3],
    "item_type":item[4],
    "year_released":item[5],
} for item in items]

items = sorted(items, key=lambda d:d["quantity"], reverse=True)

print(items)