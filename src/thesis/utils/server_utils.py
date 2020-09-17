import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET

import random
random.seed(42)

SETUP_MODE = 0
GET_GOOD_SENTENCES = 3

alignment_doc_iten = "./en-it.xml"
alignment_doc_sven = "./en-sv.xml"
alignment_doc_svit = "./it-sv.xml"


# Utility method to retrieve the correct alignment file (from the OPUS corpus)
# The current available language pairs are:
# iten - Italian/English
# sven - Swedish/English
# svit - Italian/Swedish
def __get_alignment_doc(lang):
	if lang == 'iten':
		return alignment_doc_iten
	elif lang == 'sven' :
		return alignment_doc_sven
	elif lang == 'svit':
		return alignment_doc_svit
	return None


debug = False



# SETUP MODE


# Parses file from the OPUS corpus
def __read_st_file(filename):
	tree = ET.parse(filename)
	root = tree.getroot()
	res = {}
	for node in root: 
		if node.tag == 's':
			id = int(node.attrib['id'])
			text = []
			for child in node:
				if child.tag == 'w':
					text.append(child.text)
			if text and not text[0].isalnum():
				text = text[1:]
			if text and not text[-1].isalnum():
				text = text[:-1]
			text = ' '.join(text).strip()
			res[id] = text
		elif node.tag == 'meta':
			pass
	return res


# Obtains the ids of the sentences in string format
def __compose_seg(obj, ids):
	if len(ids):
		a = []
		for id in ids:
			a.append(obj[int(id)])
		return ' '.join(a).strip()
	else:
		return None


# Methods to obtain the aligned sentences from the OPUS corpus.
# The sentences will be written in a file in the format 'sent_lang1 ||| sent_lang2'
# That can be used to run eflomal
def get_sentence_alignment(output_file, lang, num_docs):
	tree = ET.parse(__get_alignment_doc(lang))
	ces_align = tree.getroot()
	available_ids = range(len(ces_align))

	i=1
	while i > 0:
		output_file=str(i) + "_" + output_file
		if not os.path.exists(output_file):
			break
		else:
			i+=1
			if debug:
				print("Found: ", output_file)
	
	if num_docs:
		previous_ids_list = []
		previous_ids = 'random_ids_' + lang + '.txt'
		if os.path.exists(previous_ids):
			with open(previous_ids) as p_f:
				for line in p_f.readlines():
					for p_id in line.split(","):
						if p_id.isdigit():
							previous_ids_list.append(int(p_id))
		if previous_ids_list:
			available_ids = [x for x in available_ids if x not in previous_ids_list]
		random_ids=random.sample(available_ids, num_docs)
		with open(previous_ids,"a") as r_out:
			r_out.write(",".join([str(val) for val in random_ids]))
			r_out.write(',\n')
	else:
		random_ids = available_ids

	with open(output_file, "a") as f:
		for doc_id in random_ids:
			if debug:
				print("Parsing doc:", doc_id)
			doc=ces_align[doc_id]
			try:
				from_doc = doc.attrib['fromDoc']
				from_doc = from_doc[:from_doc.index(".gz")]
				to_doc = doc.attrib['toDoc']
				to_doc = to_doc[:to_doc.index(".gz")]
				if os.path.exists(from_doc) and os.path.exists(to_doc):
					o_src = __read_st_file(from_doc)
					o_trg = __read_st_file(to_doc)
					write_sentence_alignment(doc, doc_id, o_src, o_trg, f)
			except Exception:
				print(sys.exc_info())
				print(doc.attrib)
				continue
		
	if os.path.exists(output_file):
		print(output_file)
	else:
		print('Error creating file')


# Serializes the output of get_sentence_alignment
def write_sentence_alignment(doc, doc_id, o_src, o_trg, out):
	for link in doc:  
		id = link.attrib['id']
		ids = link.attrib['xtargets'].split(';')
		id_source = [x for x in ids[0].split(' ') if x]
		id_target = [x for x in ids[1].split(' ') if x]						
		overlap = float(link.attrib['overlap']) if 'overlap' in link.attrib else None
		if id_source and id_target and overlap > 0.50:
			out.write(str(doc_id) + "." + id + "|||" + __compose_seg(o_src, id_source) + " ||| " + __compose_seg(o_trg, id_target) + "\n")



# GET_GOOD_SENTENCES


#POS to ignore in the matching
ignore_pos = ['AUX','DET','PUNCT']


# Parses the ID, saved as ID_DOC.ID_SENT in the serialized sentences
def __parse_id(id):
	ids = id.split(".")
	if len(ids) != 2:
		if debug:
			print("Format error, expected 'id_document.id_sentence'")
		return
	id_doc = ids[0]
	id_sent = ids[1]
	return id_sent, id_doc


