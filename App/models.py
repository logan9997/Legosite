from django.db import models

DATE_FORMAT = '%Y-%m-%d'
DATE_DEFAULT = '1991-01-01'

class Item(models.Model):
    item_id = models.CharField(max_length=20, primary_key=True)
    item_name = models.CharField(max_length=200)
    year_released = models.IntegerField()
    item_type = models.CharField(max_length=1, choices=(
        ("M","minifig"), ("S", "set")
    ))
    views = models.IntegerField()


class Price(models.Model):
    price_record = models.AutoField(primary_key=True)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    date = models.DateField(DATE_FORMAT, blank=True, null=True, default=DATE_DEFAULT)
    avg_price = models.FloatField()
    min_price = models.FloatField()
    max_price = models.FloatField()
    total_quantity = models.IntegerField()


class Theme(models.Model):
    theme_id = models.AutoField(primary_key=True)
    theme_path = models.CharField(max_length=140)
    item = models.ForeignKey(Item, on_delete=models.CASCADE,blank=True, null=True)


class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=16, unique=True) #USERNAME MUST BE UNIQUE
    email = models.EmailField()
    password = models.CharField(max_length=22)
    email_preference = models.CharField(max_length=14, default="All", choices=(
        ("Never", "Never"), ("Occasional", "Occasional"),
        ("All", "All")
    ))
    region = models.CharField(max_length=60, default='None')


class Portfolio(models.Model):
    portfolio_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    condition = models.CharField(max_length=1, choices=(
        ("U", "used"), ("N", "new")
    ))
    date_added = models.DateField(DATE_FORMAT, null=True)
    bought_for = models.FloatField(null=True)
    sold_for = models.FloatField(null=True)
    date_sold = models.DateField(DATE_FORMAT, null=True)
    notes = models.CharField(max_length=300, null=True)


class Watchlist(models.Model):
    entry = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    date_added = models.DateField(DATE_FORMAT)


class Piece(models.Model):
    piece_id = models.CharField(max_length=40, primary_key=True)
    piece_name = models.CharField(max_length=360)
    type = models.CharField(max_length=20, choices=(
        ("MINIFIG", "MINIFIG"), ("PART", "PART"), ("SET", "SET"), ("GEAR", "GEAR"),
        ("CATALOG", "CATALOG"), ("INSTRUCTION", "INSTRUCTION"), ("UNSORTED_LOT", "UNSORTED_LOT"),
        ("ORIGINAL_BOX", "ORIGINAL_BOX")
    ))


class PieceParticipation(models.Model):
    participation = models.AutoField(primary_key=True)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    piece = models.ForeignKey(Piece, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    colour_id = models.CharField(max_length=40)


class SetParticipation(models.Model):
    participation = models.AutoField(primary_key=True)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="item")
    set = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="set")
    quantity = models.IntegerField()