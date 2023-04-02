def get_string_hash(string):
    # We do our own terrible hash because python's hash() is nondeterministic across application restarts
    strhash = 0
    for char in string:
        num = ord(char)
        strhash += num
        strhash += (strhash << 10)
        strhash ^= (strhash >> 6)
    strhash += (strhash << 3)
    strhash ^= (strhash >> 11)
    strhash += (strhash << 15)
    return strhash

def get_random_color_for_str_hsv(string):
    hashed = get_string_hash(string)
    
    hue = ((hashed >> 16) % 255) / 255
    saturation = 0.1 + (((hashed >> 8) % 255) / 255) * 0.9
    value = 0.5 + (((hashed) % 255) / 255) * 0.5
    return [hue, saturation, value]

def hsv_to_rgb(color):
    hue, saturation, value = color
    def f(n):
        k = (n + hue*6) % 6
        return value - value * saturation * max(0, min(k, 4-k, 1))
    return (f(5) * 255, f(3) * 255, f(1) * 255)
    
def get_rgb_luminance(color):
    p_colors = []
    for n in color:
        n = n/255.0
        if n <= 0.04045:
            p_colors.append(n/12.92)
        else:
            p_colors.append(((n+0.055)/1.055)**2.4)
    return 0.2126 * p_colors[0] + 0.7152 * p_colors[1] + 0.0722 * p_colors[2]

def get_text_color_for_background(bg_color):
    luminance = get_rgb_luminance(bg_color)
    if luminance > 0.3:
        return (0, 0, 0)
    else:
        return (255, 255, 255)