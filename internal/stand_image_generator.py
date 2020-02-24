import sys
from PIL import Image, ImageDraw, ImageFont

# TEXT COORDS
# POWER: 185,45
# SPEED: 300,115
# RANGE: 300,250
# DURABILITY: 185,315
# PRECISION: 70,250
# POTENTIAL: 70,115

# POLYGON COORDS

class StandImageGenerator():

    def __init__(self):
        self.text_coords = {    
            "power": (185,45),    
            "speed": (300,115),    
            "range": (300,250),    
            "durability": (185,315),    
            "precision": (70,250),    
            "potential": (70,115)
            }
        self.polygon_coords = {
            "power": {"∞": (198,70), "S": (198,95), "A":(198,111), "B":(198,130), "C":(198,150), "D":(198,170), "E":(198,185)},
            "speed": {"∞":(330,125),"S":(290,150), "A":(280,155), "B":(260,166), "C":(245,175), "D":(230,185), "E":(215,190)},
            "range": {"∞":(330,277),"S":(290,260), "A":(280,250), "B":(260,240), "C":(245,230), "D":(230,220), "E":(215,210)},
            "durability": {"∞":(198,350),"S":(198,310), "A":(198,295), "B":(198,275), "C":(198,255), "D":(198,240), "E":(198,220)},
            "precision": {"∞":(69,275),"S":(105,255), "A":(119,248), "B":(135,238), "C":(150,229), "D":(167,220), "E":(180,210)},
            "potential": {"∞":(69,125),"S":(105,148), "A":(119,156), "B":(135,165), "C":(150,175), "D":(167,185), "E":(180,193)}
        }

    def GenerateImage(self, stats_dict, colour):
        try:
            base = Image.open('./internal/data/images/statsbg.png').convert('RGBA')
            background = Image.new('RGBA', base.size, (255,255,255,255))
            font = ImageFont.truetype("arial.ttf", 40)
            txt = Image.new('RGBA', base.size, (0,0,0,0))
            poly = Image.new('RGBA', base.size)
    
            bg = ImageDraw.Draw(background)
            bg.rectangle([(0,0), background.size], fill=(251,251,250,255))
            d = ImageDraw.Draw(txt)
            d.text(self.text_coords["power"], stats_dict["power"], font=font, fill=(0,0,0,255))
            d.text(self.text_coords["speed"], stats_dict["speed"], font=font, fill=(0,0,0,255))
            d.text(self.text_coords["range"], stats_dict["range"], font=font, fill=(0,0,0,255))
            d.text(self.text_coords["durability"], stats_dict["durability"], font=font, fill=(0,0,0,255))
            d.text(self.text_coords["precision"], stats_dict["precision"], font=font, fill=(0,0,0,255))
            d.text(self.text_coords["potential"], stats_dict["potential"], font=font, fill=(0,0,0,255))
    
            p = ImageDraw.Draw(poly)
            p.polygon([self.polygon_coords["power"][stats_dict["power"]],self.polygon_coords["speed"][stats_dict["speed"]],self.polygon_coords["range"][stats_dict["range"]],self.polygon_coords["durability"][stats_dict["durability"]],self.polygon_coords["precision"][stats_dict["precision"]],self.polygon_coords["potential"][stats_dict["potential"]]], fill=colour, outline=(0,0,0,255))
    
            out = Image.alpha_composite(background, txt)
            out = Image.alpha_composite(out,poly)
            out = Image.alpha_composite(out,base)
    
            out.save('./internal/data/images/stand.png')
            return True
        except Exception as ex:
            return ex

stand_gen = StandImageGenerator()
