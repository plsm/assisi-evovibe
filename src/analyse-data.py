#PYTHONPATH=/home/pedro/cloud/Dropbox/ASSISIbf/evovibe/src python /home/pedro/cloud/Dropbox/ASSISIbf/evovibe/src/analyse-data.py
# This script processes the data produced by the evovibe program.  The
# evolutionary algorithm produces three files:
#
# * evaluation.csv - contains chromosome evaluations. Each row contains the
#   "generation" number, the episode index, the evaluation index within the
#   episode, the index of the selected arena, the index of the active CASU,
#   the chromosome genes.
#
# * population.csv - contains the populations of the evolutionary algorithm.
#   Each row contains the generation number, the episode index, the
#   chromosome genes.
#
# * fitness.csv - contains the fitness of the chromosomes in the
#   populations of the evolutionary algorithm.  Each row contains the
#   generation number, the fitness value, the chromosome genes.
#
# Pedro Mariano 2016
# ASSISIbf

import master
import evaluator
import config

import argparse
import csv
import matplotlib.pyplot
import numpy

MAX_EVALUATION_VALUE = 60
NUMBER_EVALUATIONS_PER_CHROMOSOME = 3
FREQUENCY_DOMAIN = [300, 1500]

def read_csv_file (filename):
    fp = open (filename, "r")
    freader = csv.reader (fp, delimiter = ',', quoting = csv.QUOTE_NONNUMERIC, quotechar = '"')
    header = freader.next ()
    data = [row for row in freader]
    fp.close ()
    return (header, data)

def read_evaluation_file ():
    return read_csv_file ("evaluation.csv")

def read_population_file ():
    return read_csv_file ("population.csv")

def read_fitness_file ():
    return read_csv_file ("fitness.csv")

def colorise (sequence):
    h = max (sequence)
    l = min (sequence)
    c1 = (h - l) / 3 + l
    c2 = 2 * (h - l) / 3 + l
    import matplotlib.colors
    print matplotlib.colors.from_levels_and_colors (levels = [l, c1, c2, h], colors = ['blue', 'red', 'green'])
    # def torgb (x):
    #     if x < c1:
            
    #         return 
    return [str ((x - l) / (h - l)) for x in sequence]

def summarise_fitness (fitness):
    def row_result ():
        rr = [generation]
        for v in data:
            rr.extend ([numpy.mean (v), numpy.std (v)])
        return rr
    number_genes = len (fitness [0]) - master.FIT_CHROMOSOME_GENE
    result = []
    generation = fitness [0][master.FIT_GENERATION]
    data = [[] for _ in xrange (number_genes + 1)]
    for row in fitness:
        if row [master.FIT_GENERATION] != generation:
            # nextd = [generation] + [sum (v) for v in data] + [numpy.std (v) for v in data]
            # print '---------------------'
            # print data
            # print '---------------------'
            # print nextd
            # print '---------------------'
            #result.append ([generation] + [numpy.mean (v) for v in data] + [numpy.std (v) for v in data])
            result.append (row_result ())
            generation = row [master.FIT_GENERATION]
            data = [[] for _ in xrange (number_genes + 1)]
        for index in xrange (number_genes):
            data [index].append (row [master.FIT_CHROMOSOME_GENE + index])
        data [number_genes].append (row [master.FIT_FITNESS])
        # print "  grow to  ", data
    #result.append ([generation] + [numpy.mean (v) for v in data] + [numpy.std (v) for v in data])
    result.append (row_result ())
    return result

SUMEVA_GENERATION = 0
SUMEVA_MEAN = 1
SUMEVA_STDDEV = 2
SUMEVA_MIN = 3
SUMEVA_MAX = 4
SUMEVA_CHROMOSOME_GENES = 5

def summarise_evaluation (evaluation):
    result = []
    data = []
    index = 0
    for row in evaluation:
        data.append (row [evaluator.EVA_VALUE])
        index += 1
        if index == NUMBER_EVALUATIONS_PER_CHROMOSOME:
            index = 0
            genes = row [evaluator.EVA_CHROMOSOME_GENES:]
            generation = row [evaluator.EVA_GENERATION]
            result.append ([generation, numpy.mean (data), numpy.std (data), min (data), max (data)] + genes)
            data = []
    return result

