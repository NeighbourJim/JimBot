import random

def extreme_stat_gen(min_base_bst, max_base_bst):
    #this version is heavily based on njim's version, but with madi's types system added in
    stats = []
    min_base_bst = int(min_base_bst*1.2)
    # get a random base total to use
    base_bst = random.randint(min_base_bst,max_base_bst)
    # decide the stat weight
    # clamped float value between 0.8 and 1.0, varying based on the base total
    # higher base totals will tend to have higher stat weight
    # On average (over 10000 runs) this process should result in an average BST of about 525, min 280, max 725.
    stat_weight = round(max(min((base_bst / max_base_bst) * 1.5, 1.0), 0.8), 2)
    for i in range(6):
        stat = random.randint(100,200) + random.randint(-65,55)
        if stat >= 100:
            for s in stats:
                if s >= 100:
                    stat -= random.randint(25,80)
                    break
        elif stat <= 100:
            for s in stats:
                if s <= 100:
                    stat += random.randint(15, 80)
                    if s <= 50:
                        stat += random.randint(15, 80)
                    break
        # subtract the stat from the remaining stat total, multiplying by stat weight
        # doing this should get more relatively accurate stat spreads ON AVERAGE (you can still end up with absolutely pathetic stats)
        base_bst -= round(stat * stat_weight)
        if base_bst <= 80:
            stat = random.randint(5,80)
        stats.append(stat)
    return stats

def normal_stat_gen(type, min_base_bst, max_base_bst, soft_stat_min, soft_stat_max):
    #i wrote this all and then kinda forgot what it does
    stats = []
    base_bst = random.randint(min_base_bst,max_base_bst)
    for i in range(6):
        #for the max stat, it takes the remaining BST from the max BST divided by how many stats are left to generate
        max_stat = int((max_base_bst-sum(stats))/(6-i))
        #if this is over the soft stat max, then we roll a random one between 20, and the soft stat max + 30
        if max_stat >= soft_stat_max:
            max_stat = random.randint(20, soft_stat_max+30)
        #for the min stat, we take the remaining BST from the min BST divided by how many stats are left to generate
        min_stat = int((min_base_bst-sum(stats))/(6-i))
        #if its under the soft stat min, we just set it to soft stat min minus 10
        if (min_stat <= soft_stat_min):
            min_stat = soft_stat_min-10
        #and if after that its still over the max stat somehow, we just set it to max stat minus 10
        if (min_stat > max_stat):
            min_stat = max_stat-10
        #and then it rolls an int between those two values, and appends it to the array
        stat = random.randint(min_stat,max_stat)
        stats.append(stat)
    return stats

# Generate Stats
def stat_gen():
    type = random.randint(1, 4)
    types_bst_stuff = [200, 375, 20, 80, 300, 450, 40, 110, 450, 600, 50, 150, 570, 720, 70, 225]
    min_base_bst = types_bst_stuff[(type*4) - 4]
    max_base_bst = types_bst_stuff[(type*4) - 3]
    soft_stat_min = types_bst_stuff[(type*4) - 2]
    soft_stat_max = types_bst_stuff[(type*4) - 1]
    #50% chance to use the extreme stat gen (i.e. njim's old generation but with my "types" system shoehorned in)
    gen = 0
    if type != 1:
        gen = random.randint(0,1)
    if gen == 1:
        stats = extreme_stat_gen(min_base_bst, max_base_bst)
    #and 50% chance to generate a more uniform sorta stats
    #(this was my original "new system" which ended up being a lot more uniform than i'd like, so we're alternating between crazier numbers and more uniform)
    else:
        stats = normal_stat_gen(type, min_base_bst, max_base_bst, soft_stat_min, soft_stat_max)
    #40% chance to bump a stat up so that the BST is a multiple of 5
    sru = 0
    if ((sum(stats) % 5) != 5) and (random.randint(1,5) < 3):
        sru = 1
        stats[random.randint(0,5)] += (5-(sum(stats) % 5))
    random.shuffle(stats)
    stat_total = sum(stats)
    return stats, type, gen, sru

stats, type, gen, sru = stat_gen()
settings_string = ""
if type == 1:
    settings_string += "Generating a Baby Pokemon, "
elif type == 2:
    settings_string += "Generating a Middle Evolution Pokemon, "
elif type == 3:
    settings_string += "Generating a Fully Evolved Pokemon, "
elif type == 4:
    settings_string += "Generating a Legendary Pokemon, "
if gen == 0:
    settings_string += "using Madi's algorithm, "
elif gen == 1:
    settings_string += "using NJim's algorithm, "
if sru == 1:
    settings_string += "with BST rounded up to the nearest multiple of 5..."
elif sru == 0:
    settings_string += "without any BST rounding..."
print(settings_string)
print("HP: " + str(stats[0]))
print("Attack: " + str(stats[1]))
print("Defense: " + str(stats[2]))
print("Special Attack: " + str(stats[3]))
print("Special Defense: " + str(stats[4]))
print("Speed: " + str(stats[5]))
print("BST: " + str(sum(stats)))
