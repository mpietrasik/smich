class Hierarchy:

    #Hierarchy class initializer
    def __init__(self, subsumption_axioms, root_tag):

        self.clusters_by_tag = {}
        self.root = Cluster(root_tag, None)
        self.clusters_by_tag[root_tag] = self.root

        for axiom in subsumption_axioms:
            parent = axiom[0]
            child = axiom[1]
            new_cluster = Cluster(child, self.clusters_by_tag[parent])
            self.clusters_by_tag[child] = new_cluster
    
    #Function returns root
    def get_root(self):

        return self.root

    #Function generates all the paths in the hierarchy
    def generate_paths(self):

        paths = {}
        for cluster in list(self.clusters_by_tag):
            path = []
            current_cluster = self.clusters_by_tag[cluster]
            while current_cluster != None:
                path.insert(0, current_cluster)
                current_cluster = current_cluster.get_parent()
            paths[self.clusters_by_tag[cluster]] = path

        return paths

    #Function prunes the hierarchy as described in the paper
    def prune(self, current_cluster):

        #Prune hierarchy depth first
        to_visit = list(current_cluster.get_children())
        for child in to_visit:
            self.prune(child)

        #Root cluster does not get pruned
        if current_cluster == self.root:
            return

        #If cluster is empty, remove it from hierarchy and continue
        if len(current_cluster.get_subjects()) == 0 and current_cluster != self.root:
            current_cluster.get_parent().get_children().remove(current_cluster)
            return

        #If cluster has empty parent, find first non-empty ancestor and make it the parent
        if len(current_cluster.get_parent().get_subjects()) == 0 and current_cluster.get_parent() != self.root:
            current_cluster.get_parent().get_children().remove(current_cluster)
            ancestor = current_cluster.get_parent()
            while ancestor != self.root:
                if len(ancestor.get_subjects()) > 0:
                    break
                else:
                    ancestor = ancestor.get_parent()
            ancestor.add_child(current_cluster)
            current_cluster.set_parent(ancestor)

        return

class Cluster:
    
    #Cluster class initializer
    def __init__(self, tag, parent = None):

        self.tag = tag
        self.parent = parent
        if self.parent != None:
            parent.add_child(self)
        self.children = []
        self.subjects = []

    #Function returns tag
    def get_tag(self):

        return self.tag
    
    #Function returns parent
    def get_parent(self):

        return self.parent

    #Function sets parent value
    def set_parent(self, parent):

        self.parent = parent

    #Function adds child to cluster
    def add_child(self, child):

        self.children.append(child)

    #Function returns children
    def get_children(self):

        return self.children

    #Function returns subjects
    def get_subjects(self):

        return self.subjects

    #Function returns level
    def get_level(self):

        if self.parent != None:
            return self.parent.get_level() + 1
        
        return 0

    #Functions used for printing of cluster
    def __repr__(self):

        return self.tag

    def __str__(self):

        return self.tag