def plot_value_vs_chromosome_gene (evaluation, chromosome_gene_index, chromosome_gene_name, subtitle = '', chromosome_gene_domain = None):
    matplotlib.pyplot.clf ()
    matplotlib.pyplot.scatter (
        [r [evaluator.EVA_CHROMOSOME_GENES + chromosome_gene_index] for r in evaluation],
        [r [evaluator.EVA_VALUE] for r in evaluation],
        c = [r [evaluator.EVA_GENERATION] for r in evaluation],
        edgecolors = 'face',
        alpha = 0.5
        )
    cb = matplotlib.pyplot.colorbar ()
    cb.set_label ('generation')
    matplotlib.pyplot.title ('evaluation value versus %s \n%s' % (chromosome_gene_name, subtitle))
    matplotlib.pyplot.xlabel (chromosome_gene_name)
    matplotlib.pyplot.ylabel ('value')
    matplotlib.pyplot.ylim ([0, MAX_EVALUATION_VALUE])
    if chromosome_gene_domain is not None:
        matplotlib.pyplot.xlim ([chromosome_gene_domain [0] - 10, chromosome_gene_domain[1] + 10])
    matplotlib.pyplot.savefig ('value-VS-%s.png' % chromosome_gene_name)

def plot_fitness_vs_chromosome_gene (summarised_evaluation, chromosome_gene_index, chromosome_gene_name, subtitle = '', chromosome_gene_domain = None):
    matplotlib.pyplot.clf ()
    matplotlib.pyplot.scatter (
        [r [SUMEVA_CHROMOSOME_GENES + chromosome_gene_index] for r in summarised_evaluation],
        [r [SUMEVA_MEAN] for r in summarised_evaluation],
        c = [r [SUMEVA_GENERATION] for r in summarised_evaluation],
        edgecolors = 'face',
        alpha = 0.5
        #'o'
        )
    cb = matplotlib.pyplot.colorbar ()
    cb.set_label ('generation')
    matplotlib.pyplot.title ('fitness versus %s\n%s' % (chromosome_gene_name, subtitle))
    matplotlib.pyplot.xlabel (chromosome_gene_name)
    matplotlib.pyplot.ylabel ('fitness')
    matplotlib.pyplot.ylim ([0, MAX_EVALUATION_VALUE])
    if chromosome_gene_domain is not None:
        matplotlib.pyplot.xlim ([chromosome_gene_domain [0] - 10, chromosome_gene_domain[1] + 10])
    matplotlib.pyplot.savefig ('fitness-VS-%s.png' % chromosome_gene_name)


def plot_value_range_vs_chromosome_gene (summarised_evaluation, chromosome_gene_index, chromosome_gene_name, subtitle = '', chromosome_gene_domain = None):
    # max_generations = max ([r [SUMEVA_GENERATION] for r in summarised_evaluation])
    # colors = [(2.0 * r [SUMEVA_GENERATION] / max_generations if r [SUMEVA_GENERATION] <  max_generations / 2 else 1.0 ,
    #            2.0 * (max_generations - r [SUMEVA_GENERATION]) / max_generations if r [SUMEVA_GENERATION] >= max_generations / 2 else 1.0 ,
    #                0.0) for r in summarised_evaluation]
    # for c in colors:
    #     print c, "\t",
    # print
    matplotlib.pyplot.clf ()
    matplotlib.pyplot.vlines (
        [r [SUMEVA_CHROMOSOME_GENES + chromosome_gene_index] for r in summarised_evaluation],
        [r [SUMEVA_MIN] for r in summarised_evaluation],
        [r [SUMEVA_MAX] for r in summarised_evaluation],
        colors = 'black'
        )
    pc = matplotlib.pyplot.scatter (
        [r [SUMEVA_CHROMOSOME_GENES + chromosome_gene_index] for r in summarised_evaluation],
        [r [SUMEVA_MEAN] for r in summarised_evaluation],
        c = [r [SUMEVA_GENERATION] for r in summarised_evaluation],
        edgecolors = 'face',
        alpha = 0.5
        )
    print pc.get_cmap ()
    cb = matplotlib.pyplot.colorbar ()
    cb.set_label ('generation')
    matplotlib.pyplot.title ('value range versus %s\n%s' % (chromosome_gene_name, subtitle))
    matplotlib.pyplot.xlabel (chromosome_gene_name)
    matplotlib.pyplot.ylabel ('value')
    matplotlib.pyplot.ylim ([0, MAX_EVALUATION_VALUE])
    if chromosome_gene_domain is not None:
        matplotlib.pyplot.xlim ([chromosome_gene_domain [0] - 10, chromosome_gene_domain[1] + 10])
    #matplotlib.pyplot.colorbar (colors)
    matplotlib.pyplot.savefig ('value-range-VS-%s.png' % chromosome_gene_name)
    
def plot_population_fitness_vs_generation (summarised_fitness, subtitle = ''):
    xs = [r [0] for r in summarised_fitness]
    matplotlib.pyplot.clf ()
    matplotlib.pyplot.fill_between (
        [r [0] for r in summarised_fitness],
        [r [-2] + r[-1] for r in summarised_fitness],
        [r [-2] - r[-1] for r in summarised_fitness],
        facecolor = 'red',
        alpha = 0.5)
    matplotlib.pyplot.plot (
        xs,
        [r [-2] for r in summarised_fitness],
        '-'
        )
    matplotlib.pyplot.title ('population fitness\n' + subtitle)
    matplotlib.pyplot.xlabel ('generation')
    matplotlib.pyplot.ylabel ('fitness')
    matplotlib.pyplot.savefig ('population-fitness.png')