# Retrieves the correct from and to documents from the OPUS corpus and the ids of 
# The aligned sentences. Every alignment can be composed by one or more sentences
def __get_parsed_sentence(ces_align, id_sent, id_doc):
	doc=ces_align[int(id_doc)]
	from_doc = doc.attrib['fromDoc']
	from_doc = from_doc[:from_doc.index(".gz")]
	to_doc = doc.attrib['toDoc']
	to_doc = to_doc[:to_doc.index(".gz")]
	id_source = None
	id_target = None

	for link in doc:  
		id = link.attrib['id']
		if id == id_sent:
			ids = link.attrib['xtargets'].split(';')
			id_source = [x for x in ids[0].split(' ') if x]
			id_target = [x for x in ids[1].split(' ') if x]
			break

	return from_doc, to_doc, id_source, id_target


# Retrieves the sentence tree from the correct document in the OPUS corpus, given the sentence ID 
def __get_sentence_from_id(filename, id_sent):
	tree = ET.parse(filename)
	root = tree.getroot()
	nodes = []
	for node in root:
		if node.tag == 's':
			id = node.attrib['id']
			if id in id_sent:
				nodes.append(node)
		elif node.tag == 'meta':
			pass
	return nodes


# From the aligned sentences and the output of the word alignment (created with eflomal)
# Selects the sentences according to:
# - Best match between the POS of the target and source words
# - Presence of a finite verb
def get_good_sentences(lang, sent_file, word_file_f, word_file_r, output_file):
	tree = ET.parse(__get_alignment_doc(lang))
	ces_align = tree.getroot()
	try:
		with open(sent_file) as sentence_file:
			with open(word_file_f) as word_file_f:
				with open(word_file_r) as word_file_r:
					with open(output_file, "a") as out:
						sentences = sentence_file.readlines()
						words_f = word_file_f.readlines()
						words_r = word_file_r.readlines()
						for i in range(len(sentences)):
							if i < len(words_f) and i < len(words_r):
								f_trees = check_good_alignment(ces_align, sentences[i], words_f[i])
								r_trees = check_good_alignment(ces_align, sentences[i], words_r[i])
								if f_trees and r_trees:
									sections1 = get_sections(f_trees[0])
									sections2 = get_sections(f_trees[1])
									if sections1 and sections2:
										out.write(sentences[i])
										out.write("1.")
										out.write(sections1)
										out.write("\n")
										out.write("2.")
										out.write(sections2)
										out.write("\n")
	except Exception:
		print(sys.exc_info())
		
	if os.path.exists(output_file):
		print(output_file)
	else:
		print('Error writing good sentences file')


def explore_node(node, all_nodes, section, sections):
	if node.deps:
		for child in node.deps:
			child_node = all_nodes[child.id]
			if child_node.is_core_element():
				new_section = [child_node]
				sections.append(new_section)
				explore_node(child_node, all_nodes, new_section, sections)
			else:
				section.append(child_node) 
				explore_node(child_node, all_nodes, section, sections)
    

def get_sections(tree):
	nodes = {}
	roots = []   
	for n in tree:
		if not n.is_ignore():
			for n2 in tree:
				if n2.head == n.id and not n2.is_ignore():
					n.add_dep(n2)
			nodes[n.id] = n
			if n.head == "0":
				roots.append(n)
	sections = []
	for root in roots:          
		root_section = [root]
		sections.append(root_section)
		explore_node(root, nodes, root_section, sections)

	res = ""
	for section in sections:
		at_least_one_match = False
		for el in section:
			if el.aligned_id:
				at_least_one_match = True
			res += str(el)
		if not at_least_one_match:
			# Does not consider the POS to ignore
			remove_ignore = [x for x in section if x.pos not in ignore_pos and x.pos != 'PRON']
			if len(remove_ignore) > 0:
				if debug:
					print("Section without a match")
				return None
		res += '||'
	return res


pos_regexes = [re.compile(".*NOUN"), re.compile(".*PROPN"), re.compile(".*VERB"), re.compile(".*CCONJ"), re.compile(".*SCONJ"), re.compile(".*INTJ")]

deprel_regexes = [re.compile(".*compound"), re.compile(".*name"), re.compile(".*mwe"), re.compile(".*goeswith"), re.compile(".*aux"), re.compile(".*auxpass"), re.compile(".*case")]

deprel_regexes_core = [re.compile(".*nsubj"), re.compile(".*nsubjpass"), re.compile(".*csubj"), re.compile(".*csubjpass"), re.compile(".*ccomp"), re.compile(".*xcomp"), re.compile(".*obj"), re.compile(".*iobj"), re.compile(".*obl")]

