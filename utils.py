from random import shuffle
from os import getcwd
from pathlib import Path

#Function performs smict to induce tag hierarchy
def smict(annotations, vocabulary = None, alpha = 0.7):

    #If vocabulary not given, generate vocabulary
    if vocabulary == None:
        vocabulary = []
        for entity in annotations:
            for tag in annotations[entity]:
                if tag not in vocabulary:
                    vocabulary.append(tag)
    shuffle(vocabulary)
    
    #Initialize and calulate the amount of documents annotated by each tag and tag pair
    D_counts = {}
    D_joint_counts = {}
    for annotation in annotations:
        for tag in annotations[annotation]:
            if tag not in D_counts:
                D_counts[tag] = 1
            else:
                D_counts[tag] += 1
        for tag1 in annotations[annotation]:
            for tag2 in annotations[annotation]:
                if tag1 == tag2:
                    continue
                if (tag1, tag2) not in D_joint_counts:
                    D_joint_counts[(tag1, tag2)] = 1
                else:
                    D_joint_counts[(tag1, tag2)] += 1
                if (tag2, tag1) not in D_joint_counts:
                    D_joint_counts[(tag2, tag1)] = 1
                else:
                    D_joint_counts[(tag2, tag1)] += 1

    #Calculate generality for each tag and sort in descending order
    generality = []
    for tag1 in vocabulary:
        summer = 0
        for tag2 in vocabulary:
            if (tag1, tag2) in D_joint_counts:
                summer += D_joint_counts[(tag1, tag2)] / D_counts[tag2]
        generality.append((tag1, summer))
    generality.sort(key=lambda x: x[1], reverse = True)

    #Initialize taxonomy with the tag with the highest generality
    root_node = generality.pop(0)[0]
    in_graph_children = { root_node: []}
    in_graph_path_up = {root_node : []}

    #Add tags to the taxonomy greedily in descending generality according to the higest similarity
    for entry in generality:
        child_tag = entry[0]
        highest_similarity = -1
        highest_similarity_tag = None

        for potential_parent_tag in in_graph_children:

            similarity = 0
            level = 0
            if (child_tag, potential_parent_tag) in D_joint_counts:
                similarity += (D_joint_counts[(child_tag, potential_parent_tag)] / D_counts[child_tag]) * (alpha ** level)
                level += 1
                
                for upstream_tag in in_graph_path_up[potential_parent_tag]:
                    if (upstream_tag, child_tag) in D_joint_counts:
                        similarity +=  (D_joint_counts[(child_tag, upstream_tag)] / D_counts[child_tag]) * (alpha ** level)
                    level += 1

            if similarity > highest_similarity:
                highest_similarity = similarity + 0
                highest_similarity_tag = potential_parent_tag

        in_graph_children[highest_similarity_tag].append(child_tag)
        in_graph_children[child_tag] = []

        in_graph_path_up[child_tag] = list([highest_similarity_tag]) + list(in_graph_path_up[highest_similarity_tag])

    #Store subsumption axioms
    subsumption_axioms = []
    for node1 in in_graph_children:
        for node2 in in_graph_children[node1]:
            subsumption_axioms.append((node1, node2))

    return subsumption_axioms, root_node

#Function assigns subjects to clusters on hierarchy
def subject_clustering(hierarchy, annotations):

    #Generate a dictionary of all the paths that exist in the hierarchy
    paths = hierarchy.generate_paths()

    #For each subject, find the cluster it most belongs to and assign it to the cluster
    for subject in annotations:
        belonging_cluster = None
        max_belonging = 0
        for leaf_cluster in paths:
            belonging = calculate_belonging(annotations[subject], paths[leaf_cluster])
            if belonging > max_belonging:
                belonging_cluster = leaf_cluster
                max_belonging = belonging + 0

        belonging_cluster.get_subjects().append(subject)

    return hierarchy

#Function returns the Jaccard Index between a subject's tags and a path in the hierarchy
def calculate_belonging(subject_tags, path):
    
    subject_tags = set(subject_tags)
    path = set([cluster.get_tag() for cluster in path])

    return len(subject_tags.intersection(path)) / len(subject_tags.union(path))