def plot_chromosome_gene_vs_generation (summarised_fitness, chromosome_gene_index, chromosome_gene_name, subtitle = '', chromosome_gene_domain = None):
    xs = [r [0] for r in summarised_fitness]
    ymean = [r [1 + 2 * chromosome_gene_index] for r in summarised_fitness]
    ystdv = [r [1 + 2 * chromosome_gene_index + 1] for r in summarised_fitness]
    matplotlib.pyplot.clf ()
    matplotlib.pyplot.fill_between (
        xs,
        [m + s for m, s in zip (ymean, ystdv)],
        [m - s for m, s in zip (ymean, ystdv)],
        facecolor = 'red',
        alpha = 0.5)
    matplotlib.pyplot.plot (
        xs,
        ymean,
        '-'
        )
    matplotlib.pyplot.title ('chromosome gene %s\n%s' % (chromosome_gene_name, subtitle))
    matplotlib.pyplot.xlabel ('generation')
    matplotlib.pyplot.ylabel (chromosome_gene_name)
    if chromosome_gene_domain is not None:
        matplotlib.pyplot.ylim ([chromosome_gene_domain [0] - 10, chromosome_gene_domain[1] + 10])
    matplotlib.pyplot.savefig ('population-%s.png' % (chromosome_gene_name))


def plot_histogram_fitness_noise (summarised_evaluation, subtitle):
    """For each chromosome evaluation compute the difference between lowest
    and highest value.  The bigger this difference, noisier is the fitness
    function.
    """
    noise = [s [SUMEVA_MAX] - s [SUMEVA_MIN] for s in summarised_evaluation]
    matplotlib.pyplot.clf ()
    matplotlib.pyplot.hist (noise, bins = MAX_EVALUATION_VALUE + 1)
    matplotlib.pyplot.xlim ([0, MAX_EVALUATION_VALUE])
    matplotlib.pyplot.title ('Histogram of distance between lowest and highest evaluation value\n' + subtitle)
    matplotlib.pyplot.savefig ('histogram-fitness-noise.png')

def plot_evaluation_value_vs_episode_iteration (evaluation, subtitle, config):
    """
    Plot the evaluation value versus episode iteration to check how tired bees are or if they are behaving as sitters."""
    matplotlib.pyplot.clf ()
    matplotlib.pyplot.scatter (
        [r [evaluator.EVA_ITERATION]  for r in evaluation],
        [r [evaluator.EVA_VALUE]      for r in evaluation],
        c = [r [evaluator.EVA_GENERATION] for r in evaluation],
        edgecolors = 'face',
        alpha = 0.5
        )
    matplotlib.pyplot.title ('evaluation value vs episode iteration\n' + subtitle)
    matplotlib.pyplot.xlabel ('iteration')
    matplotlib.pyplot.ylabel ('value')
    matplotlib.pyplot.xlim ([-0.5, config.number_evaluations_per_episode + 0.5])
    matplotlib.pyplot.ylim ([0, MAX_EVALUATION_VALUE])
    cb = matplotlib.pyplot.colorbar ()
    cb.set_label ('generation')
    matplotlib.pyplot.savefig ('evaluation-value-VS-episode-iteration.png')
    
def parse_arguments ():
    parser = argparse.ArgumentParser (
        description = 'Analyse data produced by the evovibe program',
        argument_default = None
    )
    parser.add_argument (
    '--subtitle', '-s',
        default = '',
        type = str,
        help = 'subtitle to add to all graphs'
    )
    parser.add_argument (
    '--config', '-c',
        default = '',
        type = str,
        help = 'configuration file name'
    )
    return parser.parse_args ()

subtitle = 'with elitism'
#subtitle = 'no elitism'
args = parse_arguments ()
subtitle = args.subtitle
cfg = config.Config (args.config)

evaluation = read_evaluation_file ()
fitness = read_fitness_file ()
sf = summarise_fitness (fitness [1])
se = summarise_evaluation (evaluation [1])
#print se
plot_value_vs_chromosome_gene (evaluation [1], 0, 'frequency', subtitle, FREQUENCY_DOMAIN)
plot_fitness_vs_chromosome_gene (se, 0, 'frequency', subtitle, FREQUENCY_DOMAIN)
plot_value_range_vs_chromosome_gene (se, 0, 'frequency', subtitle, FREQUENCY_DOMAIN)
plot_population_fitness_vs_generation (sf, subtitle)
plot_chromosome_gene_vs_generation (sf, 0, 'frequency', subtitle, FREQUENCY_DOMAIN)
plot_histogram_fitness_noise (se, subtitle)
plot_evaluation_value_vs_episode_iteration (evaluation [1], subtitle, cfg)
