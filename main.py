from argparse import ArgumentParser
from hierarchy import Hierarchy
from json import dump
from os import listdir, getcwd
from pathlib import Path
from utils import smict
from utils import generate_json_hierarchy
from utils import write_hierarchy
from utils import calculate_hie_f1_score
from utils import calculate_sub_f1_scores
from utils import calculate_tag_f1_scores
from utils import subject_clustering
from utils import inherit_subjects

if __name__ == '__main__':

    #Set decay factor, alpha, and dataset
    argument_parser = ArgumentParser(description='Generate subsumption axioms for document-tag pairs')
    argument_parser.add_argument('-d', '--dataset', help='Name of dataset in datasets directory', default='dbpedia50000')
    argument_parser.add_argument('-a', '--alpha', help='Float value of the alpha hyperparameter (default = 0.7)', default=0.7, type=float)
    argument_parser.add_argument('-m', '--metrics', help='Boolean value indicating whether or not to calculate metrics', default=False, type=bool)
    arguments = argument_parser.parse_args()

    dataset = arguments.dataset
    alpha = arguments.alpha
    metrics = arguments.metrics

    if alpha < 0.0 or alpha > 1:
        raise ValueError('Alpha value must be between 0 and 1 inclusive.')

    annotations = {}
    vocabulary = []
    #Read in dataset into annotations and vocabulary
    for filename in listdir(getcwd() + '/datasets/' + dataset):
        with open(Path(getcwd() + '/datasets/' + dataset + '/'+ filename), encoding='utf-8') as input_file:
            lines = input_file.readlines()
            assert len(lines) == 1
            annotations[filename] = lines[0].lower().strip().split(" ")
            for tag in annotations[filename]:
                if tag not in vocabulary:
                    vocabulary.append(tag)

    #Run smict, the first part of the algorithm
    subsumption_axioms, root_tag = smict(annotations, vocabulary, alpha)

    #Initialize hierarchy from subsumption axioms
    hierarchy = Hierarchy(subsumption_axioms, root_tag)

    #Perform subject clustering, the second part of our algorithm
    hierarchy = subject_clustering(hierarchy, annotations)

    #Prune the tree of empty clusters, the final part of our algorithm
    hierarchy.prune(hierarchy.get_root())

    #Write pretty printed hierarchy and json summary of hierarchy
    with Path('smich_cluster_hierarchy_' + dataset).open('w', encoding="utf-8") as output_file:
        write_hierarchy(output_file, hierarchy.get_root())

    with open('smich_cluster_hierarchy_json_' + dataset, 'w') as json_file:
        dump(generate_json_hierarchy(hierarchy), json_file)

    #Calculate metrics if specified in command line
    if metrics:

        average_hie_f1_score = calculate_hie_f1_score(dataset, subsumption_axioms)
        print('Hie-F1 Score :', average_hie_f1_score)

        inherited_subjects, descendant_entities = inherit_subjects({}, hierarchy.get_root())
            
        average_sub_f1_score = calculate_sub_f1_scores(inherited_subjects, annotations)
        print('Sub-F1 Score :', average_sub_f1_score)

        average_tag_f1_scores = calculate_tag_f1_scores(inherited_subjects, annotations, vocabulary)
        print('Tag-F1 Score :', average_tag_f1_scores)