class Node:
	def __init__(self, id):
		self.id = id
		self.aligned_id = None
		self.head = None
		self.deprel = None
		self.pos = None
		self.word = None
		self.lemma = None
		self.deps = []

	def set_aligned_id(self, aligned_id):
		self.aligned_id = aligned_id

	def set_head(self, head):
		self.head = head

	def set_deprel(self, deprel):
		self.deprel = deprel

	def set_pos(self, pos):
		self.pos = pos

	def add_dep(self, dep):
		self.deps.append(dep)
        
	def set_word(self, word):
		self.word = word

	def set_lemma(self, lemma):
		self.lemma = lemma

	def __eq__(self, obj):
		if isinstance(obj, Node):
			return self.id == obj.id
		return self.id == obj

	def __str__(self):
		return '{' + self.id + '-' + self.word + '-' + self.lemma + '-' + self.pos + '-' + self.deprel + '-' + str(self.aligned_id) + '}'
        
	def is_ignore(self):
		return self.deprel in ['punct', '']

	def is_core_element(self):
		return (any(regex.match(self.pos) for regex in pos_regexes) and not any(regex.match(self.deprel) for regex in deprel_regexes)) or any(regex.match(self.deprel) for regex in deprel_regexes_core)


# Obtains the list of POS in the sentence and a boolean value for the presence of a finite verb
def __get_wordpos_finiteverb(sent):
	words_tree = []
	finite_verb = False #VerbForm=Fin 
	if sent:
		node = sent[0]
		for child in node:
			if child.tag == 'w':
				n = Node(child.attrib['id'])
				n.set_head(child.attrib['head'] if 'head' in child.attrib else None)
				n.set_deprel(child.attrib['deprel'] if 'deprel' in child.attrib else None)
				n.set_pos(child.attrib["upos"] if 'upos' in child.attrib else None)
				n.set_word(child.text)
				n.set_lemma(child.attrib["lemma"] if 'lemma' in child.attrib else None)
				words_tree.append(n)
				if "feats" in child.attrib and "VerbForm=Fin" in child.attrib["feats"]:
					finite_verb = True
	return words_tree, finite_verb 


# Determines if an alignment is good
def check_good_alignment(ces_align, line, word_alignment):
	tokens = line.split("|||")
	id_sent, id_doc = __parse_id(tokens[0])
	from_doc, to_doc, id_source, id_target = __get_parsed_sentence(ces_align, id_sent, id_doc)
	sent1 = __get_sentence_from_id(from_doc, id_source)
	sent2 = __get_sentence_from_id(to_doc, id_target)
	w = word_alignment.split(" ")
	finite_verb1 = False
	finite_verb2 = False
	if len(sent1) != 1 or len(sent2) != 1:
		if debug:
			print("More than one sentence")
		return False
	words_tree1, finite_verb1 = __get_wordpos_finiteverb(sent1)
	words_tree2, finite_verb2 = __get_wordpos_finiteverb(sent2)
	if len(words_tree1) < 5 or len(words_tree2) < 5:
		if debug:
			print("Sentence too short")
		return False
	if not finite_verb1 or not finite_verb2:
		if debug:
			print("No finite verb")
		return False
	for i in range(len(w)):
		word = w[i].split("-")
		if len(word) < 2 or not word[0].strip().isdigit() or not word[1].strip().isdigit():
			if debug:
				print('Word indexes format not correct')
			return False
		index1 = int(word[0].strip())
		index2 = int(word[1].strip())
		words_tree1[index1].set_aligned_id(words_tree2[index2].id)
		words_tree2[index2].set_aligned_id(words_tree1[index1].id)

		if words_tree1[index1].pos != words_tree2[index2].pos:
			# Ignores specific POS
			if words_tree1[index1].pos in ignore_pos or words_tree2[index2].pos in ignore_pos:
				continue
			if debug:
				print('POS not matching:', words_tree1[index1].pos, '!=', words_tree2[index2].pos)
			return False 
	if debug:
		print('Found match')
	return words_tree1, words_tree2
	
    

#########################################################################################################################


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='server utils')
	parser.add_argument('-M', '--mode', dest='mode', type=int, default=0, help='function to call, SETUP_MODE or GET_GOOD_SENTENCES')
	parser.add_argument('-o', '--output_file', dest='output_file', default=None, help='name of the output file to write')
	parser.add_argument('-l', '--lang', dest='lang', default='iten', help='selected languages: iten, sven or svit')
	parser.add_argument('-n', '--num', dest='num', type=int, default=None, help='number of documents to parse')
	parser.add_argument('-s', '--sent_file', dest='sent_file', default=None, help='aligned sentences file')
	parser.add_argument('-wf', '--wf', dest='wf', default=None, help='word alignment forward')
	parser.add_argument('-wr', '--wr', dest='wr', default=None, help='word alignment reverse')
	parser.add_argument('-c', '--chosen_file', dest='chosen_file', default=None, help='name of the file for the chosen sentences')
	parser.add_argument('-d', '--debug', dest='debug', action='store_true', help='enable debug logging')
	args = parser.parse_args()

	debug = args.debug
	mode = args.mode
	
	if mode == SETUP_MODE:
		if debug:
			print('Selected mode: setup, lang=', args.lang,'docs=', args.num, 'file=', args.output_file)
		get_sentence_alignment(args.output_file, args.lang, args.num)
	elif mode == GET_GOOD_SENTENCES:
		if debug:
			print('Selected mode: good sentences, lang=', args.lang)
		get_good_sentences(args.lang, args.sent_file, args.wf, args.wr, args.chosen_file)
	print("server_utils done")