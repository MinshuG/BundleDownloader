def string_between(string, start, end):
    return string[string.index(start) + len(start):string.index(end)]

class IniOpen:
    def __init__(self, file):
        self.parse = {}
        self.file = file
        self.open = open(file, "r")
        self.f_read = self.open.read()
        split_content = self.f_read.split("\n")

        section = ""
        pairs = ""

        for i in range(len(split_content)):
            if split_content[i].find("[") != -1:
                section = split_content[i]
                section = string_between(section, "[", "]")  # define your own function
                self.parse.update({section: []})
            elif split_content[i].find("[") == -1 and split_content[i].find("="):
                pairs = split_content[i]
                if len(pairs) <= 1:
                    continue
                split_pairs = pairs.split("=")
                key = split_pairs[0].strip()
                value = split_pairs[1].strip()
                # if 
                self.parse[section].append({key: value})

    def read(self, section, key):
        try:
            result = []
            for k in self.parse[section]:
                if k.get(key, None) is not None:
                    result.append(k.get(key))
            return result
        except KeyError:
            return None

    def write(self, section, key, value):
        if self.parse.get(section) is  None:
            self.parse.update({section: {}})
        elif self.parse.get(section) is not None:
            if self.parse[section].get(key) is None:
                self.parse[section].update({key: value})
            elif self.parse[section].get(key) is not None:
                return None

# https://stackoverflow.com/questions/8884188/how-to-read-and-write-ini-file-with-python3