import json
from check50 import *


class Scratch(Checks):

    @check()
    def valid(self):
        """project exists and is valid Scratch program"""
        self.require("project.sb2")

        # Ensure that unzipped .sb2 file contains .json file
        self.spawn("unzip project.sb2").exit()
        self.require("project.json")

    @check("valid")
    def two_sprites(self):
        """project contains at least two sprites"""
        project = json.loads(File("project.json").read())

        # Loop over children: includes sprites and stages.
        num_sprites = sum("costumes" in child for child in project["children"])

        if num_sprites < 2:
            raise Error("Only {} sprite{} found, 2 required.".format(num_sprites,
                "" if num_sprites == 1 else "s"))

    @check("valid")
    def non_cat(self):
        """project contains a non-cat sprite"""
        project = json.loads(File("project.json").read())
        non_cat = False

        # As a heuristic, only the cat has a "meow" sound.
        for child in project["children"]:

            # Skip over any non-sprites (e.g. backdrops).
            if "costumes" not in child:
                continue

            # Check if the sprite has a "meow" sound.
            can_meow = any(sound["soundName"] == "meow" for sound in child.get("sounds", []))

            # If it doesn't meow, we've found a non-cat sprite.
            if not can_meow:
                return

        # If we haven't returned, then no non-cat sprite found.
        raise Error("Requires a non-cat sprite.")

    @check("valid")
    def three_scripts(self):
        """project contains at least three scripts"""
        project = json.loads(File("project.json").read())

        # Add up scripts from each sprite or backdrop.
        num_scripts = sum(len(child.get("scripts", [])) for child in project["children"])

        if num_scripts < 3:
            raise Error("Only {} script{} found, 3 required.".format(num_scripts,
                "" if num_scripts == 1 else "s"))

    @check("valid")
    def uses_condition(self):
        """project uses at least one condition"""
        project = json.loads(File("project.json").read())

        # Search project scripts for an if or if/else block.
        if not project_contains_keywords(project, ["doIf", "doIfElse"]):
            raise Error("No conditions found, 1 required.")

    @check("valid")
    def uses_loop(self):
        """project uses at least one loop"""
        project = json.loads(File("project.json").read())

        # Search project scripts for a repeat, repeat until, or forever block.
        if not project_contains_keywords(project, ["doRepeat", "doUntil", "doForever"]):
            raise Error("No loops found, 1 required.")

    @check("valid")
    def uses_variable(self):
        """project uses at least one variable"""
        project = json.loads(File("project.json").read())

        # Look for global variables.
        if project.get("variables"):
            return

        # Look for local-to-sprite variables.
        if not any(child.get("variables") for child in project["children"]):
            return

        # If we've reached this point, no variable found.
        raise Error("No variables found, 1 required.")

    @check("valid")
    def uses_sound(self):
        """project uses at least one sound"""
        project = json.loads(File("project.json").read())

        # Search scripts for a sound block.
        keywords = ["playSound:", "doPlaySoundAndWait", "playDrum", "noteOn:duration:elapsed:from:"]
        if not project_contains_keywords(project, keywords):
            raise Error("No sounds found, 1 required.")

def project_contains_keywords(project, keywords):
    """Returns True if project contains at least one of the keywords."""

    # Iterate over all sprites and backdrops.
    for child in project["children"]:

        # Perform a DFS on each script looking for keywords.
        if any(contains(script, keywords) for script in child.get("scripts", [])):
            return True

    return False

def contains(script, keywords):
    """Performs DFS on the script to determine if keyword exists."""

    # The keyword must be the first item in a list.
    if type(script) != list or not script:
        return False

    if script[0] in keywords:
        return True

    # Iterate over all children.
    return any(contains(child, keywords) for child in script)