#Functions returns dictionary of hierarchy for writing out as a json
def generate_json_hierarchy(hierarchy):
    
    json_hierarchy = {}
    clusters = [hierarchy.get_root()]
    while len(clusters) > 0:
        current_cluster = clusters.pop(0)
        clusters.extend(current_cluster.get_children())
        json_hierarchy[current_cluster.get_tag()] = {}
        json_hierarchy[current_cluster.get_tag()]['subjects'] = current_cluster.get_subjects()
        json_hierarchy[current_cluster.get_tag()]['children'] = [child.get_tag() for child in current_cluster.get_children()]

    return json_hierarchy

#Function writes a pretty printed hierarchy to output_file
def write_hierarchy(output_file, current_cluster):
    
    output_file.write(str('\t' * (current_cluster.get_level())) + '|--------------' + '\n')
    output_file.write(str('\t' * (current_cluster.get_level())) + '| CLUSTER TAG        : ' + current_cluster.get_tag() + '\n')
    output_file.write(str('\t' * (current_cluster.get_level())) + '| CLUSTER SUBJECT(S) : ' + " ".join(current_cluster.get_subjects()) + '\n')
    output_file.write(str('\t' * (current_cluster.get_level())) + '|--------------' + '\n')
    for child in current_cluster.get_children():
        write_hierarchy(output_file, child)

#Function calculates Hie-F1 score
def calculate_hie_f1_score(dataset, subsumption_axioms):

    #Retrieve gold standard subsumption axioms
    gold_standard_axioms = []
    with open(Path(getcwd() + '/datasets/' + dataset + '_gold_standard')) as gold_standard_file:
        lines = gold_standard_file.readlines()
        for line in lines:
            gold_standard_axioms.append((line.strip().lower().split(" ")[0], line.strip().lower().split(" ")[1]))

    #Calculate F1 score between induced and gold standard hierarchies
    subsumption_axioms = set(subsumption_axioms)
    gold_standard_axioms = set(gold_standard_axioms)

    true_positive = len(subsumption_axioms.intersection(gold_standard_axioms))
    false_positive = len(subsumption_axioms.difference(gold_standard_axioms))
    false_negative = len(gold_standard_axioms.difference(subsumption_axioms))

    if (true_positive + (0.5 * (false_positive + false_negative) )) == 0:
        return None

    return true_positive / (true_positive + (0.5 * (false_positive + false_negative)))

#Function returns a dictionary of clusters with all the subjects they inherit
def inherit_subjects(inherited_subjects, current_cluster):
    
    all_descendant_subjects = []
    for child in current_cluster.get_children():
        inherited_subjects, descendant_subjects = inherit_subjects(inherited_subjects, child)
        all_descendant_subjects.extend(descendant_subjects)
    inherited_subjects[current_cluster] = current_cluster.get_subjects() + all_descendant_subjects
    
    return inherited_subjects, inherited_subjects[current_cluster]

#Function calculates Sub-F1 score
def calculate_sub_f1_scores(inherited_subjects, annotations):

    sub_f1_scores = []
    for cluster in inherited_subjects:
        sub_f1_score = calculate_f1(inherited_subjects, annotations, cluster.get_tag(), cluster)
        sub_f1_scores.append(sub_f1_score)

    return sum(sub_f1_scores) / len(sub_f1_scores)

#Function calculates Tag-F1 score
def calculate_tag_f1_scores(inherited_subjects, annotations, vocabulary):

    tag_f1_scores = []
    for tag in vocabulary:
        max_tag_f1_score = 0
        for cluster in inherited_subjects:
            tag_f1_score = calculate_f1(inherited_subjects, annotations, tag, cluster)
            if tag_f1_score == None:
                continue
            if tag_f1_score > max_tag_f1_score:
                max_tag_f1_score = tag_f1_score + 0
        tag_f1_scores.append(max_tag_f1_score)

    return sum(tag_f1_scores) / len(tag_f1_scores)

#Function calculates F1 score, helper function for Sub-F1 and Tag-F1
def calculate_f1(inherited_subjects, annotations, tag, cluster):

    true_positive = 0
    false_positive = 0
    false_negative = 0
    true_negative = 0
    for subject in annotations:
        if subject in inherited_subjects[cluster]:
            if tag in annotations[subject]:
                true_positive += 1
            else:
                false_positive += 1
        else:
            if tag in annotations[subject]:
                false_negative += 1

    if (true_positive + (0.5 * (false_positive + false_negative) )) == 0:
        return None

    return true_positive / (true_positive + (0.5 * (false_positive + false_negative) ))

