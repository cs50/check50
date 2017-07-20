def get_user_timeline(screen_name, count=5):
    screen_name = screen_name.lstrip("@")
    if (screen_name == "cs50"):
        return ["hello, world!"]
    elif (screen_name == "beatles"):
        return ["All you need is love", "Hey Jude, don't make it bad", "Oh, I believe in yesterday"]
    elif (screen_name == "elphiethedog"):
        return ["I love you but I hate your vacuum",
                "The mailman seems friendly and fun to frighten"]
    else:
        return None
