import yaml
import copy

def identity (x):
    return x

def between (min_value, max_value, x):
    if min_value <= x <= max_value:
        return x
    else:
        raise ValueError ()

def compose (f, g, x):
    return f (g (x))

def list_element (the_list, x):
    sub = lambda x : x - 1
    f = lambda x : between (0, len (the_list) - 1, x)
    return compose (the_list.__getitem__, f, compose (sub, int, x))

def str2bool (x):
    return True if x == 'True' else False

class Parameter:
    def __init__ (self, name, user_prompt, path_in_dictionary = [], default_value = None, parse_data = identity):
        self.name = name
        self.user_prompt = user_prompt
        self.path_in_dictionary = path_in_dictionary
        self.default_value = default_value
        self.parse_data = parse_data
        self.has_value = False
        self.value = None

    def load_from_dictionary (self, dictionary):
        """
        Load a parameter value from the given dictionary.
        """
        try:
            for n in self.path_in_dictionary:
                dictionary = dictionary [n]
            self.value = dictionary [self.name]
        except KeyError as e:
            if self.default_value is None:
                raise e
            else:
                print "Using default value %s for %s!" % (self.default_value, self.name)
                self.value = self.default_value
        finally:
            self.has_value = True

    def ask_user (self):
        while True:
            try:
                self.value = self.parse_data (raw_input (self.user_prompt + '? '))
                self.has_value = True
                return
            except KeyboardInterrupt as e:
                raise e
            except:
                print 'Invalid data!'

class Config:
    def __init__ (self, parameters):
        self.parameters_as_list = copy.copy (parameters)
        self.parameters_as_dict = dict ([(p.name, p) for p in parameters])

    def load_from_yaml_file (self, filename):
        file_object = open (filename, 'r')
        dictionary = yaml.load (file_object)
        file_object.close ()
        for p in self.parameters_as_list:
            p.load_from_dictionary (dictionary)

    def ask_user (self):
        for p in self.parameters_as_list:
            p.ask_user ()

    def to_dictionary (self):
        result = {}
        return result
    
    def __getattr__ (self, name):
        try:
            p = self.parameters_as_dict [name]
        except KeyError:
            raise AttributeError
        if not p.has_value:
            raise AttributeError
        return p.value

    def __str__ (self):
        result = ""
        for p in self.parameters_as_list:
            if p.has_value:
                for b in p.path_in_dictionary:
                    result += b + ' : '
                result += p.name + ' : ' + str (p.value) + '\n'
        return result

if __name__ == '__main__':
    c = Config ([
            Parameter ('number_bees', 'Number of bees', parse_data = int),
            Parameter ('number_generations', 'Number of generations of the evolutionary algorithm', []),
            Parameter ('number_evaluations_per_episode', 'How many evaluations to perform with a set of bees', [])
            ]
                    )
    c.ask_user ()
    print c
    print c.number_bees

