
def max_fill(grid, capacity):
    total_drops = 0
    for row in grid:
        water_units = sum(row)
        drops = math.ceil(water_units / capacity)
        total_drops += drops
    return total_drops
