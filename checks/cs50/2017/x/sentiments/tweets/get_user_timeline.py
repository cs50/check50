tweets = {
    "cs50": ["hello, world"],
    "beatles": ["All you need is love", "Hey Jude, don't make it bad", "Oh I believe in yesterday"],
    "elphiethedog": ["I love you but I hate your vaccum", "The mailman seems friendly and fun to frighten"],
    "subwords": ["The zealous zealout has zeal"],
    "captainkirk": ["like your great... great... great... great... great... grandfather used to",
                    "the enormous... danger, potential... in any contact with life",
                    "intelligence... as fantastically advanced, as this",
                    "do I hear... a negative vote?"
                   ]

}

def get_user_timeline(screen_name, **kwargs):
    return tweets.get(screen_name.lstrip("@"))
